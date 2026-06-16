from __future__ import annotations

from pathlib import Path
from typing import Protocol

from .document_collection import load_documents
from .document_models import KnowledgeDocument, SimilarityMatch
from .document_preprocessing import chunk_documents
from .embedding_storage import (
    build_embedding_artifact,
    load_embedding_artifact,
    save_embedding_artifact,
)
from .semantic_similarity import rank_embedding_records


class EmbeddingProvider(Protocol):
    model: str

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        pass


def generate_embedding_artifact(
    documents: list[KnowledgeDocument],
    provider: EmbeddingProvider,
    *,
    chunk_words: int,
    chunk_overlap: int,
) -> dict[str, object]:
    """Строит artifact из документов через переданный embedding provider."""
    chunks = chunk_documents(
        documents,
        max_words=chunk_words,
        overlap_words=chunk_overlap,
    )
    embeddings = provider.embed_texts([chunk.text for chunk in chunks])
    return build_embedding_artifact(
        chunks,
        embeddings,
        model=provider.model,
        provider="huggingface",
        chunk_words=chunk_words,
        chunk_overlap=chunk_overlap,
    )


def build_embeddings_file(
    documents_path: Path,
    output_path: Path,
    provider: EmbeddingProvider,
    *,
    chunk_words: int,
    chunk_overlap: int,
) -> dict[str, object]:
    documents = load_documents(documents_path)
    artifact = generate_embedding_artifact(
        documents,
        provider,
        chunk_words=chunk_words,
        chunk_overlap=chunk_overlap,
    )
    save_embedding_artifact(output_path, artifact)
    return artifact


def search_embedding_file(
    artifact_path: Path,
    query: str,
    provider: EmbeddingProvider,
    *,
    top_k: int,
) -> list[SimilarityMatch]:
    artifact = load_embedding_artifact(artifact_path)
    return search_embedding_artifact(artifact, query, provider, top_k=top_k)


def search_embedding_artifact(
    artifact: dict[str, object],
    query: str,
    provider: EmbeddingProvider,
    *,
    top_k: int,
) -> list[SimilarityMatch]:
    records = artifact.get("records")
    if not isinstance(records, list):
        raise ValueError("embedding artifact must contain records")
    query_embedding = provider.embed_texts([query])[0]
    return rank_embedding_records(records, query_embedding, top_k=top_k)
