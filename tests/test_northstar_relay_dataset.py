from __future__ import annotations

import csv
import json
import re
import unittest
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data/northstar_relay_support_records.csv"
JSONL_PATH = ROOT / "data/northstar_relay_standardized_conversations.jsonl"
AUDIT_PATH = ROOT / "data/northstar_relay_dataset_audit.json"
DELIVERABLE_DIR = ROOT / "deliverables/northstar_relay_finetuning"
VALIDATED_JSONL_PATH = DELIVERABLE_DIR / "validated_finetuning_dataset.jsonl"
QUALITY_REPORT_PATH = DELIVERABLE_DIR / "dataset_quality_report.pdf"

RAW_HEADER = [
    "record_id",
    "channel",
    "customer_message",
    "agent_response",
    "resolution_summary",
    "created_at",
    "resolved_at",
    "product_area",
    "issue_category",
    "raw_text",
    "audit_status",
    "exclusion_reason",
    "duplicate_group_id",
    "anomaly_flags",
]


def read_rows() -> tuple[list[str], list[dict[str, str]]]:
    with RAW_PATH.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def read_jsonl() -> list[dict[str, object]]:
    return [json.loads(line) for line in JSONL_PATH.read_text(encoding="utf-8").splitlines()]


def valid_timestamp(value: str) -> bool:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


class NorthstarRelayDatasetTests(unittest.TestCase):
    def setUp(self) -> None:
        self.header, self.rows = read_rows()
        self.conversations = read_jsonl()
        self.audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))

    def test_raw_csv_schema_counts_and_synthetic_safety(self) -> None:
        raw_text = RAW_PATH.read_text(encoding="utf-8")
        statuses = {row["audit_status"] for row in self.rows}

        self.assertEqual(self.header, RAW_HEADER)
        self.assertGreaterEqual(len(self.rows), 150)
        self.assertEqual(len({row["record_id"] for row in self.rows}), len(self.rows))
        self.assertEqual(statuses, {"keep", "review", "remove"})
        self.assertFalse(re.search(r"[\w.+-]+@[\w.-]+", raw_text))
        self.assertNotIn("HF_TOKEN", raw_text)
        self.assertNotIn("Authorization", raw_text)
        self.assertNotIn("sk-", raw_text)
        self.assertNotIn("hf_", raw_text)

    def test_source_records_cover_required_channels_and_edge_cases(self) -> None:
        channels = {row["channel"] for row in self.rows}
        reasons = {row["exclusion_reason"] for row in self.rows}
        flags = "|".join(row["anomaly_flags"] for row in self.rows)
        categories = {row["issue_category"] for row in self.rows}

        self.assertTrue({"chat", "email", "internal_note", "mixed"}.issubset(channels))
        self.assertTrue({"billing_question", "technical_troubleshooting", "escalation"}.issubset(categories))
        for reason in [
            "near_duplicate",
            "off_topic_content",
            "missing_customer_context",
            "missing_resolution_context",
            "truncated_message",
            "malformed_timestamp",
            "ambiguous_customer_goal",
            "billing_action_requires_human",
        ]:
            self.assertIn(reason, reasons)
        self.assertIn("unsupported", flags)
        self.assertIn("needs_human_review", flags)

    def test_standardized_jsonl_contains_only_retained_conversations(self) -> None:
        keep_ids = {row["record_id"] for row in self.rows if row["audit_status"] == "keep"}
        non_keep_ids = {row["record_id"] for row in self.rows if row["audit_status"] != "keep"}
        conversation_ids = {str(item["record_id"]) for item in self.conversations}

        self.assertEqual(conversation_ids, keep_ids)
        self.assertFalse(conversation_ids & non_keep_ids)
        for item in self.conversations:
            self.assertEqual(
                set(item),
                {
                    "record_id",
                    "source_channel",
                    "product_area",
                    "issue_category",
                    "messages",
                    "resolution",
                    "quality_flags",
                },
            )
            self.assertEqual([message["role"] for message in item["messages"]], ["user", "assistant"])
            self.assertTrue(all(message["content"] for message in item["messages"]))
            self.assertTrue(item["resolution"])

    def test_audit_counts_inventory_and_vocabularies_match_source_data(self) -> None:
        status_counts = Counter(row["audit_status"] for row in self.rows)
        channel_counts = Counter(row["channel"] for row in self.rows)

        self.assertEqual(self.audit["source_record_count"], len(self.rows))
        self.assertEqual(self.audit["standardized_record_count"], len(self.conversations))
        self.assertEqual(self.audit["status_counts"], dict(status_counts))
        self.assertEqual(self.audit["channel_counts"], dict(channel_counts))
        for status in ["keep", "review", "remove"]:
            self.assertEqual(len(self.audit["inventory"][status]), status_counts[status])
        self.assertTrue({row["product_area"] for row in self.rows} <= set(self.audit["product_area_vocabulary"]))
        self.assertTrue({row["issue_category"] for row in self.rows} <= set(self.audit["issue_category_vocabulary"]))

    def test_duplicate_groups_do_not_leak_multiple_retained_records(self) -> None:
        grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in self.rows:
            if row["duplicate_group_id"]:
                grouped[row["duplicate_group_id"]].append(row)

        self.assertGreaterEqual(len(grouped), 2)
        self.assertEqual(len(self.audit["duplicate_groups"]), len(grouped))
        for group_id, rows in grouped.items():
            kept = [row for row in rows if row["audit_status"] == "keep"]
            self.assertLessEqual(len(kept), 1, group_id)
            self.assertTrue(any(row["audit_status"] != "keep" for row in rows))

    def test_validation_report_covers_structure_and_semantic_suitability(self) -> None:
        report = self.audit["validation_report"]
        malformed = [row for row in self.rows if not valid_timestamp(row["created_at"]) or not valid_timestamp(row["resolved_at"])]
        blocked_reasons = ("off_topic", "unsupported", "spam", "external_product", "custom_code")

        self.assertEqual(report["failed_count"], 0)
        self.assertGreaterEqual(report["passed_count"], 10)
        self.assertTrue(malformed)
        self.assertTrue(all("malformed_timestamp" in row["anomaly_flags"] for row in malformed))
        self.assertTrue(all(row["audit_status"] != "keep" for row in malformed))
        self.assertTrue(
            all(
                row["audit_status"] != "keep"
                for row in self.rows
                if any(reason in row["exclusion_reason"] for reason in blocked_reasons)
            )
        )

    def test_upload_deliverables_exist_with_expected_names(self) -> None:
        pdf_bytes = QUALITY_REPORT_PATH.read_bytes()

        self.assertEqual(VALIDATED_JSONL_PATH.read_text(encoding="utf-8"), JSONL_PATH.read_text(encoding="utf-8"))
        self.assertTrue(pdf_bytes.startswith(b"%PDF-"))
        self.assertIn(b"Northstar Relay Dataset Quality Report", pdf_bytes)
        self.assertIn(b"Final readiness status", pdf_bytes)


if __name__ == "__main__":
    unittest.main()
