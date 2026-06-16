from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class KnowledgeDocument:
    document_id: str
    title: str
    category: str
    text: str


@dataclass(frozen=True, slots=True)
class DocumentChunk:
    document_id: str
    chunk_id: str
    title: str
    category: str
    text: str
    chunk_index: int


@dataclass(frozen=True, slots=True)
class SimilarityMatch:
    document_id: str
    chunk_id: str
    title: str
    category: str
    score: float
    text: str
