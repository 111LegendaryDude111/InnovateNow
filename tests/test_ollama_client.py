from __future__ import annotations

import json
import sys
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from llm import OllamaClient, OllamaError


class FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self.body = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self.body

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None


class OllamaClientTests(unittest.TestCase):
    def test_generate_posts_non_streaming_generate_request(self) -> None:
        with patch(
            "llm.transport.request.urlopen",
            return_value=FakeResponse({"response": "hello"}),
        ) as urlopen:
            client = OllamaClient(model="llama3.2")

            result = client.generate("Say hello", options={"temperature": 0})

        self.assertEqual(result, "hello")
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "http://localhost:11434/api/generate")
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(
            payload,
            {
                "model": "llama3.2",
                "prompt": "Say hello",
                "stream": False,
                "options": {"temperature": 0},
            },
        )

    def test_chat_posts_messages_and_returns_assistant_content(self) -> None:
        with patch(
            "llm.transport.request.urlopen",
            return_value=FakeResponse({"message": {"content": "answer"}}),
        ) as urlopen:
            client = OllamaClient(model="qwen3", base_url="http://localhost:11434/api")

            result = client.chat([{"role": "user", "content": "question"}])

        self.assertEqual(result, "answer")
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "http://localhost:11434/api/chat")
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(
            payload,
            {
                "model": "qwen3",
                "messages": [{"role": "user", "content": "question"}],
                "stream": False,
            },
        )

    def test_version_gets_api_version_and_exposes_port(self) -> None:
        with patch(
            "llm.transport.request.urlopen",
            return_value=FakeResponse({"version": "0.15.1"}),
        ) as urlopen:
            client = OllamaClient(model="qwen3", base_url="http://localhost:11434")

            result = client.version()

        self.assertEqual(result, {"version": "0.15.1"})
        self.assertEqual(client.port, 11434)
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "http://localhost:11434/api/version")
        self.assertEqual(request.get_method(), "GET")

    def test_http_error_uses_ollama_error_message(self) -> None:
        def raise_http_error(*args: object, **kwargs: object) -> None:
            raise HTTPError(
                "http://localhost:11434/api/generate",
                404,
                "Not Found",
                hdrs=None,
                fp=BytesIO(b'{"error": "model not found"}'),
            )

        with patch("llm.transport.request.urlopen", side_effect=raise_http_error):
            client = OllamaClient(model="missing")

            with self.assertRaisesRegex(OllamaError, "model not found"):
                client.generate("hello")


if __name__ == "__main__":
    unittest.main()
