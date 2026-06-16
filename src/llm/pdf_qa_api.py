from __future__ import annotations

from fastapi import HTTPException, UploadFile
from pydantic import BaseModel

from .errors import HuggingFaceEmbeddingsError, OpenRouterError
from .huggingface_embeddings import HuggingFaceEmbeddingClient
from .openrouter import OpenRouterClient
from .pdf_processing import (
    PdfProcessingError,
    PdfUpload,
    PdfUploadTooLarge,
)
from .pdf_qa import (
    answer_pdf_question,
    ingest_pdf_uploads,
)
from .pdf_qa_models import (
    PdfAnswerResult,
    PdfChunkMatch,
    PdfIngestResult,
    PdfProviderKeyMissing,
    PdfQaError,
    PdfQaStore,
    PdfSessionNotFound,
)


class PdfIngestDocumentResponse(BaseModel):
    filename: str
    page_count: int
    chunk_count: int


class PdfIngestResponse(BaseModel):
    session_id: str
    documents: list[PdfIngestDocumentResponse]
    chunk_count: int
    provider_metadata: dict[str, str | int | float]


class PdfAskRequest(BaseModel):
    session_id: str
    question: str
    top_k: int | None = None


class PdfSourceResponse(BaseModel):
    filename: str
    page: int
    chunk_id: str
    rank: int
    score: float
    snippet: str


class PdfAskResponse(BaseModel):
    answer: str
    sources: list[PdfSourceResponse]
    retrieved_chunks: list[PdfSourceResponse]
    provider_metadata: dict[str, str | int | float]


_pdf_qa_store = PdfQaStore()


async def create_pdf_ingest_response(
    files: list[UploadFile] | None,
    *,
    store: PdfQaStore | None = None,
    embedding_provider: HuggingFaceEmbeddingClient | None = None,
) -> PdfIngestResponse:
    """Создает session-scoped PDF index из multipart upload."""
    try:
        uploads = await _read_uploads(files)
        result = ingest_pdf_uploads(
            uploads,
            provider=embedding_provider or HuggingFaceEmbeddingClient.from_env(),
            store=store or _pdf_qa_store,
        )
    except PdfUploadTooLarge as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc
    except PdfProviderKeyMissing as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except (PdfProcessingError, PdfQaError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HuggingFaceEmbeddingsError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return _ingest_response(result)


def create_pdf_ask_response(
    request: PdfAskRequest,
    *,
    store: PdfQaStore | None = None,
    embedding_provider: HuggingFaceEmbeddingClient | None = None,
    answer_provider: OpenRouterClient | None = None,
) -> PdfAskResponse:
    """Создает grounded answer по ранее загруженной PDF session."""
    try:
        result = answer_pdf_question(
            session_id=request.session_id,
            question=request.question,
            top_k=request.top_k,
            store=store or _pdf_qa_store,
            embedding_provider=embedding_provider or HuggingFaceEmbeddingClient.from_env(),
            answer_provider=answer_provider or OpenRouterClient.from_env(),
        )
    except PdfSessionNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PdfProviderKeyMissing as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except PdfQaError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (HuggingFaceEmbeddingsError, OpenRouterError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return _ask_response(result)


async def _read_uploads(files: list[UploadFile] | None) -> list[PdfUpload]:
    if not files:
        raise PdfQaError("at least one PDF file is required")
    return [
        PdfUpload(
            filename=file.filename or "",
            content_type=file.content_type or "",
            data=await file.read(),
        )
        for file in files
    ]


def _ingest_response(result: PdfIngestResult) -> PdfIngestResponse:
    return PdfIngestResponse(
        session_id=result.session_id,
        documents=[
            PdfIngestDocumentResponse(
                filename=document.filename,
                page_count=document.page_count,
                chunk_count=document.chunk_count,
            )
            for document in result.documents
        ],
        chunk_count=result.chunk_count,
        provider_metadata={
            "embedding_provider": "huggingface",
            "embedding_model": result.embedding_model,
        },
    )


def _ask_response(result: PdfAnswerResult) -> PdfAskResponse:
    return PdfAskResponse(
        answer=result.answer,
        sources=[_source_response(source) for source in result.sources],
        retrieved_chunks=[_source_response(chunk) for chunk in result.retrieved_chunks],
        provider_metadata=result.provider_metadata,
    )


def _source_response(match: PdfChunkMatch) -> PdfSourceResponse:
    return PdfSourceResponse(
        filename=match.filename,
        page=match.page,
        chunk_id=match.chunk_id,
        rank=match.rank,
        score=match.score,
        snippet=match.snippet,
    )
