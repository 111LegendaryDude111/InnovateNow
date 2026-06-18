from __future__ import annotations

from fastapi import HTTPException
from pydantic import BaseModel

from .cinder_hybrid_search import (
    CinderHybridSearchService,
    get_cinder_search_service,
)
from .cinder_search_models import CinderSearchFilters
from .product_search import require_top_k


class CinderHybridSearchRequest(BaseModel):
    query: str
    top_k: int | None = None
    category: str | None = None
    subcategory: str | None = None
    brand: str | None = None
    color: str | None = None
    material: str | None = None
    price_min: float | None = None
    price_max: float | None = None
    availability: str | None = None


class CinderHybridProductResult(BaseModel):
    rank: int
    score: float
    product_id: str
    title: str
    brand: str
    category: str
    subcategory: str
    price: float
    availability: str
    sku: str
    keyword_score: float
    vector_score: float
    ranking_score: float
    matched_keyword_fields: list[str]


class CinderHybridSearchResponse(BaseModel):
    query: str
    normalized_query: str
    top_k: int
    model: str
    fallback_applied: bool
    fallback_reason: str | None
    keyword_candidate_count: int
    vector_candidate_count: int
    filtered_candidate_count: int
    results: list[CinderHybridProductResult]


def create_cinder_hybrid_search_response(
    request: CinderHybridSearchRequest,
    *,
    service: CinderHybridSearchService | None = None,
) -> CinderHybridSearchResponse:
    """Создает Cinder hybrid search response с явным fallback metadata."""
    try:
        top_k = require_top_k(request.top_k)
        filters = _filters_from_request(request)
        search_service = service or get_cinder_search_service()
        output = search_service.search(request.query, filters=filters, top_k=top_k)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return CinderHybridSearchResponse(
        query=output.query,
        normalized_query=output.normalized_query,
        top_k=output.top_k,
        model=output.model,
        fallback_applied=output.fallback_applied,
        fallback_reason=output.fallback_reason,
        keyword_candidate_count=output.keyword_candidate_count,
        vector_candidate_count=output.vector_candidate_count,
        filtered_candidate_count=output.filtered_candidate_count,
        results=[
            CinderHybridProductResult(
                rank=result.rank,
                score=result.score,
                product_id=result.product.product_id,
                title=result.product.title,
                brand=result.product.brand,
                category=result.product.category,
                subcategory=result.product.subcategory,
                price=result.product.price,
                availability=result.product.availability,
                sku=result.product.sku,
                keyword_score=result.keyword_score,
                vector_score=result.vector_score,
                ranking_score=result.ranking_score,
                matched_keyword_fields=list(result.matched_keyword_fields),
            )
            for result in output.results
        ],
    )


def _filters_from_request(request: CinderHybridSearchRequest) -> CinderSearchFilters:
    price_min = _optional_non_negative(request.price_min, "price_min")
    price_max = _optional_non_negative(request.price_max, "price_max")
    if price_min is not None and price_max is not None and price_min > price_max:
        raise ValueError("price_min must be less than or equal to price_max")
    availability = _optional_text(request.availability)
    if availability is not None and availability not in {"in_stock", "out_of_stock"}:
        raise ValueError("availability must be in_stock or out_of_stock")
    return CinderSearchFilters(
        category=_optional_text(request.category),
        subcategory=_optional_text(request.subcategory),
        brand=_optional_text(request.brand),
        color=_optional_text(request.color),
        material=_optional_text(request.material),
        price_min=price_min,
        price_max=price_max,
        availability=availability,
    )


def _optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    clean = value.strip()
    return clean or None


def _optional_non_negative(value: float | None, field: str) -> float | None:
    if value is None:
        return None
    if value < 0:
        raise ValueError(f"{field} must be non-negative")
    return value
