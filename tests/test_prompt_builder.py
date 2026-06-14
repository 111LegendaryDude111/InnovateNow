from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from llm.prompt_builder import build_content_prompt


class PromptBuilderTests(unittest.TestCase):
    def test_build_content_prompt_combines_topic_and_content_type(self) -> None:
        prompt = build_content_prompt("LLM clients", "checklist")

        self.assertEqual(
            prompt,
            (
                "You are a content generation assistant.\n"
                "Topic: LLM clients\n"
                "Content type: checklist\n"
                "Write the requested content in a clear, structured, and useful way."
            ),
        )

    def test_build_content_prompt_rejects_blank_topic(self) -> None:
        with self.assertRaisesRegex(ValueError, "topic"):
            build_content_prompt(" ", "summary")


if __name__ == "__main__":
    unittest.main()
