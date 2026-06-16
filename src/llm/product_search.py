from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import numpy as np

from .document_preprocessing import preprocess_text
from .huggingface_embeddings import HuggingFaceEmbeddingClient
from .product_catalog import Product, load_products
from .semantic_similarity import cosine_scores

DEFAULT_PRODUCT_DATASET_PATH = (
    Path(__file__).resolve().parents[2] / "data/product_catalog.json"
)
DEFAULT_PRODUCT_SEARCH_TOP_K = 5
MAX_PRODUCT_SEARCH_TOP_K = 20


class EmbeddingProvider(Protocol):
    model: str
    has_api_key: bool

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]: ...


@dataclass(frozen=True, slots=True)
class ProductSearchResult:
    rank: int
    score: float
    product: Product


@dataclass(frozen=True, slots=True)
class ProductSearchOutput:
    query: str
    normalized_query: str
    top_k: int
    model: str
    results: list[ProductSearchResult]


@dataclass(frozen=True, slots=True)
class ProductSearchIndex:
    products: list[Product]
    embeddings: np.ndarray
    model: str

    def search(
        self, query_embedding: list[float], *, top_k: int
    ) -> list[ProductSearchResult]:
        """Возвращает товары по cosine similarity к embedding запроса."""
        scores = cosine_scores(query_embedding, self.embeddings.tolist())
        order = np.argsort(-scores, kind="stable")[:top_k]
        return [
            ProductSearchResult(
                rank=rank,
                score=float(scores[int(index)]),
                product=self.products[int(index)],
            )
            for rank, index in enumerate(order, start=1)
        ]


class ProductSearchService:
    def __init__(
        self,
        *,
        dataset_path: Path = DEFAULT_PRODUCT_DATASET_PATH,
        products: list[Product] | None = None,
        provider: EmbeddingProvider | None = None,
        provider_factory: Callable[
            [], EmbeddingProvider
        ] = HuggingFaceEmbeddingClient.from_env,
    ) -> None:
        self._dataset_path = dataset_path
        self._products = products
        self._provider = provider
        self._provider_factory = provider_factory
        self._index: ProductSearchIndex | None = None

    @property
    def has_api_key(self) -> bool:
        return self._embedding_provider().has_api_key

    def search(self, query: str, *, top_k: int | None = None) -> ProductSearchOutput:
        query_text = require_search_query(query)
        limit = require_top_k(top_k)
        normalized_query = normalize_search_query(query_text)
        provider = self._embedding_provider()
        index = self._product_index()
        query_embedding = provider.embed_texts([normalized_query])[0]
        return ProductSearchOutput(
            query=query_text,
            normalized_query=normalized_query,
            top_k=limit,
            model=index.model,
            results=index.search(query_embedding, top_k=limit),
        )

    def _embedding_provider(self) -> EmbeddingProvider:
        if self._provider is None:
            self._provider = self._provider_factory()
        return self._provider

    def _product_index(self) -> ProductSearchIndex:
        if self._index is None:
            products = (
                self._products
                if self._products is not None
                else load_products(self._dataset_path)
            )
            self._index = build_product_search_index(
                products, self._embedding_provider()
            )
        return self._index


def build_product_search_index(
    products: list[Product],
    provider: EmbeddingProvider,
) -> ProductSearchIndex:
    """Строит in-memory индекс: product text -> embedding matrix + metadata."""
    if not products:
        raise ValueError("products must be non-empty")
    texts = [product_search_text(product) for product in products]
    embeddings = provider.embed_texts(texts)
    _require_uniform_vector_size(embeddings)
    return ProductSearchIndex(
        products=products,
        embeddings=np.asarray(embeddings, dtype=np.float64),
        model=provider.model,
    )


def product_search_text(product: Product) -> str:
    parts = [product.name, product.category, product.description, *product.features]
    return preprocess_text(" ".join(parts), lowercase=True)


def require_search_query(query: str) -> str:
    clean = query.strip()
    if not clean:
        raise ValueError("query must be a non-empty string")
    return clean


def normalize_search_query(query: str) -> str:
    clean = preprocess_text(query, lowercase=True)
    if not clean:
        raise ValueError("query must be a non-empty string")
    return clean


def require_top_k(top_k: int | None) -> int:
    if top_k is None:
        return DEFAULT_PRODUCT_SEARCH_TOP_K
    if isinstance(top_k, bool) or not isinstance(top_k, int):
        raise ValueError("top_k must be an integer")
    if top_k < 1 or top_k > MAX_PRODUCT_SEARCH_TOP_K:
        raise ValueError(f"top_k must be between 1 and {MAX_PRODUCT_SEARCH_TOP_K}")
    return top_k


def _require_uniform_vector_size(vectors: list[list[float]]) -> int:
    if not vectors:
        raise ValueError("embeddings must be non-empty")
    vector_size = len(vectors[0])
    if vector_size < 1:
        raise ValueError("embedding vectors must be non-empty")
    if any(len(vector) != vector_size for vector in vectors):
        raise ValueError("embedding vector sizes must match")
    return vector_size


_product_search_service: ProductSearchService | None = None


def get_product_search_service() -> ProductSearchService:
    global _product_search_service
    if _product_search_service is None:
        # ponytail: per-process cache; rebuild per worker after process restart.
        _product_search_service = ProductSearchService()
    return _product_search_service
