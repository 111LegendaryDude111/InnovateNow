# Northstar Relay Fine-Tuning Dataset

This package prepares a deterministic synthetic support-response dataset for the
fictional SaaS product Northstar Relay. It is intended for data quality checks
before any future fine-tuning run. It does not contain real customer transcripts,
email addresses, phone numbers, account IDs, secrets, or private data.

## Что Сделано

Подготовлен полный синтетический пакет данных для будущего обучения модели
support-ответов Northstar Relay. Пакет закрывает весь workflow: raw records ->
source audit -> keep/review/remove inventory -> duplicate and exclusion audit ->
standardized JSONL -> validation report -> upload-ready deliverables.

Состав результата:

- создан source CSV `data/northstar_relay_support_records.csv` на 152
  синтетические support-записи;
- добавлены статусы аудита `keep`, `review`, `remove` для каждой source-записи;
- покрыты chat, email, internal note и mixed-format каналы;
- добавлены чистые training examples, неполные threads, duplicate и
  near-duplicate records, off-topic cases, escalations, billing issues,
  technical troubleshooting, missing context, truncated text, malformed
  timestamps и ambiguous review cases;
- создан standardized JSONL
  `data/northstar_relay_standardized_conversations.jsonl` на 120 approved
  conversations;
- создан audit artifact `data/northstar_relay_dataset_audit.json` с counts,
  keep/review/remove inventory, duplicate groups, exclusion reasons and
  validation report;
- создан upload-ready JSONL
  `deliverables/northstar_relay_finetuning/validated_finetuning_dataset.jsonl`;
- создан upload-ready PDF report
  `deliverables/northstar_relay_finetuning/dataset_quality_report.pdf`;
- добавлены deterministic generators:
  `scripts/build_northstar_relay_dataset.py` и
  `scripts/build_northstar_relay_upload_deliverables.py`;
- добавлены validation tests `tests/test_northstar_relay_dataset.py`.

Пакет полностью synthetic: в нем нет реальных customer transcripts, email
addresses, phone numbers, account IDs, secrets или private data. Валидация не
вызывает внешние LLM/provider API.

## Artifacts

- `data/northstar_relay_support_records.csv` - mixed raw synthetic source records.
- `data/northstar_relay_standardized_conversations.jsonl` - retained training-ready conversations.
- `data/northstar_relay_dataset_audit.json` - audit inventory, duplicate groups, exclusion reasons, and validation report.
- `deliverables/northstar_relay_finetuning/validated_finetuning_dataset.jsonl` - upload-ready copy of the approved standardized JSONL.
- `deliverables/northstar_relay_finetuning/dataset_quality_report.pdf` - upload-ready PDF quality summary.
- `scripts/build_northstar_relay_dataset.py` - deterministic artifact generator.
- `scripts/build_northstar_relay_upload_deliverables.py` - deterministic upload deliverables generator.
- `tests/test_northstar_relay_dataset.py` - validation tests for schema and data readiness.

## Source Schema

Raw CSV fields are stable and ordered:

```text
record_id,channel,customer_message,agent_response,resolution_summary,created_at,resolved_at,product_area,issue_category,raw_text,audit_status,exclusion_reason,duplicate_group_id,anomaly_flags
```

Allowed `audit_status` values:

- `keep` - suitable for standardized training examples.
- `review` - visible for human decision, excluded from JSONL.
- `remove` - unsuitable for training, excluded from JSONL.

Supported channels:

- `chat`
- `email`
- `internal_note`
- `mixed`

Product area vocabulary:

- `inbox_routing`
- `automations`
- `billing`
- `integrations`
- `reporting`
- `mobile_app`
- `user_management`
- `workspace_settings`

Issue category vocabulary:

- `technical_troubleshooting`
- `how_to`
- `billing_question`
- `account_access`
- `configuration`
- `escalation`

## Mapping Rules

Raw to standardized mapping:

| Raw field | Standardized field | Rule |
|---|---|---|
| `record_id` | `record_id` | Preserve stable source ID. |
| `channel` | `source_channel` | Preserve source channel. |
| `product_area` | `product_area` | Must exist in documented vocabulary. |
| `issue_category` | `issue_category` | Must exist in documented vocabulary. |
| `customer_message` | `messages[0].content` | Role is always `user`. |
| `agent_response` | `messages[1].content` | Role is always `assistant`. |
| `resolution_summary` | `resolution` | Preserve source resolution; do not invent missing outcomes. |
| `anomaly_flags` | `quality_flags` | Safe source quirks such as `note_derived` or `mixed_format_source`. |

Only records with `audit_status = keep` are standardized. `review` and `remove`
records stay in `northstar_relay_dataset_audit.json`.

## Formatting Rules

- One JSON object per JSONL line.
- Each standardized record has exactly one user message followed by one assistant message.
- Role labels are only `user` and `assistant`.
- Empty customer problems, empty support responses, and empty resolutions are not kept.
- Duplicate groups may contain one kept representative, but not multiple kept records.
- Malformed timestamps remain visible in raw CSV and are flagged with `malformed_timestamp`.
- Unsupported, off-topic, spam, external-product, and custom-code requests are routed to `review` or `remove`.

## Audit Summary

Current generated package:

| Metric | Count |
|---|---:|
| Source records | 152 |
| Standardized conversations | 120 |
| Keep | 120 |
| Review | 16 |
| Remove | 16 |

Channel coverage is balanced: 38 `chat`, 38 `email`, 38 `internal_note`, and
38 `mixed` records.

Covered edge cases include:

- incomplete threads;
- duplicate and near-duplicate conversations;
- off-topic content;
- escalations;
- billing issues;
- technical troubleshooting;
- missing customer context;
- missing resolution context;
- truncated messages;
- repeated conversations with slight wording changes;
- malformed timestamps;
- ambiguous review cases.

Duplicate groups:

| Group | Representative | Other records | Rule |
|---|---|---|---|
| `DUP-ROUTE-001` | `NR-0001` | `NR-0121`, `NR-0122` | Keep one routing representative. |
| `DUP-BILL-001` | `NR-0013` | `NR-0123`, `NR-0124`, `NR-0149` | Keep one billing representative. |

Common exclusion reasons are listed in
`data/northstar_relay_dataset_audit.json` under `exclusion_reason_counts`.

## Validation Report

The committed audit report currently shows:

```json
{
  "passed_count": 12,
  "failed_count": 0,
  "warning_count": 3,
  "warning_checks": [
    "duplicate_groups_reported",
    "review_records_present",
    "remove_records_present"
  ]
}
```

Warnings are expected because duplicates, review records, and remove records are
intentional audit inputs.

Validation covers:

- exact raw schema;
- minimum source record count;
- stable unique `record_id` values;
- allowed audit statuses;
- non-empty training text for kept records;
- parseable JSONL objects;
- user/assistant role order;
- exclusion of `review` and `remove` from JSONL;
- duplicate leakage prevention;
- malformed timestamp flagging;
- documented vocabulary use;
- unsupported/off-topic exclusion from training data.

Run validation:

```bash
uv run pytest tests/test_northstar_relay_dataset.py
```

Regenerate upload deliverables:

```bash
uv run python scripts/build_northstar_relay_upload_deliverables.py
```

## Training Readiness

Status: ready for offline fine-tuning preparation experiments, not for
production model launch.

Ready:

- deterministic synthetic data package;
- clean separation between source audit and retained JSONL;
- documented keep/review/remove inventory;
- duplicate and exclusion audit trail;
- validation with no provider calls and no real customer data.

Not included in this issue:

- model training;
- train/validation/test split;
- quality metrics for a tuned model;
- production monitoring;
- real customer transcript ingestion.
