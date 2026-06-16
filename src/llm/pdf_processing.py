from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

from pypdf import PdfReader

from .document_preprocessing import preprocess_text

MAX_PDF_UPLOAD_BYTES = 8 * 1024 * 1024
PDF_CHUNK_MAX_WORDS = 180
PDF_CHUNK_OVERLAP_WORDS = 30
PDF_CONTENT_TYPES = {"application/pdf", "application/octet-stream"}


class PdfProcessingError(ValueError):
    """Ошибка валидации или обработки загруженного PDF."""


class PdfUploadTooLarge(PdfProcessingError):
    """PDF превышает разрешенный размер upload."""


@dataclass(frozen=True, slots=True)
class PdfUpload:
    filename: str
    content_type: str
    data: bytes


@dataclass(frozen=True, slots=True)
class PdfPage:
    filename: str
    page: int
    text: str


@dataclass(frozen=True, slots=True)
class PdfDocumentText:
    filename: str
    page_count: int
    pages: list[PdfPage]


@dataclass(frozen=True, slots=True)
class PdfChunk:
    filename: str
    page: int
    chunk_id: str
    text: str
    chunk_index: int


@dataclass(frozen=True, slots=True)
class PdfDocumentSummary:
    filename: str
    page_count: int
    chunk_count: int


def extract_pdf_text(upload: PdfUpload) -> PdfDocumentText:
    """Извлекает текст страниц PDF и сохраняет имя файла/page metadata."""
    filename = validate_pdf_upload(upload)
    try:
        reader = PdfReader(BytesIO(upload.data))
        page_count = len(reader.pages)
        pages = [
            PdfPage(filename, page_number, text)
            for page_number, text in _iter_page_text(reader, filename)
        ]
    except PdfProcessingError:
        raise
    except Exception as exc:
        raise PdfProcessingError(f"could not read PDF: {filename}") from exc

    if not pages:
        raise PdfProcessingError(f"PDF has no extractable text: {filename}")
    return PdfDocumentText(filename=filename, page_count=page_count, pages=pages)


def chunk_pdf_documents(
    documents: list[PdfDocumentText],
    *,
    max_words: int = PDF_CHUNK_MAX_WORDS,
    overlap_words: int = PDF_CHUNK_OVERLAP_WORDS,
) -> tuple[list[PdfChunk], list[PdfDocumentSummary]]:
    """Делит PDF text pages на chunks с filename/page/chunk_id."""
    if max_words < 1:
        raise ValueError("max_words must be positive")
    if overlap_words < 0 or overlap_words >= max_words:
        raise ValueError("overlap_words must be non-negative and smaller than max_words")

    all_chunks: list[PdfChunk] = []
    summaries: list[PdfDocumentSummary] = []
    for document in documents:
        chunks = [
            chunk
            for page in document.pages
            for chunk in _chunk_page(page, max_words=max_words, overlap_words=overlap_words)
        ]
        summaries.append(
            PdfDocumentSummary(
                filename=document.filename,
                page_count=document.page_count,
                chunk_count=len(chunks),
            )
        )
        all_chunks.extend(chunks)

    if not all_chunks:
        raise PdfProcessingError("uploaded PDFs have no extractable text")
    return all_chunks, summaries


def validate_pdf_upload(upload: PdfUpload) -> str:
    filename = upload.filename.strip()
    if not filename:
        raise PdfProcessingError("filename is required")
    if not filename.lower().endswith(".pdf"):
        raise PdfProcessingError("only .pdf files are supported")
    if upload.content_type and upload.content_type not in PDF_CONTENT_TYPES:
        raise PdfProcessingError("only application/pdf uploads are supported")
    if not upload.data:
        raise PdfProcessingError(f"PDF is empty: {filename}")
    if len(upload.data) > MAX_PDF_UPLOAD_BYTES:
        limit_mb = MAX_PDF_UPLOAD_BYTES // (1024 * 1024)
        raise PdfUploadTooLarge(f"PDF exceeds {limit_mb} MB limit: {filename}")
    return filename


def _iter_page_text(reader: PdfReader, filename: str) -> list[tuple[int, str]]:
    pages: list[tuple[int, str]] = []
    for page_number, page in enumerate(reader.pages, start=1):
        try:
            text = preprocess_text(page.extract_text() or "")
        except Exception as exc:
            raise PdfProcessingError(
                f"could not extract text from {filename} page {page_number}"
            ) from exc
        if text:
            pages.append((page_number, text))
    return pages


def _chunk_page(
    page: PdfPage,
    *,
    max_words: int,
    overlap_words: int,
) -> list[PdfChunk]:
    words = page.text.split()
    step = max_words - overlap_words
    chunks: list[PdfChunk] = []
    for index, start in enumerate(range(0, len(words), step), start=1):
        chunk_words = words[start : start + max_words]
        if not chunk_words:
            continue
        chunks.append(
            PdfChunk(
                filename=page.filename,
                page=page.page,
                chunk_id=f"{page.filename}:p{page.page}:c{index}",
                text=" ".join(chunk_words),
                chunk_index=index,
            )
        )
        if start + max_words >= len(words):
            break
    return chunks
