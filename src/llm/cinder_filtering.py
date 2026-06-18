from __future__ import annotations

from .cinder_catalog import CinderProduct
from .cinder_search_models import CinderCandidate, CinderSearchFilters


def apply_cinder_filters(
    candidates: list[CinderCandidate],
    filters: CinderSearchFilters,
) -> list[CinderCandidate]:
    """Применяет hard filters к candidate set без изменения ranking-сигналов."""
    return [
        candidate
        for candidate in candidates
        if _passes_filters(candidate.product, filters)
    ]


def _passes_filters(product: CinderProduct, filters: CinderSearchFilters) -> bool:
    checks = (
        _same(product.category, filters.category),
        _same(product.subcategory, filters.subcategory),
        _same(product.brand, filters.brand),
        _same(product.attribute_color, filters.color),
        _same(product.attribute_material, filters.material),
        _same(product.availability, filters.availability),
        filters.price_min is None or product.price >= filters.price_min,
        filters.price_max is None or product.price <= filters.price_max,
    )
    return all(checks)


def _same(value: str, expected: str | None) -> bool:
    return expected is None or value.casefold() == expected.casefold()
