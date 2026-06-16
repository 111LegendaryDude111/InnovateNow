from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .document_models import KnowledgeDocument


def load_documents(path: Path) -> list[KnowledgeDocument]:
    """Загружает committed knowledge-base dataset и проверяет форму записей."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("document collection must be a JSON array")

    documents = [_document_from_payload(item, index) for index, item in enumerate(payload)]
    require_unique_document_ids(documents)
    return documents


def require_unique_document_ids(
    documents: list[KnowledgeDocument],
) -> list[KnowledgeDocument]:
    seen: set[str] = set()
    for document in documents:
        if document.document_id in seen:
            raise ValueError(f"duplicate document_id: {document.document_id}")
        seen.add(document.document_id)
    return documents


def _document_from_payload(item: object, index: int) -> KnowledgeDocument:
    if not isinstance(item, Mapping):
        raise ValueError(f"document at index {index} must be an object")

    document_id = _required_text(item, "document_id", index)
    title = _required_text(item, "title", index)
    category = _required_text(item, "category", index)
    text = _required_text(item, "text", index)
    return KnowledgeDocument(
        document_id=document_id,
        title=title,
        category=category,
        text=text,
    )


def _required_text(item: Mapping[str, Any], key: str, index: int) -> str:
    value = item.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"document at index {index} must have non-empty {key}")
    return value.strip()
