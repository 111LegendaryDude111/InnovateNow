from __future__ import annotations

import csv
import json
from pathlib import Path

from northstar_relay_dataset_audit import build_audit
from northstar_relay_dataset_contract import (
    BUSINESSES,
    CHANNELS,
    KEEP_TEMPLATES,
    RAW_COLUMNS,
)
from northstar_relay_dataset_edges import iter_edge_cases


ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data/northstar_relay_support_records.csv"
JSONL_PATH = ROOT / "data/northstar_relay_standardized_conversations.jsonl"
AUDIT_PATH = ROOT / "data/northstar_relay_dataset_audit.json"


def main() -> None:
    rows = build_rows()
    conversations = [standardize(row) for row in rows if row["audit_status"] == "keep"]
    audit = build_audit(rows, conversations)
    write_csv(rows)
    write_jsonl(conversations)
    AUDIT_PATH.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(rows)} raw records and {len(conversations)} conversations")


def build_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for index, business in enumerate(BUSINESSES):
        for template_index, template in enumerate(KEEP_TEMPLATES):
            channel = CHANNELS[(index + template_index) % len(CHANNELS)]
            add_record(
                rows,
                channel=channel,
                business=business,
                status="keep",
                template=template,
                tag=["billing", "urgent", "wholesale", "callback"][index % 4],
                flags=keep_flags(channel),
            )

    rows[0]["duplicate_group_id"] = "DUP-ROUTE-001"
    rows[12]["duplicate_group_id"] = "DUP-BILL-001"
    for edge in iter_edge_cases():
        duplicate_group = edge["duplicate_group_id"]
        add_record(
            rows,
            channel=edge["channel"],
            business=duplicate_business(duplicate_group) or BUSINESSES[edge["index"] % len(BUSINESSES)],
            status=edge["status"],
            template=edge["template"],
            tag=duplicate_tag(duplicate_group),
            reason=edge["reason"],
            duplicate_group_id=duplicate_group,
            flags=edge["flags"],
            created_at="bad-timestamp" if "malformed_timestamp" in edge["flags"] else None,
        )
    return rows


def add_record(
    rows: list[dict[str, str]],
    *,
    channel: str,
    business: str,
    status: str,
    template: tuple[str, str, str, str, str],
    tag: str = "urgent",
    reason: str = "",
    duplicate_group_id: str = "",
    flags: list[str] | None = None,
    created_at: str | None = None,
) -> None:
    product_area, issue_category, customer, agent, resolution = template
    day = (len(rows) % 28) + 1
    hour = 8 + (len(rows) % 9)
    customer_text = customer.format(business=business, tag=tag)
    agent_text = agent.format(business=business, tag=tag)
    resolution_text = resolution.format(business=business, tag=tag)
    created = created_at or f"2026-05-{day:02d}T{hour:02d}:15:00Z"
    resolved = created_at if created_at else f"2026-05-{day:02d}T{hour + 1:02d}:05:00Z"
    rows.append(
        {
            "record_id": f"NR-{len(rows) + 1:04d}",
            "channel": channel,
            "customer_message": customer_text,
            "agent_response": agent_text,
            "resolution_summary": resolution_text,
            "created_at": created,
            "resolved_at": resolved,
            "product_area": product_area,
            "issue_category": issue_category,
            "raw_text": raw_text(channel, customer_text, agent_text, resolution_text),
            "audit_status": status,
            "exclusion_reason": reason,
            "duplicate_group_id": duplicate_group_id,
            "anomaly_flags": "|".join(flags or []),
        }
    )


def raw_text(channel: str, customer: str, agent: str, resolution: str) -> str:
    if channel == "chat":
        return "\n".join([label("Customer", customer), label("Agent", agent), label("Resolution", resolution)])
    if channel == "email":
        return "\n".join(["Subject: Northstar Relay support", label("Customer wrote", customer), label("Support replied", agent)])
    if channel == "internal_note":
        return f"Case note. {label('Customer problem', customer)} {label('Support response', agent)} {label('Outcome', resolution)}"
    return f"MIXED THREAD :: user={customer} :: assistant={agent} :: outcome={resolution}"


def label(name: str, value: str) -> str:
    return f"{name}: {value}" if value else f"{name}:"


def keep_flags(channel: str) -> list[str]:
    return {"internal_note": ["note_derived"], "mixed": ["mixed_format_source"]}.get(channel, [])


def duplicate_business(group_id: str) -> str:
    return {"DUP-ROUTE-001": "bakery", "DUP-BILL-001": "clinic"}.get(group_id, "")


def duplicate_tag(group_id: str) -> str:
    return {"DUP-ROUTE-001": "billing", "DUP-BILL-001": "urgent"}.get(group_id, "urgent")


def standardize(row: dict[str, str]) -> dict[str, object]:
    return {
        "record_id": row["record_id"],
        "source_channel": row["channel"],
        "product_area": row["product_area"],
        "issue_category": row["issue_category"],
        "messages": [
            {"role": "user", "content": row["customer_message"]},
            {"role": "assistant", "content": row["agent_response"]},
        ],
        "resolution": row["resolution_summary"],
        "quality_flags": [flag for flag in row["anomaly_flags"].split("|") if flag],
    }


def write_csv(rows: list[dict[str, str]]) -> None:
    with RAW_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=RAW_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def write_jsonl(conversations: list[dict[str, object]]) -> None:
    with JSONL_PATH.open("w", encoding="utf-8") as handle:
        for conversation in conversations:
            handle.write(json.dumps(conversation, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
