from __future__ import annotations

import hashlib
import json
import re
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "deliverables/alpenglow_assist_finetuning"
DATASET_PATH = OUT / "alpenglow_assist_training_dataset.jsonl"
SETUP_PATH = OUT / "fine_tuning_setup.json"
REPORT_PATH = OUT / "training_evaluation_report.pdf"
DEPLOY_PATH = OUT / "deployment_package.json"
STATUS = "blocked_pending_model_provider_decision"
TOPICS = {"onboarding", "troubleshooting", "account_access", "billing_basics", "workflow_how_to", "safe_escalation"}
FIELDS = {
    "conversation_id",
    "topic",
    "intent",
    "user_message",
    "assistant_response",
    "escalation_flag",
    "difficulty",
    "tone",
    "source_notes",
    "split",
}


def read_jsonl() -> list[dict[str, object]]:
    return [json.loads(line) for line in DATASET_PATH.read_text(encoding="utf-8").splitlines()]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def norm(value: object) -> str:
    return re.sub(r"\s+", " ", str(value).lower()).strip()


class AlpenglowAssistFinetuningTests(unittest.TestCase):
    def setUp(self) -> None:
        self.records = read_jsonl()
        self.setup = json.loads(SETUP_PATH.read_text(encoding="utf-8"))
        self.deployment = json.loads(DEPLOY_PATH.read_text(encoding="utf-8"))

    def test_required_upload_files_exist_and_blocked_status_is_truthful(self) -> None:
        for path in [DATASET_PATH, SETUP_PATH, REPORT_PATH, DEPLOY_PATH]:
            self.assertTrue(path.exists(), path)

        pdf = REPORT_PATH.read_bytes()
        self.assertTrue(pdf.startswith(b"%PDF-"))
        self.assertIn(b"Alpenglow Assist Training Evaluation Report", pdf)
        self.assertIn(STATUS.encode("ascii"), pdf)
        self.assertEqual(self.setup["training_status"], STATUS)
        self.assertEqual(self.deployment["training_status"], STATUS)
        self.assertIsNone(self.deployment["selected_checkpoint"])

    def test_jsonl_schema_vocab_and_synthetic_safety(self) -> None:
        raw_text = DATASET_PATH.read_text(encoding="utf-8")

        self.assertEqual(len(self.records), 108)
        self.assertFalse(re.search(r"[\w.+-]+@[\w.-]+", raw_text))
        self.assertFalse(re.search(r"\b\d{3}[-.]\d{3}[-.]\d{4}\b", raw_text))
        for forbidden in ["HF_TOKEN", "OPENROUTER_API_KEY", "Authorization", "sk-", "hf_"]:
            self.assertNotIn(forbidden, raw_text)

        for index, row in enumerate(self.records, start=1):
            self.assertEqual(set(row), FIELDS)
            self.assertEqual(row["conversation_id"], f"AA-{index:04d}")
            self.assertIn(row["topic"], TOPICS)
            self.assertIn(row["difficulty"], {"easy", "medium"})
            self.assertEqual(row["tone"], "concise_support")
            self.assertEqual(row["source_notes"], "synthetic_clean_example")
            self.assertIn(row["split"], {"train", "validation"})
            self.assertTrue(row["user_message"])
            self.assertTrue(row["assistant_response"])

    def test_topic_balance_validation_split_and_duplicate_integrity(self) -> None:
        topic_counts = Counter(row["topic"] for row in self.records)
        split_counts = Counter(row["split"] for row in self.records)
        normalized_users = [norm(row["user_message"]) for row in self.records]
        normalized_pairs = [(norm(row["user_message"]), norm(row["assistant_response"])) for row in self.records]

        self.assertEqual(set(topic_counts), TOPICS)
        self.assertTrue(all(count == 18 for count in topic_counts.values()))
        self.assertEqual(split_counts, {"train": 96, "validation": 12})
        for topic in TOPICS:
            topic_rows = [row for row in self.records if row["topic"] == topic]
            self.assertEqual(Counter(row["split"] for row in topic_rows), {"train": 16, "validation": 2})
        self.assertEqual(len(normalized_users), len(set(normalized_users)))
        self.assertEqual(len(normalized_pairs), len(set(normalized_pairs)))

    def test_escalation_coverage_and_cleaning_summary(self) -> None:
        escalation_rows = [row for row in self.records if row["escalation_flag"]]
        summary = self.setup["candidate_cleaning_summary"]
        reasons = summary["exclusion_reason_counts"]

        self.assertGreaterEqual(len(escalation_rows), 20)
        self.assertTrue(all("handoff" in norm(row["assistant_response"]) or "security" in norm(row["assistant_response"]) for row in escalation_rows))
        self.assertEqual(summary["candidate_count"], 120)
        self.assertEqual(summary["retained_count"], 108)
        self.assertEqual(summary["excluded_count"], 12)
        self.assertFalse(summary["duplicate_cross_split_leakage"])
        for reason in [
            "exact_duplicate",
            "near_duplicate",
            "contradictory_answer",
            "off_brand_tone",
            "incomplete_response",
            "mislabeled_topic",
            "unsafe_overly_technical_response",
            "direct_answer_to_escalation_case",
        ]:
            self.assertIn(reason, reasons)

    def test_setup_and_deployment_metadata(self) -> None:
        integrity = self.setup["dataset_integrity"]

        self.assertEqual(self.setup["base_model"], "pending_human_decision")
        self.assertEqual(self.setup["training_provider_runtime"], "pending_human_decision")
        self.assertEqual(integrity["jsonl_record_count"], len(self.records))
        self.assertEqual(integrity["record_count_source"], "one JSON object per JSONL line")
        self.assertIn("previews only", integrity["review_note"])
        self.assertEqual(self.setup["validation_split"]["seed"], 17017)
        self.assertEqual(len(self.setup["evaluation_prompt_set_references"]), 6)
        self.assertEqual(self.deployment["model_version"], "alpenglow-assist-v1.0.0")
        self.assertEqual(self.deployment["dataset"]["sha256"], digest(DATASET_PATH))
        self.assertEqual(self.deployment["fine_tuning_setup"]["sha256"], digest(SETUP_PATH))
        self.assertEqual(self.deployment["evaluation_report"]["sha256"], digest(REPORT_PATH))
        self.assertEqual(self.deployment["integration_readiness_status"], "not_ready_for_support_workflow_integration")


if __name__ == "__main__":
    unittest.main()
