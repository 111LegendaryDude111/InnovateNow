from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from llm.api import LOCAL_FRONTEND_ORIGINS, StreamRequest, app, create_stream_response
from llm.streaming import format_sse_event, iter_sse_events


def _parse_sse_event(raw_event: bytes) -> dict[str, object]:
    """Разбирает одно SSE-событие для проверок тестов."""
    event_line, data_line = raw_event.decode("utf-8").strip().splitlines()
    return {
        "event": event_line.removeprefix("event: "),
        "data": json.loads(data_line.removeprefix("data: ")),
    }


class FakeApiClient:
    has_api_key = True


class StreamingApiTests(unittest.TestCase):
    def test_app_registers_stream_endpoint(self) -> None:
        paths = {route.path for route in app.routes}

        self.assertIn("/llm/stream", paths)

    def test_app_allows_local_frontend_origin(self) -> None:
        cors_middleware = next(
            middleware
            for middleware in app.user_middleware
            if middleware.cls is CORSMiddleware
        )

        self.assertEqual(
            cors_middleware.kwargs["allow_origins"], LOCAL_FRONTEND_ORIGINS
        )

    def test_create_stream_response_returns_sse_response(self) -> None:
        response = create_stream_response(
            StreamRequest(prompt="Explain testing", system="Be short"),
            client=FakeApiClient(),
        )

        self.assertEqual(response.media_type, "text/event-stream")
        self.assertEqual(response.headers["cache-control"], "no-cache")
        self.assertEqual(response.headers["x-accel-buffering"], "no")

    def test_blank_prompt_returns_http_error(self) -> None:
        with self.assertRaises(HTTPException) as raised:
            create_stream_response(StreamRequest(prompt="   "), client=FakeApiClient())

        self.assertEqual(raised.exception.status_code, 400)
        self.assertEqual(
            raised.exception.detail,
            "prompt must be a non-empty string",
        )

    def test_missing_openrouter_api_key_returns_http_error(self) -> None:
        class MissingKeyClient:
            has_api_key = False

        with self.assertRaises(HTTPException) as raised:
            create_stream_response(
                StreamRequest(prompt="Explain testing"),
                client=MissingKeyClient(),
            )

        self.assertEqual(raised.exception.status_code, 500)
        self.assertEqual(raised.exception.detail, "OPENROUTER_API_KEY is required")

    def test_iter_sse_events_streams_start_delta_and_done(self) -> None:
        events = [
            _parse_sse_event(raw_event)
            for raw_event in iter_sse_events(["Hello ", "world"])
        ]

        self.assertEqual(events[0]["event"], "start")
        self.assertEqual(events[0]["data"]["done"], False)
        self.assertEqual(events[1]["data"]["content"], "Hello ")
        self.assertEqual(events[2]["data"]["content"], "world")
        self.assertEqual(events[-1]["event"], "done")
        self.assertEqual(events[-1]["data"]["done"], True)

    def test_iter_sse_events_sends_error_event_on_stream_failure(self) -> None:
        def broken_chunks() -> object:
            """Имитирует ошибку источника chunks после начала SSE."""
            raise RuntimeError("stream failed")
            yield "unreachable"

        events = [
            _parse_sse_event(raw_event)
            for raw_event in iter_sse_events(broken_chunks())
        ]

        self.assertEqual([event["event"] for event in events], ["start", "error"])
        self.assertEqual(events[-1]["data"]["done"], True)
        self.assertEqual(events[-1]["data"]["error"], "stream failed")

    def test_format_sse_event_uses_stable_json_payload(self) -> None:
        event = _parse_sse_event(
            format_sse_event(
                "delta",
                {"content": "hello", "index": 1, "done": False},
            ),
        )

        self.assertEqual(event["event"], "delta")
        self.assertEqual(
            event["data"],
            {"type": "delta", "content": "hello", "index": 1, "done": False},
        )


if __name__ == "__main__":
    unittest.main()
