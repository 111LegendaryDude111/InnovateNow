from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from llm.cinder_hybrid_search import CinderHybridSearchService
from llm.cinder_search_models import CinderSearchFilters


class QualityFakeEmbeddingProvider:
    model = "fake-quality-embedding-model"
    has_api_key = True

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._vector_for(text) for text in texts]

    def _vector_for(self, text: str) -> list[float]:
        lower = text.lower()
        if any(word in lower for word in ("bench", "storage", "entryway")):
            return [1.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        if any(word in lower for word in ("lamp", "lighting", "shade")):
            return [0.0, 1.0, 0.0, 0.0, 0.0, 0.0]
        if any(word in lower for word in ("runner", "rug")):
            return [0.0, 0.0, 1.0, 0.0, 0.0, 0.0]
        if any(word in lower for word in ("saucepan", "cookware", "copper")):
            return [0.0, 0.0, 0.0, 1.0, 0.0, 0.0]
        if any(word in lower for word in ("dining", "table")):
            return [0.0, 0.0, 0.0, 0.0, 1.0, 0.0]
        return [0.0, 0.0, 0.0, 0.0, 0.0, 1.0]


class CinderHybridSearchQualityTests(unittest.TestCase):
    def test_representative_queries_recall_expected_products_at_3(self) -> None:
        service = CinderHybridSearchService(provider=QualityFakeEmbeddingProvider())
        cases = [
            ("CND-SOF-1001", CinderSearchFilters(), {"CHG-001"}),
            (
                "storage bench",
                CinderSearchFilters(
                    category="furniture",
                    subcategory="benches",
                    material="wood",
                ),
                {"CHG-005", "CHG-006"},
            ),
            (
                "calm bedroom lighting",
                CinderSearchFilters(category="lighting", availability="in_stock"),
                {"CHG-015", "CHG-017"},
            ),
            (
                "runner for dining table",
                CinderSearchFilters(category="kitchen", subcategory="table linens"),
                {"CHG-023"},
            ),
            (
                "privacy shade for bedroom",
                CinderSearchFilters(category="window", subcategory="window shades"),
                {"CHG-019"},
            ),
            (
                "copper saucepan under 200",
                CinderSearchFilters(
                    category="kitchen",
                    subcategory="cookware",
                    material="stainless steel",
                    price_max=200,
                ),
                {"CHG-029"},
            ),
        ]

        hits = 0
        for query, filters, expected_ids in cases:
            output = service.search(query, filters=filters, top_k=3)
            result_ids = {result.product.product_id for result in output.results}
            hits += int(bool(result_ids & expected_ids))

        self.assertEqual(hits, len(cases))


if __name__ == "__main__":
    unittest.main()
