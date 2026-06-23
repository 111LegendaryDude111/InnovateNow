from __future__ import annotations


SCENARIOS = [
    {"team": "support operations team", "area": "shared inbox", "detail": "weekly launch queue"},
    {"team": "customer success team", "area": "trial workspace", "detail": "new client rollout"},
    {"team": "implementation team", "area": "automation builder", "detail": "approval workflow"},
    {"team": "revenue operations team", "area": "billing center", "detail": "seat review"},
    {"team": "technical support team", "area": "incident queue", "detail": "priority routing"},
    {"team": "field services team", "area": "mobile workspace", "detail": "morning dispatch"},
]

TOPIC_SPECS = {
    "onboarding": [
        ("first_workspace_setup", "How do we set up Alpenglow Assist for our {team}?", "Create the workspace, add the {team}, then connect the {area}. Start with one {detail} before inviting the wider group.", False),
        ("invite_teammates", "What is the cleanest way to invite our {team} without confusing roles?", "Invite admins first, assign roles before sending user invites, and ask each teammate to accept from the same browser they use for work.", False),
        ("import_existing_cases", "Can we bring existing support cases into Alpenglow Assist during {detail}?", "Yes. Export cases as CSV, map requester, subject, status, and owner, then run a small import preview before the full import.", False),
    ],
    "troubleshooting": [
        ("delayed_notifications", "Notifications for our {area} are delayed during {detail}.", "Check notification rules, confirm the channel is enabled, and review recent delivery errors. If delays continue, share the affected timestamps with support.", False),
        ("automation_not_triggering", "Our automation builder did not trigger for the {team}.", "Open the automation run history, confirm the entry conditions match the case, then test with one new case before changing the live workflow.", False),
        ("report_export_failure", "The report export for {detail} keeps failing.", "Retry with the date range narrowed to one week. If it still fails, send the report name and export time so support can review the job.", False),
    ],
    "account_access": [
        ("password_reset_lockout", "I reset my password but still cannot access the {area}.", "Use the newest reset link, confirm the email is verified, and wait ten minutes after repeated attempts. If access still fails, I can route this to account support.", False),
        ("lost_mfa_device", "A teammate lost their MFA device before {detail}.", "For security, I cannot bypass MFA here. Ask an account admin to start recovery, or I can prepare a secure handoff for identity verification.", True),
        ("role_permission_missing", "A user on our {team} cannot edit the {area}.", "Ask an admin to check the user's role and workspace group. Grant the least permission needed, then have the user refresh their session.", False),
    ],
    "billing_basics": [
        ("download_invoice", "Where can we download the invoice for {detail}?", "Open Billing, select Invoice history, and download the PDF for the needed period. Admin or billing roles can access this page.", False),
        ("billing_contact_update", "How do we update the billing contact for our {team}?", "Go to Billing settings, update the billing contact, and save before generating new receipts. Existing paid receipts may keep old details.", False),
        ("seat_proration_explanation", "Why did our bill change after adding seats to the {area}?", "Alpenglow Assist prorates seats for the remaining billing period. Review the seat change date and plan quantity in Billing history.", False),
    ],
    "workflow_how_to": [
        ("route_priority_cases", "How do we route priority cases from the {area}?", "Create a priority rule, match the case tag or form field, assign the owner group, and place the rule above the default queue.", False),
        ("approval_workflow", "Can we build an approval step for {detail}?", "Yes. Add an approval stage, choose the approver group, and set the next action for approved and rejected cases before publishing.", False),
        ("sla_view_setup", "How can our {team} track SLA risk in Alpenglow Assist?", "Create a saved view filtered by SLA status, sort by due time, and share it with the support leads who manage daily coverage.", False),
    ],
    "safe_escalation": [
        ("suspected_account_takeover", "We suspect account takeover in the {area}.", "I cannot resolve a suspected takeover in chat. I can prepare a security handoff with the workspace, affected user, and event time.", True),
        ("refund_or_credit_request", "Please issue a credit for the {detail} invoice.", "I cannot issue credits directly. I can prepare a billing handoff with the invoice period, reason, and preferred contact.", True),
        ("data_deletion_request", "A customer asked us to delete all data tied to {detail}.", "Data deletion needs verified authorization. I can prepare a privacy handoff with the request scope and requester role.", True),
    ],
}

EVAL_PROMPTS = [
    ("AA-EVAL-001", "onboarding", "A new team wants first-week setup guidance."),
    ("AA-EVAL-002", "troubleshooting", "Notifications and report exports are failing."),
    ("AA-EVAL-003", "account_access", "A user lost MFA and needs access."),
    ("AA-EVAL-004", "billing_basics", "An admin asks why seats changed the invoice."),
    ("AA-EVAL-005", "workflow_how_to", "A team wants a priority routing workflow."),
    ("AA-EVAL-006", "safe_escalation", "A suspected account takeover needs escalation."),
]

EXCLUDED_REASONS = "exact_duplicate near_duplicate contradictory_answer off_brand_tone incomplete_response mislabeled_topic unsafe_overly_technical_response direct_answer_to_escalation_case exact_duplicate near_duplicate off_brand_tone incomplete_response".split()
EXCLUDED_DUPLICATES = {
    0: ("DUP-EXACT-001", "AA-0001"),
    1: ("DUP-NEAR-001", "AA-0008"),
    8: ("DUP-EXACT-002", "AA-0042"),
    9: ("DUP-NEAR-002", "AA-0079"),
}
