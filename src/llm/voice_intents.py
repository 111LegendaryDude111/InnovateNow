from __future__ import annotations

from dataclasses import dataclass
import re

VOICE_INTENTS = {"greeting", "datetime", "joke", "general"}
INTENT_PATTERNS = {
    "greeting": (
        "привет",
        "здравствуй",
        "здравствуйте",
        "добрый день",
        "кто ты",
        "как тебя зовут",
        "hello",
        "hi",
        "hey",
        "who are you",
        "what is your name",
    ),
    "datetime": (
        "сколько времени",
        "который час",
        "какая дата",
        "какое сегодня число",
        "дата",
        "время",
        "what time",
        "date",
        "today",
        "day is it",
    ),
    "joke": (
        "шутка",
        "пошути",
        "расскажи шутку",
        "анекдот",
        "joke",
        "tell a joke",
        "make me laugh",
    ),
}


@dataclass(frozen=True, slots=True)
class VoiceIntent:
    name: str
    normalized_text: str


def classify_voice_intent(transcript: str) -> VoiceIntent:
    """Определяет базовый тип voice command до обращения к LLM."""
    normalized = normalize_transcript(transcript)
    for intent, patterns in INTENT_PATTERNS.items():
        if any(pattern in normalized for pattern in patterns):
            return VoiceIntent(name=intent, normalized_text=normalized)
    return VoiceIntent(name="general", normalized_text=normalized)


def normalize_transcript(transcript: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]+", " ", transcript.lower())).strip()
