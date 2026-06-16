from __future__ import annotations

import sys
import unittest
from pathlib import Path

from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from llm.api import app
from llm.product_catalog import Product, load_products
from llm.product_search import ProductSearchService, build_product_search_index
from llm.product_search_api import (
    SemanticSearchRequest,
    create_semantic_search_response,
)


class FakeEmbeddingProvider:
    model = "fake-product-embedding-model"
    has_api_key = True

    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(list(texts))
        return [self._vector_for(text) for text in texts]

    def _vector_for(self, text: str) -> list[float]:
        lower = text.lower()
        if any(word in lower for word in ("chair", "recliner", "reading", "lounge")):
            return [1.0, 0.0, 0.0, 0.0]
        if any(word in lower for word in ("headphone", "earbud", "flight", "focus", "noise")):
            return [0.0, 1.0, 0.0, 0.0]
        if any(word in lower for word in ("hub", "automate", "routine", "light", "scene")):
            return [0.0, 0.0, 1.0, 0.0]
        return [0.0, 0.0, 0.0, 1.0]


def sample_products() -> list[Product]:
    return [
        Product(
            "PROD-001",
            "Luna Reading Armchair",
            "Deep upholstered seat for a book nook.",
            "furniture",
            349.0,
            ("reading nook", "lumbar support"),
        ),
        Product(
            "PROD-004",
            "AeroQuiet Over-Ear Headphones",
            "Active noise cancellation for flights and focus work.",
            "audio",
            249.0,
            ("travel case", "40 hour battery"),
        ),
        Product(
            "PROD-006",
            "HomeFlow Smart Hub",
            "Connects lights, plugs, sensors, and routines.",
            "smart home",
            129.0,
            ("routine automation", "lighting scenes"),
        ),
        Product(
            "PROD-009",
            "BrewMate Thermal Coffee Maker",
            "Programmable coffee maker with a thermal carafe.",
            "kitchen",
            139.0,
            ("timer", "12 cup capacity"),
        ),
    ]


class ProductSemanticSearchTests(unittest.TestCase):
    def test_app_registers_semantic_search_endpoint(self) -> None:
        paths = {route.path for route in app.routes}

        self.assertIn("/search/semantic", paths)

    def test_committed_product_dataset_has_fifty_items_without_secrets(self) -> None:
        path = Path(__file__).resolve().parents[1] / "data/product_catalog.json"

        products = load_products(path)
        raw = path.read_text(encoding="utf-8")

        self.assertEqual(len(products), 50)
        self.assertEqual(len({product.product_id for product in products}), 50)
        self.assertTrue(all(product.name and product.description for product in products))
        self.assertTrue(all(product.category and product.price > 0 for product in products))
        self.assertNotIn("HF_TOKEN", raw)
        self.assertNotIn("Authorization", raw)
        self.assertNotIn("hf_", raw)

    def test_build_index_and_rank_products_with_fake_embeddings(self) -> None:
        provider = FakeEmbeddingProvider()
        index = build_product_search_index(sample_products(), provider)

        query_embedding = provider.embed_texts(["headphones for flights and focus work"])[0]
        results = index.search(query_embedding, top_k=2)

        self.assertEqual(index.model, "fake-product-embedding-model")
        self.assertEqual(results[0].product.product_id, "PROD-004")
        self.assertGreater(results[0].score, results[1].score)

    def test_api_response_contains_metadata_and_ranked_product_fields(self) -> None:
        service = ProductSearchService(
            products=sample_products(),
            provider=FakeEmbeddingProvider(),
        )

        response = create_semantic_search_response(
            SemanticSearchRequest(
                query="device to automate lights and home routines",
                top_k=1,
            ),
            service=service,
        )

        self.assertEqual(response.model, "fake-product-embedding-model")
        self.assertEqual(response.top_k, 1)
        self.assertEqual(response.normalized_query, "device to automate lights and home routines")
        self.assertEqual(response.results[0].rank, 1)
        self.assertEqual(response.results[0].product_id, "PROD-006")
        self.assertEqual(response.results[0].category, "smart home")
        self.assertEqual(response.results[0].price, 129.0)

    def test_query_validation_returns_http_error_before_embedding_call(self) -> None:
        provider = FakeEmbeddingProvider()
        service = ProductSearchService(products=sample_products(), provider=provider)

        with self.assertRaises(HTTPException) as raised:
            create_semantic_search_response(
                SemanticSearchRequest(query="   ", top_k=3),
                service=service,
            )

        self.assertEqual(raised.exception.status_code, 400)
        self.assertEqual(raised.exception.detail, "query must be a non-empty string")
        self.assertEqual(provider.calls, [])

    def test_top_k_validation_returns_http_error(self) -> None:
        service = ProductSearchService(
            products=sample_products(),
            provider=FakeEmbeddingProvider(),
        )

        with self.assertRaises(HTTPException) as raised:
            create_semantic_search_response(
                SemanticSearchRequest(query="reading chair", top_k=0),
                service=service,
            )

        self.assertEqual(raised.exception.status_code, 400)
        self.assertEqual(raised.exception.detail, "top_k must be between 1 and 20")

    def test_missing_token_error_does_not_expose_secret(self) -> None:
        class MissingKeyProvider(FakeEmbeddingProvider):
            has_api_key = False
            secret = "not-a-real-token"

        service = ProductSearchService(
            products=sample_products(),
            provider=MissingKeyProvider(),
        )

        with self.assertRaises(HTTPException) as raised:
            create_semantic_search_response(
                SemanticSearchRequest(query="reading chair", top_k=1),
                service=service,
            )

        self.assertEqual(raised.exception.status_code, 500)
        self.assertEqual(raised.exception.detail, "HF_TOKEN is required")
        self.assertNotIn("not-a-real-token", raised.exception.detail)

    def test_service_reuses_built_index_on_repeated_calls(self) -> None:
        provider = FakeEmbeddingProvider()
        service = ProductSearchService(products=sample_products(), provider=provider)

        first = service.search("comfortable chair for a reading corner", top_k=1)
        second = service.search("headphones for flights and focus work", top_k=1)

        self.assertEqual(first.results[0].product.product_id, "PROD-001")
        self.assertEqual(second.results[0].product.product_id, "PROD-004")
        self.assertEqual([len(call) for call in provider.calls], [4, 1, 1])


if __name__ == "__main__":
    unittest.main()
