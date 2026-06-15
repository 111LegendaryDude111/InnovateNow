from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .errors import OpenRouterError
from .voice_intents import classify_voice_intent

SUPPORTED_VOICE_LANGUAGES = {"ru", "en"}
VOICE_SYSTEM_PROMPTS = {
    "ru": (
        "Ты голосовой ассистент Task Learn. Отвечай на русском, естественно и "
        "кратко, 1-3 предложения. Не используй Markdown. Если вопрос про дату "
        "или время, используй текущее server time из prompt."
    ),
    "en": (
        "You are the Task Learn voice assistant. Answer in English, naturally "
        "and concisely, in 1-3 sentences. Do not use Markdown. If the user asks "
        "about date or time, use the current server time from the prompt."
    ),
}


@dataclass(frozen=True, slots=True)
class VoiceAssistantResult:
    transcript: str
    response_text: str
    intent: str
    language: str
    stt_model: str
    stt_provider: str
    llm_model: str
    llm_provider: str = "openrouter"
    tts_audio_base64: str = ""
    tts_mime_type: str = ""
    tts_model: str = ""
    tts_provider: str = "huggingface"


def create_voice_assistant_result(
    audio_body: bytes,
    *,
    mime_type: str,
    language: str,
    speech_client,
    llm_client,
    tts_client,
    now: datetime | None = None,
) -> VoiceAssistantResult:
    """Строит полный voice response: ASR -> intent -> LLM -> TTS."""
    clean_language = require_voice_language(language)
    transcription = speech_client.transcribe(audio_body, mime_type=mime_type)
    transcript = require_transcript_text(transcription.text)
    intent = classify_voice_intent(transcript)
    response_text = generate_voice_llm_response(
        transcript,
        intent=intent.name,
        language=clean_language,
        llm_client=llm_client,
        now=now,
    )
    speech = tts_client.synthesize(response_text, language=clean_language)
    return VoiceAssistantResult(
        transcript=transcript,
        response_text=response_text,
        intent=intent.name,
        language=clean_language,
        stt_model=transcription.model,
        stt_provider=transcription.provider,
        llm_model=llm_client.model,
        tts_audio_base64=speech.audio_base64,
        tts_mime_type=speech.mime_type,
        tts_model=speech.model,
        tts_provider=speech.provider,
    )


def require_voice_language(language: str) -> str:
    clean_language = language.strip().lower()
    if clean_language not in SUPPORTED_VOICE_LANGUAGES:
        allowed = ", ".join(sorted(SUPPORTED_VOICE_LANGUAGES))
        raise ValueError(f"language must be one of: {allowed}")
    return clean_language


def require_transcript_text(transcript: str) -> str:
    clean_transcript = transcript.strip()
    if not clean_transcript:
        raise ValueError("transcript must be non-empty")
    if len(clean_transcript) > 8_000:
        raise ValueError("transcript must be at most 8000 characters")
    return clean_transcript


def generate_voice_llm_response(
    transcript: str,
    *,
    intent: str,
    language: str,
    llm_client,
    now: datetime | None = None,
) -> str:
    server_time = (now or datetime.now().astimezone()).isoformat(timespec="seconds")
    prompt = (
        f"Current server time: {server_time}\n"
        f"Detected command intent: {intent}\n"
        f"User voice transcript: {transcript}"
    )
    response_text = llm_client.generate(
        prompt,
        system=VOICE_SYSTEM_PROMPTS[language],
        options={"temperature": 0.4, "max_tokens": 180},
    ).strip()
    if not response_text:
        raise OpenRouterError("OpenRouter returned an empty voice response")
    return response_text
