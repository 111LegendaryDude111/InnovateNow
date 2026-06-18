from __future__ import annotations

import re

from .cinder_catalog import CinderProduct
from .document_preprocessing import preprocess_text

TOKEN_RE = re.compile(r"[a-z0-9]+")


def cinder_vector_text(product: CinderProduct) -> str:
    parts = [
        product.title,
        product.description,
        *product.attribute_texts(),
        product.tags.replace("|", " "),
    ]
    return normalize_cinder_text(" ".join(part for part in parts if part))


def normalize_cinder_text(text: str) -> str:
    clean = preprocess_text(text, lowercase=True)
    if not clean:
        raise ValueError("query must be a non-empty string")
    return clean


def cinder_keyword_score(
    product: CinderProduct,
    normalized_query: str,
) -> tuple[float, tuple[str, ...]]:
    query_tokens = _tokens(normalized_query)
    sku = _plain(product.sku)
    query_plain = _plain(normalized_query)
    score = 0.0
    fields: list[str] = []

    if query_plain == sku or sku in query_plain:
        score += 1.0
        fields.append("sku")
    if normalized_query == normalize_cinder_text(product.title):
        score += 0.9
        fields.append("title")

    for field, weight, value in _keyword_fields(product):
        if not value.strip():
            continue
        field_text = normalize_cinder_text(value)
        field_tokens = _tokens(field_text)
        if normalized_query in field_text and field not in fields:
            score += weight
            fields.append(field)
        elif query_tokens and query_tokens & field_tokens:
            score += weight * len(query_tokens & field_tokens) / len(query_tokens)
            fields.append(field)

    return min(score, 1.0), tuple(dict.fromkeys(fields))


def _keyword_fields(product: CinderProduct) -> tuple[tuple[str, float, str], ...]:
    attrs = " ".join(product.attribute_texts())
    return (
        ("title", 0.45, product.title),
        ("brand", 0.14, product.brand),
        ("category", 0.12, product.category),
        ("subcategory", 0.18, product.subcategory),
        ("attributes", 0.16, attrs),
        ("tags", 0.2, product.tags.replace("|", " ")),
    )


def _tokens(text: str) -> set[str]:
    return set(TOKEN_RE.findall(text))


def _plain(text: str) -> str:
    return "".join(TOKEN_RE.findall(text.lower()))
