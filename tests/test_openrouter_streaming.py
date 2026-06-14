from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from llm import OpenRouterError
from llm.openrouter import DEFAULT_OPENROUTER_APP_TITLE, OpenRouterClient
from llm.openrouter_streaming import (
    parse_openrouter_stream_content,
    stream_openrouter_prompt_chunks,
)
from llm.sse_transport import iter_sse_data


class FakeStreamResponse:
    def __init__(self, lines: list[bytes]) -> None:
        self.lines = [
            split_line
            for line in lines
            for split_line in line.splitlines(keepends=True)
        ]

    def __iter__(self) -> object:
        return iter(self.lines)

    def __enter__(self) -> "FakeStreamResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None


class OpenRouterStreamingTests(unittest.TestCase):
    def test_stream_openrouter_prompt_posts_streaming_chat_request(self) -> None:
        lines = [
            b": OPENROUTER PROCESSING\n",
            b"\n",
            _sse_data({"choices": [{"delta": {"content": "Hel"}}]}),
            _sse_data({"choices": [{"delta": {"content": "lo"}}]}),
            b"data: [DONE]\n\n",
        ]

        with patch(
            "llm.sse_transport.request.urlopen",
            return_value=FakeStreamResponse(lines),
        ) as urlopen:
            client = OpenRouterClient(api_key="test-key")

            chunks = list(
                stream_openrouter_prompt_chunks(
                    client,
                    "Say hello",
                    system="Be short",
                    options={"max_tokens": 12},
                ),
            )

        self.assertEqual(chunks, ["Hel", "lo"])
        request = urlopen.call_args.args[0]
        self.assertEqual(
            request.full_url,
            "https://openrouter.ai/api/v1/chat/completions",
        )
        self.assertEqual(request.headers["Accept"], "text/event-stream")
        self.assertEqual(request.headers["Authorization"], "Bearer test-key")
        self.assertEqual(request.headers["X-title"], DEFAULT_OPENROUTER_APP_TITLE)
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(
            payload,
            {
                "model": "deepseek/deepseek-v4-flash",
                "messages": [
                    {"role": "system", "content": "Be short"},
                    {"role": "user", "content": "Say hello"},
                ],
                "max_tokens": 12,
                "stream": True,
            },
        )

    def test_iter_sse_data_ignores_comments_and_done_marker(self) -> None:
        data = list(
            iter_sse_data(
                [
                    b": OPENROUTER PROCESSING\n",
                    b"\n",
                    b"data: first\n",
                    b"\n",
                    b"data: [DONE]\n",
                    b"\n",
                    b"data: ignored\n",
                    b"\n",
                ],
            ),
        )

        self.assertEqual(data, ["first"])

    def test_parse_openrouter_stream_content_returns_empty_for_usage_chunk(
        self,
    ) -> None:
        content = parse_openrouter_stream_content('{"choices":[],"usage":{"total":1}}')

        self.assertEqual(content, "")

    def test_parse_openrouter_stream_content_raises_on_stream_error(self) -> None:
        with self.assertRaisesRegex(OpenRouterError, "Provider disconnected"):
            parse_openrouter_stream_content(
                '{"error":{"message":"Provider disconnected unexpectedly"}}',
            )

    def test_parse_openrouter_stream_content_raises_on_invalid_json(self) -> None:
        with self.assertRaisesRegex(OpenRouterError, "invalid stream JSON"):
            parse_openrouter_stream_content("not-json")


def _sse_data(payload: dict[str, object]) -> bytes:
    """Формирует строку data для fake OpenRouter SSE response."""
    return f"data: {json.dumps(payload)}\n\n".encode("utf-8")


if __name__ == "__main__":
    unittest.main()
