from __future__ import annotations

import math
import sys
import unittest
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from llm.document_collection import load_documents
from llm.document_models import KnowledgeDocument
from llm.qdrant_vector_store import (
    DEFAULT_QDRANT_COLLECTION,
    QDRANT_DISTANCE,
    build_qdrant_points,
    ingest_qdrant_documents,
    search_qdrant_documents,
)


class FakeEmbeddingProvider:
    model = "fake-qdrant-embedding-model"

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._vector_for(text) for text in texts]

    def _vector_for(self, text: str) -> list[float]:
        lower = text.lower()
        if "password" in lower or "credential" in lower:
            return [1.0, 0.0, 0.0]
        if "headphone" in lower or "microphone" in lower or "audio" in lower:
            return [0.0, 1.0, 0.0]
        return [0.0, 0.0, 1.0]


@dataclass(frozen=True)
class FakeScoredPoint:
    score: float
    payload: dict[str, object]


@dataclass(frozen=True)
class FakeQueryResponse:
    points: list[FakeScoredPoint]


class FakeQdrantClient:
    def __init__(self) -> None:
        self.collections: set[str] = set()
        self.deleted: list[str] = []
        self.created: list[tuple[str, object]] = []
        self.points: list[object] = []

    def collection_exists(self, collection_name: str) -> bool:
        return collection_name in self.collections

    def delete_collection(self, collection_name: str) -> None:
        self.deleted.append(collection_name)
        self.collections.discard(collection_name)

    def create_collection(
        self, collection_name: str, *, vectors_config: object
    ) -> None:
        self.created.append((collection_name, vectors_config))
        self.collections.add(collection_name)

    def upsert(self, collection_name: str, *, points: list[object], wait: bool) -> None:
        self.collections.add(collection_name)
        self.points = points

    def query_points(
        self,
        collection_name: str,
        *,
        query: list[float],
        limit: int,
        with_payload: bool,
    ) -> FakeQueryResponse:
        scored = [
            FakeScoredPoint(_cosine(query, point.vector), point.payload)
            for point in self.points
        ]
        scored.sort(key=lambda point: point.score, reverse=True)
        return FakeQueryResponse(scored[:limit])


class QdrantVectorSearchTests(unittest.TestCase):
    def test_committed_qdrant_dataset_has_sixty_unique_items(self) -> None:
        path = Path(__file__).resolve().parents[1] / "data/qdrant_sample_documents.json"

        documents = load_documents(path)

        self.assertEqual(len(documents), 60)
        self.assertEqual(len({document.document_id for document in documents}), 60)
        self.assertTrue(
            any("password" in document.text.lower() for document in documents)
        )
        self.assertTrue(
            any("headphones" in document.text.lower() for document in documents)
        )

    def test_build_points_preserves_payload_metadata(self) -> None:
        document = KnowledgeDocument("QDR-100", "Password FAQ", "faq", "reset password")

        points = build_qdrant_points([document], [[1.0, 0.0]], model="fake-model")

        self.assertEqual(points[0].id, 1)
        self.assertEqual(points[0].vector, [1.0, 0.0])
        self.assertEqual(points[0].payload["source_id"], "QDR-100")
        self.assertEqual(points[0].payload["category"], "faq")
        self.assertEqual(points[0].payload["embedding_model"], "fake-model")

    def test_ingest_creates_cosine_collection_and_upserts_points(self) -> None:
        documents = [
            KnowledgeDocument("QDR-001", "Password", "faq", "reset password"),
            KnowledgeDocument(
                "QDR-007", "Headphones", "product", "wireless headphones"
            ),
        ]
        client = FakeQdrantClient()

        summary = ingest_qdrant_documents(
            client,
            documents,
            FakeEmbeddingProvider(),
            collection_name=DEFAULT_QDRANT_COLLECTION,
        )

        collection_name, vectors_config = client.created[0]
        self.assertEqual(collection_name, DEFAULT_QDRANT_COLLECTION)
        self.assertEqual(vectors_config.size, 3)
        self.assertEqual(vectors_config.distance, QDRANT_DISTANCE)
        self.assertEqual(summary.point_count, 2)
        self.assertEqual(client.points[0].payload["source_id"], "QDR-001")

    def test_recreate_deletes_existing_collection_before_create(self) -> None:
        client = FakeQdrantClient()
        client.collections.add(DEFAULT_QDRANT_COLLECTION)

        ingest_qdrant_documents(
            client,
            [KnowledgeDocument("QDR-001", "Password", "faq", "reset password")],
            FakeEmbeddingProvider(),
            collection_name=DEFAULT_QDRANT_COLLECTION,
            recreate=True,
        )

        self.assertEqual(client.deleted, [DEFAULT_QDRANT_COLLECTION])
        self.assertEqual(client.created[0][0], DEFAULT_QDRANT_COLLECTION)

    def test_search_demo_queries_return_password_and_headphones_matches(self) -> None:
        documents = [
            KnowledgeDocument("QDR-001", "Password FAQ", "faq", "reset password"),
            KnowledgeDocument("QDR-007", "Headphones", "product", "headphones audio"),
            KnowledgeDocument("QDR-013", "Billing", "faq", "update billing card"),
        ]
        client = FakeQdrantClient()
        provider = FakeEmbeddingProvider()
        ingest_qdrant_documents(client, documents, provider)

        password_matches = search_qdrant_documents(
            client,
            provider,
            "how do I reset my password?",
            top_k=3,
        )
        headphone_matches = search_qdrant_documents(
            client,
            provider,
            "wireless headphones with microphone and audio controls",
            top_k=3,
        )

        self.assertEqual(password_matches[0].source_id, "QDR-001")
        self.assertEqual(headphone_matches[0].source_id, "QDR-007")


def _cosine(left: list[float], right: list[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    return dot / (left_norm * right_norm)


if __name__ == "__main__":
    unittest.main()
