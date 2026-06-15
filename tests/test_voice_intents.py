from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from llm.voice_intents import classify_voice_intent


class VoiceIntentTests(unittest.TestCase):
    def test_classifies_greeting(self) -> None:
        self.assertEqual(classify_voice_intent("Привет, кто ты?").name, "greeting")

    def test_classifies_datetime(self) -> None:
        self.assertEqual(classify_voice_intent("Сколько времени").name, "datetime")

    def test_classifies_joke(self) -> None:
        self.assertEqual(classify_voice_intent("Tell a joke").name, "joke")

    def test_classifies_general_request(self) -> None:
        self.assertEqual(classify_voice_intent("Explain FastAPI").name, "general")


if __name__ == "__main__":
    unittest.main()
