from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from llm.errors import HuggingFaceSpeechConnectionError, HuggingFaceSpeechError
from llm.speech_recognition import (
    HuggingFaceSpeechClient,
    extract_transcript_text,
    require_voice_audio,
    require_voice_mime_type,
)


class FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self.body = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self.body

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None


class SpeechRecognitionTests(unittest.TestCase):
    def test_transcribe_posts_audio_bytes_to_huggingface(self) -> None:
        with patch(
            "llm.transport.request.urlopen",
            return_value=FakeResponse({"text": "hello from audio"}),
        ) as urlopen:
            client = HuggingFaceSpeechClient(api_key="test-key")

            result = client.transcribe(
                b"audio-bytes", mime_type="audio/webm;codecs=opus"
            )

        self.assertEqual(result.text, "hello from audio")
        self.assertEqual(result.provider, "huggingface")
        request = urlopen.call_args.args[0]
        self.assertEqual(
            request.full_url,
            "https://router.huggingface.co/hf-inference/models/openai/whisper-large-v3",
        )
        self.assertEqual(request.data, b"audio-bytes")
        self.assertEqual(request.headers["Authorization"], "Bearer test-key")
        self.assertEqual(request.headers["Content-type"], "audio/webm")

    def test_missing_huggingface_token_fails_before_request(self) -> None:
        client = HuggingFaceSpeechClient(api_key="")

        with self.assertRaisesRegex(HuggingFaceSpeechError, "HF_TOKEN"):
            client.transcribe(b"audio", mime_type="audio/webm")

    def test_timeout_becomes_connection_error(self) -> None:
        with patch("llm.transport.request.urlopen", side_effect=TimeoutError):
            client = HuggingFaceSpeechClient(api_key="test-key")

            with self.assertRaisesRegex(HuggingFaceSpeechConnectionError, "Timed out"):
                client.transcribe(b"audio", mime_type="audio/webm")

    def test_requires_non_empty_audio_body(self) -> None:
        with self.assertRaisesRegex(ValueError, "audio body"):
            require_voice_audio(b"")

    def test_rejects_non_audio_content_type(self) -> None:
        with self.assertRaisesRegex(ValueError, "audio content type"):
            require_voice_mime_type("text/plain")

    def test_missing_transcript_text_raises_provider_error(self) -> None:
        with self.assertRaisesRegex(HuggingFaceSpeechError, "no transcript"):
            extract_transcript_text({"text": "  "})


if __name__ == "__main__":
    unittest.main()
