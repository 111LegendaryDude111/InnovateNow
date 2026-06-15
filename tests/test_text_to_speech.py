from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from llm.errors import HuggingFaceTTSError
from llm.text_to_speech import HuggingFaceTTSClient, require_tts_text


class FakeBinaryResponse:
    headers = {"Content-Type": "audio/wav"}

    def read(self) -> bytes:
        return b"wav-bytes"

    def __enter__(self) -> "FakeBinaryResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None


class TextToSpeechTests(unittest.TestCase):
    def test_synthesize_posts_text_to_language_model(self) -> None:
        with patch("llm.transport.request.urlopen", return_value=FakeBinaryResponse()) as urlopen:
            client = HuggingFaceTTSClient(api_key="test-key")

            result = client.synthesize("Hello", language="en")

        self.assertEqual(result.audio_base64, "d2F2LWJ5dGVz")
        self.assertEqual(result.mime_type, "audio/wav")
        self.assertEqual(result.model, "facebook/mms-tts-eng")
        request = urlopen.call_args.args[0]
        self.assertEqual(
            request.full_url,
            "https://router.huggingface.co/hf-inference/models/facebook/mms-tts-eng",
        )
        self.assertEqual(request.headers["Authorization"], "Bearer test-key")
        self.assertIn(b'"inputs": "Hello"', request.data)

    def test_missing_huggingface_token_fails_before_request(self) -> None:
        client = HuggingFaceTTSClient(api_key="")

        with self.assertRaisesRegex(HuggingFaceTTSError, "HF_TOKEN"):
            client.synthesize("Hello", language="en")

    def test_requires_non_empty_tts_text(self) -> None:
        with self.assertRaisesRegex(ValueError, "TTS text"):
            require_tts_text(" ")

    def test_rejects_unsupported_language(self) -> None:
        client = HuggingFaceTTSClient(api_key="test-key")

        with self.assertRaisesRegex(ValueError, "not supported"):
            client.synthesize("Hello", language="ka")


if __name__ == "__main__":
    unittest.main()
