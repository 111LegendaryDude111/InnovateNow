from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from qdrant_client.http.exceptions import ApiException, ResponseHandlingException

from .document_models import KnowledgeDocument
from .document_preprocessing import preprocess_text

DEFAULT_QDRANT_COLLECTION = "innovatech_sample_documents"
DEFAULT_QDRANT_URL = "http://localhost:6333"
QDRANT_DISTANCE = qmodels.Distance.COSINE
QDRANT_ERROR_TYPES = (ApiException, ResponseHandlingException, httpx.HTTPError, OSError)


@dataclass(frozen=True, slots=True)
class QdrantIngestSummary:
    collection_name: str
    point_count: int
    vector_size: int
    distance: str
    model: str


@dataclass(frozen=True, slots=True)
class QdrantSearchMatch:
    source_id: str
    score: float
    title: str
    category: str
    text: str


class QdrantReadinessError(RuntimeError):
    pass


def make_qdrant_client(
    *,
    url: str = DEFAULT_QDRANT_URL,
    timeout: int = 30,
) -> QdrantClient:
    return QdrantClient(url=url, timeout=timeout)


def ingest_qdrant_documents(
    client: Any,
    documents: list[KnowledgeDocument],
    provider: Any,
    *,
    collection_name: str = DEFAULT_QDRANT_COLLECTION,
    recreate: bool = False,
) -> QdrantIngestSummary:
    if not documents:
        raise ValueError("documents must be non-empty")

    texts = [preprocess_text(document.text) for document in documents]
    vectors = provider.embed_texts(texts)
    vector_size = require_uniform_vector_size(vectors)
    points = build_qdrant_points(documents, vectors, model=provider.model)

    ensure_qdrant_collection(
        client,
        collection_name=collection_name,
        vector_size=vector_size,
        recreate=recreate,
    )
    try:
        client.upsert(collection_name=collection_name, points=points, wait=True)
    except QDRANT_ERROR_TYPES as exc:
        raise QdrantReadinessError(qdrant_error_message(exc)) from exc

    return QdrantIngestSummary(
        collection_name=collection_name,
        point_count=len(points),
        vector_size=vector_size,
        distance=str(QDRANT_DISTANCE),
        model=provider.model,
    )


def ensure_qdrant_collection(
    client: Any,
    *,
    collection_name: str,
    vector_size: int,
    recreate: bool = False,
) -> None:
    try:
        exists = client.collection_exists(collection_name)
        if exists and recreate:
            client.delete_collection(collection_name)
            exists = False
        if not exists:
            client.create_collection(
                collection_name=collection_name,
                vectors_config=qmodels.VectorParams(
                    size=vector_size,
                    distance=QDRANT_DISTANCE,
                ),
            )
    except QDRANT_ERROR_TYPES as exc:
        raise QdrantReadinessError(qdrant_error_message(exc)) from exc


def build_qdrant_points(
    documents: list[KnowledgeDocument],
    vectors: list[list[float]],
    *,
    model: str,
) -> list[qmodels.PointStruct]:
    if len(documents) != len(vectors):
        raise ValueError("documents and vectors counts must match")
    require_uniform_vector_size(vectors)
    return [
        qmodels.PointStruct(
            id=index,
            vector=[float(value) for value in vector],
            payload={
                "source_id": document.document_id,
                "title": document.title,
                "category": document.category,
                "item_type": document.category,
                "text": document.text,
                "embedding_model": model,
            },
        )
        for index, (document, vector) in enumerate(
            zip(documents, vectors, strict=True),
            start=1,
        )
    ]


def search_qdrant_documents(
    client: Any,
    provider: Any,
    query: str,
    *,
    collection_name: str = DEFAULT_QDRANT_COLLECTION,
    top_k: int = 5,
) -> list[QdrantSearchMatch]:
    if top_k < 1:
        raise ValueError("top_k must be positive")
    query_text = query.strip()
    if not query_text:
        raise ValueError("query must be non-empty")

    query_vector = provider.embed_texts([query_text])[0]
    try:
        response = client.query_points(
            collection_name=collection_name,
            query=query_vector,
            limit=top_k,
            with_payload=True,
        )
    except QDRANT_ERROR_TYPES as exc:
        raise QdrantReadinessError(qdrant_error_message(exc)) from exc
    return [_match_from_point(point) for point in response.points]


def require_uniform_vector_size(vectors: list[list[float]]) -> int:
    if not vectors:
        raise ValueError("embeddings must be non-empty")
    vector_size = len(vectors[0])
    if vector_size < 1:
        raise ValueError("embedding vectors must be non-empty")
    if any(len(vector) != vector_size for vector in vectors):
        raise ValueError("embedding vector sizes must match")
    return vector_size


def qdrant_error_message(exc: BaseException) -> str:
    return f"Qdrant request failed. Is Qdrant running? {exc}"


def _match_from_point(point: Any) -> QdrantSearchMatch:
    payload = point.payload
    if not isinstance(payload, dict):
        raise ValueError("Qdrant point payload must be an object")
    return QdrantSearchMatch(
        source_id=_payload_text(payload, "source_id"),
        score=float(point.score),
        title=_payload_text(payload, "title"),
        category=_payload_text(payload, "category"),
        text=_payload_text(payload, "text"),
    )


def _payload_text(payload: dict[str, object], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"Qdrant point payload must contain {key}")
    return value
