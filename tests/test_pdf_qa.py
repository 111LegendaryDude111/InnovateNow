from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from llm.api import app
from llm.pdf_processing import PdfChunk, PdfDocumentText, PdfPage
from llm.pdf_qa import ANSWER_NOT_FOUND, answer_pdf_question
from llm.pdf_qa_api import PdfAskRequest, create_pdf_ask_response
from llm.pdf_qa_models import PdfQaStore


class FakeEmbeddingProvider:
    model = "fake-pdf-embedding"
    has_api_key = True

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._vector_for(text) for text in texts]

    def _vector_for(self, text: str) -> list[float]:
        lower = text.lower()
        if "password" in lower or "reset" in lower:
            return [1.0, 0.0]
        if "expense" in lower or "invoice" in lower:
            return [0.0, 1.0]
        return [0.0, -1.0]


class FakeAnswerProvider:
    model = "fake-openrouter"
    has_api_key = True

    def __init__(self) -> None:
        self.prompts: list[str] = []

    def generate(self, prompt: str, **_: object) -> str:
        self.prompts.append(prompt)
        return "Use the reset form and confirm the account owner."


def fake_pdf_text() -> PdfDocumentText:
    return PdfDocumentText(
        "handbook.pdf",
        2,
        [
            PdfPage(
                "handbook.pdf",
                2,
                "Password reset requires the reset form and owner confirmation.",
            )
        ],
    )


class PdfQaTests(unittest.TestCase):
    def test_upload_requires_files(self) -> None:
        response = TestClient(app).post("/pdf/ingest")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "at least one PDF file is required")

    def test_upload_rejects_non_pdf_file(self) -> None:
        response = TestClient(app).post(
            "/pdf/ingest",
            files={"files": ("notes.txt", b"hello", "text/plain")},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "only .pdf files are supported")

    def test_upload_rejects_invalid_pdf(self) -> None:
        response = TestClient(app).post(
            "/pdf/ingest",
            files={"files": ("bad.pdf", b"not a pdf", "application/pdf")},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "could not read PDF: bad.pdf")

    def test_missing_hf_token_does_not_expose_secret(self) -> None:
        class MissingEmbeddingProvider(FakeEmbeddingProvider):
            has_api_key = False
            secret = "not-a-real-token"

        with (
            patch("llm.pdf_qa.extract_pdf_text", return_value=fake_pdf_text()),
            patch(
                "llm.pdf_qa_api.HuggingFaceEmbeddingClient.from_env",
                return_value=MissingEmbeddingProvider(),
            ),
        ):
            response = TestClient(app).post(
                "/pdf/ingest",
                files={"files": ("handbook.pdf", b"%PDF", "application/pdf")},
            )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["detail"], "HF_TOKEN is required")
        self.assertNotIn("not-a-real-token", response.text)

    def test_unknown_session_returns_http_error(self) -> None:
        with self.assertRaises(HTTPException) as raised:
            create_pdf_ask_response(
                PdfAskRequest(session_id="missing", question="What is required?")
            )

        self.assertEqual(raised.exception.status_code, 404)
        self.assertEqual(raised.exception.detail, "unknown PDF session")

    def test_blank_question_returns_http_error(self) -> None:
        with self.assertRaises(HTTPException) as raised:
            create_pdf_ask_response(PdfAskRequest(session_id="x", question="   "))

        self.assertEqual(raised.exception.status_code, 400)
        self.assertEqual(raised.exception.detail, "question must be a non-empty string")

    def test_session_without_chunks_returns_http_error(self) -> None:
        store = PdfQaStore()
        session = store.create_session(
            documents=[], chunks=[], embeddings=[], embedding_model="fake"
        )

        with self.assertRaises(HTTPException) as raised:
            create_pdf_ask_response(
                PdfAskRequest(session_id=session.session_id, question="Anything?"),
                store=store,
            )

        self.assertEqual(raised.exception.status_code, 400)
        self.assertEqual(raised.exception.detail, "session has no processed chunks")

    def test_no_relevant_context_returns_controlled_answer(self) -> None:
        store = PdfQaStore()
        session = store.create_session(
            documents=[], chunks=[fake_chunk("handbook.pdf:p2:c1")],
            embeddings=[[1.0, 0.0]], embedding_model="fake-pdf-embedding",
        )

        result = answer_pdf_question(
            session_id=session.session_id,
            question="vacation policy",
            store=store,
            embedding_provider=FakeEmbeddingProvider(),
            answer_provider=FakeAnswerProvider(),
            top_k=1,
        )

        self.assertEqual(result.answer, ANSWER_NOT_FOUND)
        self.assertEqual(result.sources, [])
        self.assertEqual(result.retrieved_chunks[0].rank, 1)

    def test_ingest_and_ask_routes_return_answer_with_sources(self) -> None:
        client = TestClient(app)
        answer_provider = FakeAnswerProvider()

        with (
            patch("llm.pdf_qa.extract_pdf_text", return_value=fake_pdf_text()),
            patch(
                "llm.pdf_qa_api.HuggingFaceEmbeddingClient.from_env",
                return_value=FakeEmbeddingProvider(),
            ),
            patch(
                "llm.pdf_qa_api.OpenRouterClient.from_env",
                return_value=answer_provider,
            ),
        ):
            ingest = client.post(
                "/pdf/ingest",
                files={"files": ("handbook.pdf", b"%PDF", "application/pdf")},
            )
            ask = client.post(
                "/pdf/ask",
                json={
                    "session_id": ingest.json()["session_id"],
                    "question": "How do I reset a password?",
                    "top_k": 1,
                },
            )

        self.assertEqual(ingest.status_code, 200)
        self.assertEqual(ask.status_code, 200)
        payload = ask.json()
        self.assertEqual(payload["answer"], "Use the reset form and confirm the account owner.")
        self.assertEqual(payload["sources"][0]["filename"], "handbook.pdf")
        self.assertEqual(payload["sources"][0]["page"], 2)
        self.assertEqual(payload["retrieved_chunks"][0]["rank"], 1)
        self.assertEqual(payload["provider_metadata"]["answer_model"], "fake-openrouter")
        self.assertIn("Password reset", answer_provider.prompts[0])


def fake_chunk(chunk_id: str):
    return PdfChunk("handbook.pdf", 2, chunk_id, "Password reset requires a form.", 1)
