from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from llm.document_collection import load_documents
from llm.document_models import KnowledgeDocument
from llm.document_preprocessing import chunk_documents, preprocess_text
from llm.embedding_pipeline import (
    generate_embedding_artifact,
    search_embedding_artifact,
)
from llm.embedding_storage import load_embedding_artifact, save_embedding_artifact


class FakeEmbeddingProvider:
    model = "fake-embedding-model"

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            lower = text.lower()
            if "password" in lower:
                vectors.append([1.0, 0.0, 0.0])
            elif "vpn" in lower or "security" in lower:
                vectors.append([0.0, 1.0, 0.0])
            else:
                vectors.append([0.0, 0.0, 1.0])
        return vectors


class DocumentEmbeddingsTests(unittest.TestCase):
    def test_preprocess_text_cleans_formatting_and_keeps_case(self) -> None:
        text = "  ## Password\tReset\n\nUse **Forgot password**.\x00 "

        result = preprocess_text(text)

        self.assertEqual(result, "Password Reset Use Forgot password .")

    def test_chunk_documents_preserves_document_id_association(self) -> None:
        documents = [
            KnowledgeDocument(
                document_id="DOC-100",
                title="Long doc",
                category="test",
                text="one two three four five six",
            )
        ]

        chunks = chunk_documents(documents, max_words=3, overlap_words=1)

        self.assertEqual([chunk.document_id for chunk in chunks], ["DOC-100"] * 3)
        self.assertEqual(
            [chunk.chunk_id for chunk in chunks],
            [
                "DOC-100-CHUNK-001",
                "DOC-100-CHUNK-002",
                "DOC-100-CHUNK-003",
            ],
        )

    def test_generate_artifact_has_storage_metadata_shape(self) -> None:
        documents = [
            KnowledgeDocument(
                document_id="DOC-001",
                title="Password FAQ",
                category="faq",
                text="Reset a forgotten password from the sign-in page.",
            )
        ]

        artifact = generate_embedding_artifact(
            documents,
            FakeEmbeddingProvider(),
            chunk_words=50,
            chunk_overlap=0,
        )

        self.assertEqual(artifact["schema_version"], 1)
        self.assertEqual(artifact["provider"], "huggingface")
        self.assertEqual(artifact["model"], "fake-embedding-model")
        record = artifact["records"][0]
        self.assertEqual(record["document_id"], "DOC-001")
        self.assertEqual(record["chunk_id"], "DOC-001-CHUNK-001")
        self.assertEqual(record["embedding"], [1.0, 0.0, 0.0])

    def test_save_and_load_embedding_artifact(self) -> None:
        artifact = {
            "schema_version": 1,
            "provider": "huggingface",
            "model": "fake",
            "preprocessing": {"case_policy": "keep-case"},
            "records": [{"document_id": "DOC-001", "embedding": [1.0]}],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "embeddings.json"

            save_embedding_artifact(path, artifact)
            loaded = load_embedding_artifact(path)

        self.assertEqual(loaded, artifact)

    def test_similarity_ranking_returns_password_document_first(self) -> None:
        documents = [
            KnowledgeDocument("DOC-001", "Password FAQ", "faq", "reset password"),
            KnowledgeDocument("DOC-002", "Security", "security", "vpn security"),
        ]
        artifact = generate_embedding_artifact(
            documents,
            FakeEmbeddingProvider(),
            chunk_words=50,
            chunk_overlap=0,
        )

        matches = search_embedding_artifact(
            artifact,
            "how do I reset my password?",
            FakeEmbeddingProvider(),
            top_k=2,
        )

        self.assertEqual(matches[0].document_id, "DOC-001")
        self.assertGreater(matches[0].score, matches[1].score)

    def test_committed_sample_dataset_has_unique_business_documents(self) -> None:
        path = Path(__file__).resolve().parents[1] / "data/internal_knowledge_documents.json"

        documents = load_documents(path)

        self.assertEqual(len(documents), 20)
        self.assertEqual(len({doc.document_id for doc in documents}), 20)
        self.assertTrue(any("Password Reset" in doc.title for doc in documents))


if __name__ == "__main__":
    unittest.main()
