from __future__ import annotations

import re
import unicodedata

from .document_models import DocumentChunk, KnowledgeDocument

CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]")
FORMAT_MARKS_RE = re.compile(r"[*_`>#|]+")
WHITESPACE_RE = re.compile(r"\s+")


def preprocess_text(text: str, *, lowercase: bool = False) -> str:
    """Нормализует текст документа перед embedding без потери смыслового регистра."""
    normalized = unicodedata.normalize("NFKC", text)
    normalized = CONTROL_CHARS_RE.sub(" ", normalized)
    normalized = FORMAT_MARKS_RE.sub(" ", normalized)
    normalized = normalized.replace("\u200b", " ").replace("\ufeff", " ")
    normalized = WHITESPACE_RE.sub(" ", normalized).strip()
    if lowercase:
        return normalized.lower()
    return normalized


def chunk_documents(
    documents: list[KnowledgeDocument],
    *,
    max_words: int = 180,
    overlap_words: int = 30,
) -> list[DocumentChunk]:
    """Делит длинные документы на word chunks с сохранением document_id."""
    if max_words < 1:
        raise ValueError("max_words must be positive")
    if overlap_words < 0 or overlap_words >= max_words:
        raise ValueError("overlap_words must be non-negative and smaller than max_words")

    chunks: list[DocumentChunk] = []
    for document in documents:
        clean_text = preprocess_text(document.text)
        words = clean_text.split()
        if not words:
            raise ValueError(f"document has no text after preprocessing: {document.document_id}")
        chunks.extend(_chunk_document(document, words, max_words, overlap_words))
    return chunks


def _chunk_document(
    document: KnowledgeDocument,
    words: list[str],
    max_words: int,
    overlap_words: int,
) -> list[DocumentChunk]:
    step = max_words - overlap_words
    chunks: list[DocumentChunk] = []
    for index, start in enumerate(range(0, len(words), step), start=1):
        chunk_words = words[start : start + max_words]
        if not chunk_words:
            continue
        chunks.append(
            DocumentChunk(
                document_id=document.document_id,
                chunk_id=f"{document.document_id}-CHUNK-{index:03d}",
                title=document.title,
                category=document.category,
                text=" ".join(chunk_words),
                chunk_index=index,
            )
        )
        if start + max_words >= len(words):
            break
    return chunks
