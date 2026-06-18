from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from llm.api import app
from llm.cinder_hybrid_search import CinderHybridSearchService
from llm.cinder_hybrid_search_api import (
    CinderHybridSearchRequest,
    create_cinder_hybrid_search_response,
)
from llm.cinder_search_models import CinderSearchFilters


class FakeCinderEmbeddingProvider:
    model = "fake-cinder-embedding-model"
    has_api_key = True

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._vector_for(text) for text in texts]

    def _vector_for(self, text: str) -> list[float]:
        lower = text.lower()
        if "storage" in lower or "entryway" in lower:
            return [1.0, 0.0, 0.0, 0.0, 0.0]
        if "lamp" in lower or "lighting" in lower or "shade" in lower:
            return [0.0, 1.0, 0.0, 0.0, 0.0]
        if "patio" in lower or "outdoor" in lower:
            return [0.0, 0.0, 1.0, 0.0, 0.0]
        if "dining" in lower or "table" in lower:
            return [0.0, 0.0, 0.0, 1.0, 0.0]
        if "rug" in lower or "runner" in lower:
            return [0.0, 0.0, 0.0, 0.0, 1.0]
        return [0.2, 0.2, 0.2, 0.2, 0.2]


class MissingEmbeddingProvider(FakeCinderEmbeddingProvider):
    model = "missing-token-model"
    has_api_key = False


def fake_service(provider: object | None = None) -> CinderHybridSearchService:
    return CinderHybridSearchService(
        provider=provider or FakeCinderEmbeddingProvider(),
    )


class CinderHybridSearchTests(unittest.TestCase):
    def test_app_registers_cinder_hybrid_endpoint(self) -> None:
        paths = {route.path for route in app.routes}

        self.assertIn("/search/cinder/hybrid", paths)

    def test_exact_sku_uses_keyword_fallback_without_vector_provider(self) -> None:
        service = fake_service(MissingEmbeddingProvider())

        output = service.search("CND-SOF-1001", top_k=1)

        self.assertTrue(output.fallback_applied)
        self.assertEqual(output.model, "keyword-only")
        self.assertIn("vector_provider_unavailable", output.fallback_reason or "")
        self.assertEqual(output.results[0].product.product_id, "CHG-001")
        self.assertIn("sku", output.results[0].matched_keyword_fields)

    def test_filters_constrain_storage_bench_results(self) -> None:
        service = fake_service()

        output = service.search(
            "storage bench",
            filters=CinderSearchFilters(
                category="furniture",
                subcategory="benches",
                material="wood",
                availability="in_stock",
            ),
            top_k=2,
        )

        self.assertEqual(
            {result.product.product_id for result in output.results},
            {"CHG-005", "CHG-006"},
        )
        self.assertFalse(output.fallback_applied)
        self.assertEqual(output.filtered_candidate_count, 2)

    def test_strict_filter_fallback_is_explicit(self) -> None:
        service = fake_service(MissingEmbeddingProvider())

        output = service.search(
            "CND-SOF-1001",
            filters=CinderSearchFilters(availability="out_of_stock"),
            top_k=1,
        )

        self.assertTrue(output.fallback_applied)
        self.assertIn("filters_relaxed_no_results", output.fallback_reason or "")
        self.assertEqual(output.results[0].product.product_id, "CHG-001")

    def test_api_response_contains_hybrid_metadata(self) -> None:
        response = create_cinder_hybrid_search_response(
            CinderHybridSearchRequest(
                query="storage bench",
                top_k=1,
                category="furniture",
                subcategory="benches",
                material="wood",
                availability="in_stock",
            ),
            service=fake_service(),
        )

        self.assertEqual(response.model, "fake-cinder-embedding-model")
        self.assertEqual(response.top_k, 1)
        self.assertGreater(response.keyword_candidate_count, 0)
        self.assertGreater(response.vector_candidate_count, 0)
        self.assertEqual(response.results[0].category, "furniture")
        self.assertEqual(response.results[0].availability, "in_stock")

    def test_endpoint_returns_ranked_products(self) -> None:
        client = TestClient(app)

        with patch(
            "llm.cinder_hybrid_search_api.get_cinder_search_service",
            return_value=fake_service(),
        ):
            response = client.post(
                "/search/cinder/hybrid",
                json={"query": "calm bedroom lighting", "top_k": 1},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["model"], "fake-cinder-embedding-model")
        self.assertEqual(payload["results"][0]["rank"], 1)
        self.assertIn(payload["results"][0]["category"], {"lighting", "window"})

    def test_invalid_filters_return_http_error(self) -> None:
        with self.assertRaises(HTTPException) as raised:
            create_cinder_hybrid_search_response(
                CinderHybridSearchRequest(
                    query="desk",
                    price_min=100,
                    price_max=50,
                ),
                service=fake_service(),
            )

        self.assertEqual(raised.exception.status_code, 400)
        self.assertEqual(
            raised.exception.detail,
            "price_min must be less than or equal to price_max",
        )


if __name__ == "__main__":
    unittest.main()
