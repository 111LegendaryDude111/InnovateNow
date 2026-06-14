from __future__ import annotations

import sys
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import main as app_main


class FakeClient:
    model = "deepseek/deepseek-v4-flash"
    base_url = "https://openrouter.ai/api/v1"
    api_base_url = "https://openrouter.ai/api/v1"
    port = 443
    has_api_key = True

    def generate(self, prompt: str, *, system: str | None = None) -> str:
        return f"{prompt}::{system}"

    def model_available(self) -> bool:
        return True


class MainTests(unittest.TestCase):
    def test_ask_builds_prompt_from_topic_and_content_type(self) -> None:
        with (
            patch("main.load_env_file"),
            patch("main.OpenRouterClient.from_env", return_value=FakeClient()),
        ):
            stdout = StringIO()
            with redirect_stdout(stdout):
                exit_code = app_main.main(
                    [
                        "ask",
                        "--topic",
                        "Python testing",
                        "--content-type",
                        "tutorial",
                        "--system",
                        "short",
                    ],
                )

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            stdout.getvalue(),
            (
                "You are a content generation assistant.\n"
                "Topic: Python testing\n"
                "Content type: tutorial\n"
                "Write the requested content in a clear, structured, and useful way."
                "::short\n"
            ),
        )

    def test_status_prints_openrouter_config(self) -> None:
        with (
            patch("main.load_env_file"),
            patch("main.OpenRouterClient.from_env", return_value=FakeClient()),
        ):
            stdout = StringIO()
            with redirect_stdout(stdout):
                exit_code = app_main.main(["status"])

        self.assertEqual(exit_code, 0)
        self.assertIn("Provider: OpenRouter", stdout.getvalue())
        self.assertIn("Port: 443", stdout.getvalue())
        self.assertIn("Model status: available", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
