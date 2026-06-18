from __future__ import annotations

import sys
import unittest
from pathlib import Path

from fastapi import HTTPException
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from llm.api import app
from llm.haven_support_api import (
    HavenSupportRequest,
    create_haven_support_response,
)
from llm.haven_support_bot import HavenSupportBot, load_haven_support_config


class HavenSupportBotTests(unittest.TestCase):
    def setUp(self) -> None:
        self.bot = HavenSupportBot()

    def test_config_contains_scope_and_kb_contract(self) -> None:
        config = load_haven_support_config()

        self.assertGreaterEqual(len(config["supported_requests"]), 4)
        self.assertGreaterEqual(len(config["unsupported_requests"]), 3)
        self.assertGreaterEqual(len(config["boundary_rules"]), 5)
        self.assertIn("Haven Cam", {item["term"] for item in config["canonical_terms"]})

    def test_device_setup_returns_supported_answer_with_source(self) -> None:
        output = self.bot.respond("How do I pair and install a new Haven Cam?")

        self.assertEqual(output.intent, "device_setup")
        self.assertEqual(output.action, "answer")
        self.assertIn("Add device", output.answer)
        self.assertEqual(output.sources[0].source_id, "device_setup")

    def test_account_access_escalates_with_handoff_payload(self) -> None:
        output = self.bot.respond("I can't log in and need a password reset")

        self.assertEqual(output.intent, "account_access")
        self.assertEqual(output.action, "escalate")
        self.assertIsNotNone(output.handoff)
        self.assertEqual(output.handoff.status, "needs_human")
        self.assertIn("identity", output.handoff.reason.lower())

    def test_safety_request_escalates_before_supported_keywords(self) -> None:
        output = self.bot.respond("My Haven alarm says break in, dispatch police now")

        self.assertEqual(output.intent, "safety_sensitive")
        self.assertEqual(output.action, "escalate")
        self.assertIn("emergency services", output.handoff.next_step.lower())

    def test_non_haven_request_is_refused(self) -> None:
        output = self.bot.respond("Can you configure my Ring camera?")

        self.assertEqual(output.intent, "non_haven_product")
        self.assertEqual(output.action, "refuse")
        self.assertFalse(output.sources)

    def test_unknown_request_uses_clarifying_fallback(self) -> None:
        output = self.bot.respond("Can you recommend a movie tonight?")

        self.assertEqual(output.intent, "unrelated_request")
        self.assertEqual(output.action, "refuse")

        unknown = self.bot.respond("Tell me something interesting")
        self.assertEqual(unknown.intent, "unknown")
        self.assertEqual(unknown.action, "clarify")

    def test_api_response_maps_runtime_payload(self) -> None:
        response = create_haven_support_response(
            HavenSupportRequest(message="What is included in Haven Secure?", channel="in_app"),
            bot=self.bot,
        )

        self.assertEqual(response.intent, "monitoring_plans")
        self.assertEqual(response.channel, "in_app")
        self.assertEqual(response.sources[0].intent, "monitoring_plans")

    def test_invalid_request_returns_http_error(self) -> None:
        with self.assertRaises(HTTPException) as raised:
            create_haven_support_response(
                HavenSupportRequest(message="   ", channel="help_center"),
                bot=self.bot,
            )

        self.assertEqual(raised.exception.status_code, 400)
        self.assertEqual(raised.exception.detail, "message must be a non-empty string")

    def test_app_registers_haven_support_endpoint(self) -> None:
        client = TestClient(app)

        response = client.post(
            "/support/haven/respond",
            json={"message": "My sensor is offline", "channel": "help_center"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["intent"], "basic_troubleshooting")


if __name__ == "__main__":
    unittest.main()
