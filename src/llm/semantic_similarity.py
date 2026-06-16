from __future__ import annotations

from typing import Any, Mapping

import numpy as np

from .document_models import SimilarityMatch


def rank_embedding_records(
    records: list[Mapping[str, Any]],
    query_embedding: list[float],
    *,
    top_k: int = 5,
) -> list[SimilarityMatch]:
    """Считает cosine similarity и возвращает top-k chunk matches."""
    if top_k < 1:
        raise ValueError("top_k must be positive")

    embeddings = [_record_embedding(record) for record in records]
    scores = cosine_scores(query_embedding, embeddings)
    order = np.argsort(scores)[::-1][:top_k]
    return [
        _match_from_record(records[int(index)], float(scores[int(index)]))
        for index in order
    ]


def cosine_scores(
    query_embedding: list[float],
    embeddings: list[list[float]],
) -> np.ndarray:
    query = np.asarray(query_embedding, dtype=np.float64)
    matrix = np.asarray(embeddings, dtype=np.float64)
    if query.ndim != 1:
        raise ValueError("query embedding must be one-dimensional")
    if matrix.ndim != 2:
        raise ValueError("stored embeddings must be a two-dimensional matrix")
    if matrix.shape[1] != query.shape[0]:
        raise ValueError("embedding dimensions must match")

    query_norm = np.linalg.norm(query)
    matrix_norms = np.linalg.norm(matrix, axis=1)
    if query_norm == 0 or np.any(matrix_norms == 0):
        raise ValueError("embeddings must not contain zero vectors")
    return (matrix @ query) / (matrix_norms * query_norm)


def _record_embedding(record: Mapping[str, Any]) -> list[float]:
    value = record.get("embedding")
    if not isinstance(value, list):
        raise ValueError("embedding record must contain embedding")
    return [float(item) for item in value]


def _match_from_record(record: Mapping[str, Any], score: float) -> SimilarityMatch:
    return SimilarityMatch(
        document_id=str(record["document_id"]),
        chunk_id=str(record["chunk_id"]),
        title=str(record["title"]),
        category=str(record["category"]),
        score=score,
        text=str(record["text"]),
    )
