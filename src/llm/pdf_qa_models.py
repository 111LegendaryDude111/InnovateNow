from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence
from uuid import uuid4

import numpy as np

from .pdf_processing import PdfChunk, PdfDocumentSummary


class PdfQaError(ValueError):
    """Ошибка session-scoped PDF Q&A workflow."""


class PdfSessionNotFound(PdfQaError):
    """Session ID не найден во временном store."""


class PdfProviderKeyMissing(PdfQaError):
    """Не задан server-side API key provider."""


class EmbeddingProvider(Protocol):
    model: str
    has_api_key: bool

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        ...


class AnswerProvider(Protocol):
    model: str
    has_api_key: bool

    def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        options: dict[str, object] | None = None,
    ) -> str:
        ...


@dataclass(frozen=True, slots=True)
class PdfSession:
    session_id: str
    documents: list[PdfDocumentSummary]
    chunks: list[PdfChunk]
    embeddings: np.ndarray
    embedding_model: str


@dataclass(frozen=True, slots=True)
class PdfIngestResult:
    session_id: str
    documents: list[PdfDocumentSummary]
    chunk_count: int
    embedding_model: str


@dataclass(frozen=True, slots=True)
class PdfChunkMatch:
    filename: str
    page: int
    chunk_id: str
    rank: int
    score: float
    snippet: str
    text: str


@dataclass(frozen=True, slots=True)
class PdfAnswerResult:
    answer: str
    sources: list[PdfChunkMatch]
    retrieved_chunks: list[PdfChunkMatch]
    provider_metadata: dict[str, str | int | float]


class PdfQaStore:
    def __init__(self) -> None:
        self._sessions: dict[str, PdfSession] = {}

    def create_session(
        self,
        *,
        documents: list[PdfDocumentSummary],
        chunks: list[PdfChunk],
        embeddings: list[list[float]],
        embedding_model: str,
    ) -> PdfSession:
        """Создает временную session с chunks и embedding matrix."""
        session = PdfSession(
            session_id=uuid4().hex,
            documents=documents,
            chunks=chunks,
            embeddings=np.asarray(embeddings, dtype=np.float64),
            embedding_model=embedding_model,
        )
        self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> PdfSession | None:
        return self._sessions.get(session_id)
