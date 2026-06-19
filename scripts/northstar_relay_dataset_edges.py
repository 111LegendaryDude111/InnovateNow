from __future__ import annotations

from northstar_relay_dataset_contract import (
    CHANNELS,
    ISSUE_CATEGORIES,
    KEEP_TEMPLATES,
    PRODUCT_AREAS,
)


EDGE_CASES = [
    ("review", "near_duplicate", "DUP-ROUTE-001", ["near_duplicate"]),
    ("remove", "exact_duplicate", "DUP-ROUTE-001", ["exact_duplicate"]),
    ("review", "near_duplicate", "DUP-BILL-001", ["near_duplicate"]),
    ("remove", "exact_duplicate", "DUP-BILL-001", ["exact_duplicate"]),
    ("review", "missing_customer_context", "", ["missing_customer_context"]),
    ("review", "missing_resolution_context", "", ["missing_resolution_context"]),
    ("review", "truncated_message", "", ["truncated"]),
    ("review", "malformed_timestamp", "", ["malformed_timestamp"]),
    ("review", "ambiguous_customer_goal", "", ["ambiguous"]),
    ("review", "escalation_required", "", ["needs_human_review"]),
    ("review", "internal_note_only", "", ["missing_customer_context"]),
    ("review", "partial_mixed_format", "", ["missing_resolution_context"]),
    ("review", "malformed_timestamp", "", ["malformed_timestamp"]),
    ("review", "ambiguous_product_area", "", ["ambiguous"]),
    ("review", "billing_action_requires_human", "", ["needs_human_review"]),
    ("remove", "off_topic_content", "", ["unsupported"]),
    ("remove", "spam_or_test_record", "", ["unsupported"]),
    ("remove", "no_support_response", "", ["missing_response"]),
    ("remove", "unsupported_legal_request", "", ["unsupported"]),
    ("remove", "empty_transcript", "", ["missing_customer_context"]),
    ("remove", "customer_only_thread", "", ["missing_response"]),
    ("remove", "assistant_only_note", "", ["missing_customer_context"]),
    ("remove", "external_product_request", "", ["unsupported"]),
    ("remove", "training_unsuitable_rant", "", ["unsupported"]),
    ("remove", "malformed_without_context", "", ["malformed_timestamp", "missing_response"]),
    ("remove", "off_topic_content", "", ["unsupported"]),
    ("remove", "no_customer_problem", "", ["missing_customer_context"]),
    ("remove", "unsupported_custom_code", "", ["unsupported"]),
    ("remove", "duplicate_without_resolution", "DUP-BILL-001", ["exact_duplicate", "missing_response"]),
    ("review", "ambiguous_escalation", "", ["ambiguous", "needs_human_review"]),
    ("review", "truncated_message", "", ["truncated"]),
    ("review", "missing_resolution_context", "", ["missing_resolution_context"]),
]


def edge_template(index: int, status: str, reason: str, duplicate_group_id: str) -> tuple[str, str, str, str, str]:
    if "off_topic" in reason:
        return ("workspace_settings", "configuration", "Can you suggest lunch ideas for the team?", "", "")
    if "duplicate" in reason:
        base = KEEP_TEMPLATES[0 if duplicate_group_id == "DUP-ROUTE-001" else 2]
        if reason == "near_duplicate":
            return (
                base[0],
                base[1],
                base[2].replace("still land", "still keep landing").replace("shows", "still shows"),
                base[3],
                base[4],
            )
        return base
    if "missing_customer" in reason or "assistant_only" in reason:
        return ("reporting", "how_to", "", "The report filter was updated.", "")
    if "missing_response" in reason or "customer_only" in reason:
        return ("integrations", "technical_troubleshooting", "The integration is failing again.", "", "")
    if "truncated" in reason:
        return ("mobile_app", "technical_troubleshooting", "Notifications stopped after...", "Please check mobile settings, then", "")
    if "legal" in reason:
        return ("billing", "billing_question", "Can Relay tell me if this contract is legally enforceable?", "", "")
    if "custom_code" in reason:
        return ("integrations", "how_to", "Write a custom scraper for another vendor portal.", "", "")
    if "spam" in reason or "empty" in reason:
        return ("workspace_settings", "configuration", "", "", "")
    if "billing_action" in reason:
        return ("billing", "escalation", "Please refund the last invoice today.", "A billing specialist must verify the request.", "")
    if "escalation" in reason:
        return ("user_management", "escalation", "A former employee still appears in our workspace.", "I will escalate this to account security for review.", "")
    if "ambiguous" in reason:
        return ("inbox_routing", "configuration", "Relay is not doing the thing from yesterday.", "Can you share which workflow or inbox this concerns?", "")
    return (
        PRODUCT_AREAS[index % len(PRODUCT_AREAS)],
        ISSUE_CATEGORIES[index % len(ISSUE_CATEGORIES)],
        "Northstar Relay did not behave as expected.",
        "" if status == "remove" else "Please share the affected workflow and timestamp so support can verify.",
        "",
    )


def iter_edge_cases():
    for index, (status, reason, duplicate_group_id, flags) in enumerate(EDGE_CASES):
        yield {
            "index": index,
            "channel": CHANNELS[index % len(CHANNELS)],
            "status": status,
            "reason": reason,
            "duplicate_group_id": duplicate_group_id,
            "flags": flags,
            "template": edge_template(index, status, reason, duplicate_group_id),
        }
