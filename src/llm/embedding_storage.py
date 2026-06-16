from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .document_models import DocumentChunk

SCHEMA_VERSION = 1


def build_embedding_artifact(
    chunks: list[DocumentChunk],
    embeddings: list[list[float]],
    *,
    model: str,
    provider: str,
    chunk_words: int,
    chunk_overlap: int,
) -> dict[str, Any]:
    """Создает JSON-ready artifact без provider secrets."""
    if len(chunks) != len(embeddings):
        raise ValueError("chunks and embeddings counts must match")
    return {
        "schema_version": SCHEMA_VERSION,
        "provider": provider,
        "model": model,
        "preprocessing": {
            "case_policy": "keep-case",
            "chunk_words": chunk_words,
            "chunk_overlap": chunk_overlap,
        },
        "records": [
            {
                "document_id": chunk.document_id,
                "chunk_id": chunk.chunk_id,
                "chunk_index": chunk.chunk_index,
                "title": chunk.title,
                "category": chunk.category,
                "text": chunk.text,
                "embedding": embedding,
            }
            for chunk, embedding in zip(chunks, embeddings, strict=True)
        ],
    }


def save_embedding_artifact(path: Path, artifact: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(artifact, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )


def load_embedding_artifact(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("embedding artifact must be a JSON object")
    records = payload.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError("embedding artifact must contain records")
    return payload
