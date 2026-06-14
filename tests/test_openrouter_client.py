from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from llm import OpenRouterClient, OpenRouterError


class FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self.body = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self.body

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None


class OpenRouterClientTests(unittest.TestCase):
    def test_generate_posts_chat_completion_request(self) -> None:
        with patch(
            "llm.transport.request.urlopen",
            return_value=FakeResponse(
                {"choices": [{"message": {"content": "hello"}}]},
            ),
        ) as urlopen:
            client = OpenRouterClient(api_key="test-key")

            result = client.generate(
                "Say hello",
                system="Be short",
                options={"temperature": 0, "max_tokens": 20},
            )

        self.assertEqual(result, "hello")
        request = urlopen.call_args.args[0]
        self.assertEqual(
            request.full_url,
            "https://openrouter.ai/api/v1/chat/completions",
        )
        self.assertEqual(request.headers["Authorization"], "Bearer test-key")
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(
            payload,
            {
                "model": "deepseek/deepseek-v4-flash",
                "messages": [
                    {"role": "system", "content": "Be short"},
                    {"role": "user", "content": "Say hello"},
                ],
                "temperature": 0,
                "max_tokens": 20,
            },
        )

    def test_missing_api_key_fails_before_request(self) -> None:
        client = OpenRouterClient(api_key="")

        with self.assertRaisesRegex(OpenRouterError, "OPENROUTER_API_KEY"):
            client.generate("hello")

    def test_model_available_checks_models_response(self) -> None:
        with patch(
            "llm.transport.request.urlopen",
            return_value=FakeResponse(
                {"data": [{"id": "deepseek/deepseek-v4-flash"}]},
            ),
        ) as urlopen:
            client = OpenRouterClient()

            result = client.model_available()

        self.assertTrue(result)
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "https://openrouter.ai/api/v1/models")
        self.assertEqual(request.get_method(), "GET")


if __name__ == "__main__":
    unittest.main()
