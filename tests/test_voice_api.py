from __future__ import annotations

import sys
import unittest
from pathlib import Path

from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from llm.api import app
from llm.errors import HuggingFaceSpeechError, HuggingFaceTTSError, OpenRouterError
from llm.speech_recognition import SpeechTranscriptionResult
from llm.text_to_speech import TextToSpeechResult
from llm.voice_api import create_voice_response


class FakeSpeechClient:
    has_api_key = True

    def __init__(self, text: str = "Привет") -> None:
        self.text = text
        self.calls: list[tuple[bytes, str]] = []

    def transcribe(self, audio_body: bytes, *, mime_type: str) -> SpeechTranscriptionResult:
        self.calls.append((audio_body, mime_type))
        return SpeechTranscriptionResult(
            text=self.text,
            model="openai/whisper-test",
        )


class FakeLLMClient:
    has_api_key = True
    model = "test-llm"

    def __init__(self, response: str = "Ответ от LLM.") -> None:
        self.response = response
        self.calls: list[tuple[str, str | None, dict[str, object] | None]] = []

    def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        options: dict[str, object] | None = None,
    ) -> str:
        self.calls.append((prompt, system, options))
        return self.response


class FakeTTSClient:
    has_api_key = True

    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def synthesize(self, text: str, *, language: str) -> TextToSpeechResult:
        self.calls.append((text, language))
        return TextToSpeechResult(
            audio_base64="d2F2",
            mime_type="audio/wav",
            model="facebook/mms-tts-test",
        )


class VoiceApiTests(unittest.TestCase):
    def test_app_registers_voice_endpoint(self) -> None:
        paths = {route.path for route in app.routes}

        self.assertIn("/voice/respond", paths)

    def test_create_voice_response_returns_transcript_and_llm_answer(self) -> None:
        speech_client = FakeSpeechClient()
        llm_client = FakeLLMClient()

        response = create_voice_response(
            b"audio",
            mime_type="audio/webm",
            language="ru",
            speech_client=speech_client,
            llm_client=llm_client,
            tts_client=FakeTTSClient(),
        )

        self.assertEqual(response.transcript, "Привет")
        self.assertEqual(response.response_text, "Ответ от LLM.")
        self.assertEqual(response.intent, "greeting")
        self.assertEqual(response.stt_provider, "huggingface")
        self.assertEqual(response.llm_provider, "openrouter")
        self.assertEqual(response.tts_audio_base64, "d2F2")
        self.assertEqual(response.tts_mime_type, "audio/wav")
        self.assertEqual(response.tts_provider, "huggingface")
        self.assertEqual(speech_client.calls, [(b"audio", "audio/webm")])
        self.assertIn("Detected command intent: greeting", llm_client.calls[0][0])
        self.assertIn("User voice transcript: Привет", llm_client.calls[0][0])
        self.assertIn("русском", llm_client.calls[0][1])

    def test_invalid_language_returns_http_error_before_provider_call(self) -> None:
        speech_client = FakeSpeechClient()

        with self.assertRaises(HTTPException) as raised:
            create_voice_response(
                b"audio",
                mime_type="audio/webm",
                language="ka",
                speech_client=speech_client,
                llm_client=FakeLLMClient(),
                tts_client=FakeTTSClient(),
            )

        self.assertEqual(raised.exception.status_code, 400)
        self.assertEqual(speech_client.calls, [])

    def test_missing_huggingface_token_returns_http_error(self) -> None:
        class MissingKeySpeechClient(FakeSpeechClient):
            has_api_key = False

        with self.assertRaises(HTTPException) as raised:
            create_voice_response(
                b"audio",
                mime_type="audio/webm",
                language="ru",
                speech_client=MissingKeySpeechClient(),
                llm_client=FakeLLMClient(),
                tts_client=FakeTTSClient(),
            )

        self.assertEqual(raised.exception.status_code, 500)
        self.assertEqual(raised.exception.detail, "HF_TOKEN is required")

    def test_provider_errors_return_bad_gateway(self) -> None:
        class FailingSpeechClient(FakeSpeechClient):
            def transcribe(self, audio_body: bytes, *, mime_type: str) -> SpeechTranscriptionResult:
                raise HuggingFaceSpeechError("ASR failed")

        with self.assertRaises(HTTPException) as raised:
            create_voice_response(
                b"audio",
                mime_type="audio/webm",
                language="ru",
                speech_client=FailingSpeechClient(),
                llm_client=FakeLLMClient(),
                tts_client=FakeTTSClient(),
            )

        self.assertEqual(raised.exception.status_code, 502)
        self.assertEqual(raised.exception.detail, "ASR failed")

    def test_empty_llm_response_returns_bad_gateway(self) -> None:
        with self.assertRaises(HTTPException) as raised:
            create_voice_response(
                b"audio",
                mime_type="audio/webm",
                language="en",
                speech_client=FakeSpeechClient(text="hello"),
                llm_client=FakeLLMClient(response=" "),
                tts_client=FakeTTSClient(),
            )

        self.assertEqual(raised.exception.status_code, 502)
        self.assertIsInstance(raised.exception.__cause__, OpenRouterError)

    def test_tts_provider_errors_return_bad_gateway(self) -> None:
        class FailingTTSClient(FakeTTSClient):
            def synthesize(self, text: str, *, language: str) -> TextToSpeechResult:
                raise HuggingFaceTTSError("TTS failed")

        with self.assertRaises(HTTPException) as raised:
            create_voice_response(
                b"audio",
                mime_type="audio/webm",
                language="en",
                speech_client=FakeSpeechClient(text="tell a joke"),
                llm_client=FakeLLMClient(response="A short joke."),
                tts_client=FailingTTSClient(),
            )

        self.assertEqual(raised.exception.status_code, 502)
        self.assertEqual(raised.exception.detail, "TTS failed")


if __name__ == "__main__":
    unittest.main()
