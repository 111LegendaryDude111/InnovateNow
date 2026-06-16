from __future__ import annotations

from fastapi import HTTPException
from pydantic import BaseModel

from .errors import HuggingFaceEmbeddingsError
from .product_search import (
    ProductSearchService,
    get_product_search_service,
    require_search_query,
    require_top_k,
)


class SemanticSearchRequest(BaseModel):
    query: str
    top_k: int | None = None


class SemanticProductResult(BaseModel):
    rank: int
    score: float
    product_id: str
    name: str
    description: str
    category: str
    price: float


class SemanticSearchResponse(BaseModel):
    query: str
    normalized_query: str
    top_k: int
    model: str
    results: list[SemanticProductResult]


def create_semantic_search_response(
    request: SemanticSearchRequest,
    *,
    service: ProductSearchService | None = None,
) -> SemanticSearchResponse:
    """Создает semantic product search response без раскрытия server-side token."""
    try:
        query = require_search_query(request.query)
        top_k = require_top_k(request.top_k)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    search_service = service or get_product_search_service()
    if not search_service.has_api_key:
        raise HTTPException(status_code=500, detail="HF_TOKEN is required")

    try:
        output = search_service.search(query, top_k=top_k)
    except HuggingFaceEmbeddingsError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return SemanticSearchResponse(
        query=output.query,
        normalized_query=output.normalized_query,
        top_k=output.top_k,
        model=output.model,
        results=[
            SemanticProductResult(
                rank=result.rank,
                score=result.score,
                product_id=result.product.product_id,
                name=result.product.name,
                description=result.product.description,
                category=result.product.category,
                price=result.product.price,
            )
            for result in output.results
        ],
    )
