from __future__ import annotations

from .cinder_catalog import CinderProduct
from .cinder_search_models import CinderCandidate, CinderSearchResult


def rank_cinder_candidates(
    candidates: list[CinderCandidate],
) -> list[CinderSearchResult]:
    """Сортирует merged candidates с поведением только как post-retrieval signal."""
    ordered = sorted(candidates, key=_candidate_score, reverse=True)
    return [
        CinderSearchResult(
            rank=index,
            score=_candidate_score(candidate),
            product=candidate.product,
            keyword_score=candidate.keyword_score,
            vector_score=candidate.vector_score,
            ranking_score=_behavior_score(candidate.product),
            matched_keyword_fields=candidate.matched_keyword_fields,
        )
        for index, candidate in enumerate(ordered, start=1)
    ]


def _candidate_score(candidate: CinderCandidate) -> float:
    availability = 1.0 if candidate.product.availability == "in_stock" else 0.2
    return round(
        candidate.keyword_score * 0.55
        + candidate.vector_score * 0.3
        + _behavior_score(candidate.product) * 0.1
        + availability * 0.05,
        6,
    )


def _behavior_score(product: CinderProduct) -> float:
    clicks = min(product.clicks / 2000, 1.0)
    carts = min(product.add_to_cart_count / 250, 1.0)
    conversion = min(product.conversion_rate / 0.1, 1.0)
    return round((clicks + carts + conversion + product.popularity_score) / 4, 6)
