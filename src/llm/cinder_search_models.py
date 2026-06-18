from __future__ import annotations

from dataclasses import dataclass

from .cinder_catalog import CinderProduct


@dataclass(frozen=True, slots=True)
class CinderSearchFilters:
    category: str | None = None
    subcategory: str | None = None
    brand: str | None = None
    color: str | None = None
    material: str | None = None
    price_min: float | None = None
    price_max: float | None = None
    availability: str | None = None

    def has_any(self) -> bool:
        return any(
            value is not None
            for value in (
                self.category,
                self.subcategory,
                self.brand,
                self.color,
                self.material,
                self.price_min,
                self.price_max,
                self.availability,
            )
        )


@dataclass(frozen=True, slots=True)
class CinderCandidate:
    product: CinderProduct
    keyword_score: float
    vector_score: float
    matched_keyword_fields: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CinderSearchResult:
    rank: int
    score: float
    product: CinderProduct
    keyword_score: float
    vector_score: float
    ranking_score: float
    matched_keyword_fields: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CinderSearchOutput:
    query: str
    normalized_query: str
    top_k: int
    model: str
    fallback_applied: bool
    fallback_reason: str | None
    keyword_candidate_count: int
    vector_candidate_count: int
    filtered_candidate_count: int
    results: list[CinderSearchResult]
