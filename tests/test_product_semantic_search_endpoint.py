from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from llm.api import app
from llm.product_catalog import Product
from llm.product_search import ProductSearchService


class FakeEmbeddingProvider:
    model = "fake-product-embedding-model"
    has_api_key = True

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._vector_for(text) for text in texts]

    def _vector_for(self, text: str) -> list[float]:
        lower = text.lower()
        if "headphone" in lower or "flight" in lower or "focus" in lower:
            return [1.0, 0.0]
        return [0.0, 1.0]


def fake_service() -> ProductSearchService:
    return ProductSearchService(
        products=[
            Product(
                "PROD-004",
                "AeroQuiet Over-Ear Headphones",
                "Active noise cancellation for flights and focus work.",
                "audio",
                249.0,
                ("active noise cancellation", "travel case"),
            ),
            Product(
                "PROD-009",
                "BrewMate Thermal Coffee Maker",
                "Programmable coffee maker with a thermal carafe.",
                "kitchen",
                139.0,
                ("timer", "12 cup capacity"),
            ),
        ],
        provider=FakeEmbeddingProvider(),
    )


class ProductSemanticSearchEndpointTests(unittest.TestCase):
    def test_post_search_semantic_returns_ranked_products(self) -> None:
        client = TestClient(app)

        with patch(
            "llm.product_search_api.get_product_search_service",
            return_value=fake_service(),
        ):
            response = client.post(
                "/search/semantic",
                json={"query": "headphones for flights and focus work", "top_k": 1},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["model"], "fake-product-embedding-model")
        self.assertEqual(payload["top_k"], 1)
        self.assertEqual(payload["results"][0]["rank"], 1)
        self.assertEqual(payload["results"][0]["product_id"], "PROD-004")
        self.assertEqual(payload["results"][0]["category"], "audio")


if __name__ == "__main__":
    unittest.main()
