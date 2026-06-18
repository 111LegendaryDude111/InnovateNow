from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Protocol

import numpy as np

from .cinder_catalog import CinderProduct, load_cinder_products
from .cinder_filtering import apply_cinder_filters
from .cinder_ranking import rank_cinder_candidates
from .cinder_search_models import (
    CinderCandidate,
    CinderSearchFilters,
    CinderSearchOutput,
)
from .cinder_search_text import (
    cinder_keyword_score,
    cinder_vector_text,
    normalize_cinder_text,
)
from .errors import HuggingFaceEmbeddingsError
from .huggingface_embeddings import HuggingFaceEmbeddingClient
from .product_search import require_top_k
from .semantic_similarity import cosine_scores

DEFAULT_CINDER_DATASET_PATH = (
    Path(__file__).resolve().parents[2] / "data/cinder_home_goods_products.csv"
)
VECTOR_CANDIDATE_POOL = 30


class EmbeddingProvider(Protocol):
    model: str
    has_api_key: bool

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]: ...


class CinderHybridSearchService:
    def __init__(
        self,
        *,
        dataset_path: Path = DEFAULT_CINDER_DATASET_PATH,
        products: list[CinderProduct] | None = None,
        provider: EmbeddingProvider | None = None,
        provider_factory: Callable[
            [], EmbeddingProvider
        ] = HuggingFaceEmbeddingClient.from_env,
    ) -> None:
        self._dataset_path = dataset_path
        self._products = products
        self._provider = provider
        self._provider_factory = provider_factory
        self._vector_index: np.ndarray | None = None

    def search(
        self,
        query: str,
        *,
        filters: CinderSearchFilters | None = None,
        top_k: int | None = None,
    ) -> CinderSearchOutput:
        query_text = _require_query(query)
        normalized_query = normalize_cinder_text(query_text)
        limit = require_top_k(top_k)
        active_filters = filters or CinderSearchFilters()
        products = self._load_products()
        fallback_reasons: list[str] = []
        keyword_candidates = _keyword_candidates(products, normalized_query)
        vector_scores = self._vector_scores(products, normalized_query, fallback_reasons)
        candidates = _merge_candidates(products, keyword_candidates, vector_scores)
        vector_count = sum(1 for score in vector_scores.values() if score > 0)

        if not candidates:
            candidates = _popular_candidates(products)
            fallback_reasons.append("no_retrieval_candidates")

        filtered = apply_cinder_filters(candidates, active_filters)
        if active_filters.has_any() and not filtered:
            filtered = candidates
            fallback_reasons.append("filters_relaxed_no_results")

        ranked = rank_cinder_candidates(filtered)[:limit]
        return CinderSearchOutput(
            query=query_text,
            normalized_query=normalized_query,
            top_k=limit,
            model=self._model_name(fallback_reasons),
            fallback_applied=bool(fallback_reasons),
            fallback_reason=";".join(fallback_reasons) or None,
            keyword_candidate_count=len(keyword_candidates),
            vector_candidate_count=vector_count,
            filtered_candidate_count=len(filtered),
            results=ranked,
        )

    def _load_products(self) -> list[CinderProduct]:
        return self._products if self._products is not None else load_cinder_products(
            self._dataset_path
        )

    def _embedding_provider(self) -> EmbeddingProvider:
        if self._provider is None:
            self._provider = self._provider_factory()
        return self._provider

    def _vector_scores(
        self,
        products: list[CinderProduct],
        normalized_query: str,
        fallback_reasons: list[str],
    ) -> dict[str, float]:
        provider = self._embedding_provider()
        if not provider.has_api_key:
            fallback_reasons.append("vector_provider_unavailable")
            return {}
        try:
            index = self._product_vectors(products, provider)
            query_vector = provider.embed_texts([normalized_query])[0]
            scores = cosine_scores(query_vector, index.tolist())
        except (HuggingFaceEmbeddingsError, ValueError):
            fallback_reasons.append("vector_retrieval_failed")
            return {}
        order = np.argsort(-scores, kind="stable")[:VECTOR_CANDIDATE_POOL]
        return {
            products[int(index)].product_id: max(float(scores[int(index)]), 0.0)
            for index in order
        }

    def _product_vectors(
        self,
        products: list[CinderProduct],
        provider: EmbeddingProvider,
    ) -> np.ndarray:
        if self._vector_index is None:
            texts = [cinder_vector_text(product) for product in products]
            self._vector_index = np.asarray(provider.embed_texts(texts), dtype=float)
        return self._vector_index

    def _model_name(self, fallback_reasons: list[str]) -> str:
        if "vector_provider_unavailable" in fallback_reasons:
            return "keyword-only"
        return self._embedding_provider().model


def _require_query(query: str) -> str:
    clean = query.strip()
    if not clean:
        raise ValueError("query must be a non-empty string")
    return clean


def _keyword_candidates(
    products: list[CinderProduct],
    normalized_query: str,
) -> dict[str, tuple[float, tuple[str, ...]]]:
    matches = {}
    for product in products:
        score, fields = cinder_keyword_score(product, normalized_query)
        if score > 0:
            matches[product.product_id] = (score, fields)
    return matches


def _merge_candidates(
    products: list[CinderProduct],
    keyword: dict[str, tuple[float, tuple[str, ...]]],
    vector: dict[str, float],
) -> list[CinderCandidate]:
    product_by_id = {product.product_id: product for product in products}
    candidates = []
    for product_id, product in product_by_id.items():
        if product_id not in keyword and product_id not in vector:
            continue
        keyword_score, fields = keyword.get(product_id, (0, ()))
        candidates.append(
            CinderCandidate(
                product=product,
                keyword_score=keyword_score,
                vector_score=vector.get(product_id, 0),
                matched_keyword_fields=fields,
            )
        )
    return candidates


def _popular_candidates(products: list[CinderProduct]) -> list[CinderCandidate]:
    return [CinderCandidate(product, 0, 0, ()) for product in products]


_cinder_search_service: CinderHybridSearchService | None = None


def get_cinder_search_service() -> CinderHybridSearchService:
    global _cinder_search_service
    if _cinder_search_service is None:
        # ponytail: process-local CSV/vector cache; external index belongs in later scale work.
        _cinder_search_service = CinderHybridSearchService()
    return _cinder_search_service
