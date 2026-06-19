from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime

from northstar_relay_dataset_contract import (
    ISSUE_CATEGORIES,
    PRODUCT_AREAS,
    RAW_COLUMNS,
)


def build_audit(rows: list[dict[str, str]], conversations: list[dict[str, object]]) -> dict[str, object]:
    duplicate_groups = summarize_duplicates(rows)
    return {
        "schema_version": "2026-06-19",
        "dataset": "northstar_relay_support_responses",
        "source_record_count": len(rows),
        "standardized_record_count": len(conversations),
        "status_counts": dict(Counter(row["audit_status"] for row in rows)),
        "channel_counts": dict(Counter(row["channel"] for row in rows)),
        "product_area_vocabulary": PRODUCT_AREAS,
        "issue_category_vocabulary": ISSUE_CATEGORIES,
        "exclusion_reason_counts": dict(Counter(row["exclusion_reason"] for row in rows if row["exclusion_reason"])),
        "inventory": {status: inventory(rows, status) for status in ["keep", "review", "remove"]},
        "duplicate_groups": duplicate_groups,
        "validation_report": validation_report(rows, conversations, duplicate_groups),
    }


def inventory(rows: list[dict[str, str]], status: str) -> list[dict[str, str]]:
    fields = ["record_id", "channel", "product_area", "issue_category", "exclusion_reason", "duplicate_group_id"]
    return [{field: row[field] for field in fields} for row in rows if row["audit_status"] == status]


def summarize_duplicates(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        if row["duplicate_group_id"]:
            groups[row["duplicate_group_id"]].append(row)
    return [
        {
            "duplicate_group_id": group_id,
            "record_ids": [row["record_id"] for row in group],
            "kept_record_id": next((row["record_id"] for row in group if row["audit_status"] == "keep"), None),
            "statuses": dict(Counter(row["audit_status"] for row in group)),
            "reason": "Only one representative conversation is retained for training.",
        }
        for group_id, group in sorted(groups.items())
    ]


def validation_report(
    rows: list[dict[str, str]],
    conversations: list[dict[str, object]],
    duplicate_groups: list[dict[str, object]],
) -> dict[str, object]:
    keep_rows = [row for row in rows if row["audit_status"] == "keep"]
    keep_ids = {row["record_id"] for row in keep_rows}
    conversation_ids = {str(conversation["record_id"]) for conversation in conversations}
    duplicate_keep_counts = Counter(
        row["duplicate_group_id"] for row in rows if row["duplicate_group_id"] and row["audit_status"] == "keep"
    )
    checks = [
        ("raw_schema", set(rows[0]) == set(RAW_COLUMNS), "failed"),
        ("minimum_source_records", len(rows) >= 150, "failed"),
        ("unique_record_ids", len({row["record_id"] for row in rows}) == len(rows), "failed"),
        ("valid_audit_statuses", {row["audit_status"] for row in rows} <= {"keep", "review", "remove"}, "failed"),
        ("keep_records_have_training_text", all(row["customer_message"] and row["agent_response"] and row["resolution_summary"] for row in keep_rows), "failed"),
        ("standardized_records_json_serializable", all(is_jsonable(conversation) for conversation in conversations), "failed"),
        ("standardized_messages_present", all(has_messages(conversation) for conversation in conversations), "failed"),
        ("jsonl_only_keep_records", conversation_ids == keep_ids, "failed"),
        ("duplicate_leakage_absent", all(count <= 1 for count in duplicate_keep_counts.values()), "failed"),
        ("malformed_timestamps_flagged", malformed_timestamps_are_flagged(rows), "failed"),
        ("documented_vocabularies_used", vocabulary_values_are_valid(rows), "failed"),
        ("unsupported_or_off_topic_excluded", unsupported_rows_not_kept(rows), "failed"),
        ("duplicate_groups_reported", bool(duplicate_groups), "warning"),
        ("review_records_present", any(row["audit_status"] == "review" for row in rows), "warning"),
        ("remove_records_present", any(row["audit_status"] == "remove" for row in rows), "warning"),
    ]
    failed = [name for name, ok, severity in checks if not ok and severity == "failed"]
    warnings = [name for name, ok, severity in checks if ok and severity == "warning"]
    return {
        "passed_count": sum(1 for _, ok, severity in checks if ok and severity == "failed"),
        "failed_count": len(failed),
        "warning_count": len(warnings),
        "failed_checks": failed,
        "warning_checks": warnings,
    }


def is_jsonable(value: dict[str, object]) -> bool:
    try:
        json.dumps(value)
    except TypeError:
        return False
    return True


def has_messages(conversation: dict[str, object]) -> bool:
    messages = conversation.get("messages")
    if not isinstance(messages, list) or len(messages) < 2:
        return False
    roles = [message.get("role") for message in messages if isinstance(message, dict)]
    contents = [message.get("content") for message in messages if isinstance(message, dict)]
    return roles == ["user", "assistant"] and all(isinstance(content, str) and content for content in contents)


def malformed_timestamps_are_flagged(rows: list[dict[str, str]]) -> bool:
    malformed = [row for row in rows if not valid_timestamp(row["created_at"]) or not valid_timestamp(row["resolved_at"])]
    return bool(malformed) and all("malformed_timestamp" in row["anomaly_flags"] and row["audit_status"] != "keep" for row in malformed)


def valid_timestamp(value: str) -> bool:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def vocabulary_values_are_valid(rows: list[dict[str, str]]) -> bool:
    return all(row["product_area"] in PRODUCT_AREAS and row["issue_category"] in ISSUE_CATEGORIES for row in rows)


def unsupported_rows_not_kept(rows: list[dict[str, str]]) -> bool:
    blocked_terms = ("off_topic", "unsupported", "spam", "external_product", "custom_code")
    return all(
        row["audit_status"] != "keep"
        for row in rows
        if any(term in row["exclusion_reason"] for term in blocked_terms) or "unsupported" in row["anomaly_flags"]
    )
