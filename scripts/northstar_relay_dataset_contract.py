from __future__ import annotations


RAW_COLUMNS = [
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

PRODUCT_AREAS = [
    "inbox_routing",
    "automations",
    "billing",
    "integrations",
    "reporting",
    "mobile_app",
    "user_management",
    "workspace_settings",
]

ISSUE_CATEGORIES = [
    "technical_troubleshooting",
    "how_to",
    "billing_question",
    "account_access",
    "configuration",
    "escalation",
]

CHANNELS = ["chat", "email", "internal_note", "mixed"]

BUSINESSES = [
    "bakery",
    "clinic",
    "repair shop",
    "design studio",
    "pet groomer",
    "bookstore",
    "coffee bar",
    "bike shop",
    "florist",
    "tax office",
    "dance school",
    "catering team",
]

KEEP_TEMPLATES = [
    (
        "inbox_routing",
        "technical_troubleshooting",
        "Messages tagged {tag} for our {business} still land in Unassigned after we changed the routing rule.",
        "Open Routing rules, move the {tag} rule above the catch-all rule, then run the preview against the last five messages before saving.",
        "Rule order corrected; future {tag} messages route to the expected team.",
    ),
    (
        "automations",
        "configuration",
        "We need after-hours web leads for the {business} to create a manager task and send an SMS summary.",
        "Create an automation with the after-hours schedule, add the task action first, then add the SMS summary action with the lead name and source fields.",
        "After-hours automation configured with task creation and SMS summary.",
    ),
    (
        "billing",
        "billing_question",
        "The invoice receipt for our {business} shows the old billing contact name.",
        "Update the billing contact in Workspace billing, then regenerate the receipt from Billing history so the exported PDF uses the new name.",
        "Billing contact updated and receipt regenerated from billing history.",
    ),
    (
        "integrations",
        "technical_troubleshooting",
        "Shopfront orders are not creating Relay tasks for the {business} since yesterday.",
        "Reconnect the Shopfront integration, confirm task creation is enabled, and replay the failed order event from Integration logs.",
        "Integration reconnected and failed order event replayed.",
    ),
    (
        "reporting",
        "how_to",
        "The weekly response report for the {business} is missing closed chat conversations.",
        "Edit the report filter, include chat as a source, and set conversation status to closed plus resolved so the export matches support totals.",
        "Report filter updated to include closed chat conversations.",
    ),
    (
        "mobile_app",
        "technical_troubleshooting",
        "Push notifications for our {business} arrive late on Android but desktop alerts are instant.",
        "Check that battery optimization is disabled for Northstar Relay, then refresh the device registration from Mobile settings.",
        "Mobile device registration refreshed after battery optimization check.",
    ),
    (
        "user_management",
        "account_access",
        "A new teammate at the {business} cannot accept the invite after we changed domains.",
        "Cancel the pending invite, send a new invite to the current domain, and ask the teammate to open it in a private browser window.",
        "Invite resent for the current domain and pending stale invite removed.",
    ),
    (
        "workspace_settings",
        "configuration",
        "The {business} workspace shows appointments in the wrong local time.",
        "Set the workspace time zone under Settings, then refresh calendar sync so existing appointment cards display in the local time.",
        "Workspace time zone corrected and calendar sync refreshed.",
    ),
    (
        "inbox_routing",
        "how_to",
        "Can we pin VIP customer messages for the {business} above the regular inbox queue?",
        "Add a VIP tag rule with priority inbox placement, then turn on pinned queue view for the support team.",
        "VIP tag rule added and pinned queue view enabled.",
    ),
    (
        "automations",
        "technical_troubleshooting",
        "Our reminder automation for the {business} sends twice when a customer replies quickly.",
        "Add a condition that skips the reminder if the conversation received a customer reply after the trigger time.",
        "Reminder automation updated with a reply-after-trigger condition.",
    ),
]
