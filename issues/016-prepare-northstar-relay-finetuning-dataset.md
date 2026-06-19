# Подготовить fine-tuning dataset для Northstar Relay support responses

- Type: AFK
- User stories covered:
  - Как support team Northstar Relay, я хочу получить очищенный набор support examples, чтобы будущая модель отвечала на реальные small-business support scenarios.
  - Как ML Engineer, я хочу иметь audit trail keep/remove/review и duplicate/exclusion list, чтобы шумные записи не попали в fine-tuning dataset.
  - Как сопровождающий проекта, я хочу deterministic synthetic dataset и validation report, чтобы проверять schema, content quality и training readiness без реальных customer data.

## What to build

Создать полный synthetic dataset package для fictional SaaS `Northstar Relay`, который готовит support-response model к fine-tuning. Вертикальный срез должен пройти весь data workflow: mixed raw support records -> source record audit -> keep/remove/review inventory -> duplicate and exclusion list -> standardized conversation records -> final validation -> training readiness summary.

Dataset должен быть полностью синтетическим. Не использовать реальные customer transcripts, email addresses, phone numbers, account IDs, secrets или private data. Не вызывать внешние LLM/provider API для генерации или валидации в тестах.

Подготовить committed artifacts:

- `data/northstar_relay_support_records.csv` — raw synthetic support records.
- `data/northstar_relay_standardized_conversations.jsonl` — retained records in uniform fine-tuning conversation format.
- `data/northstar_relay_dataset_audit.json` — audit summary, keep/remove/review inventory, duplicate groups and exclusion reasons.
- `docs/northstar-relay-finetuning-dataset.md` — schema mapping notes, formatting rules, validation results and training readiness summary.

Raw source CSV schema must include these columns in stable order:

```text
record_id,channel,customer_message,agent_response,resolution_summary,created_at,resolved_at,product_area,issue_category,raw_text,audit_status,exclusion_reason,duplicate_group_id,anomaly_flags
```

Standardized JSONL records must use a predictable schema:

```json
{
  "record_id": "NR-0001",
  "source_channel": "chat",
  "product_area": "inbox_routing",
  "issue_category": "technical_troubleshooting",
  "messages": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ],
  "resolution": "...",
  "quality_flags": []
}
```

Only records with `audit_status = keep` should appear in the standardized JSONL. Records marked `review` or `remove` stay in the audit artifact with reasons.

## Source record audit requirements

Generate a mixed collection of support records across channels:

- chat transcripts;
- email threads;
- internal resolution notes;
- mixed-format support interactions.

Each source record must include enough metadata to determine `keep`, `remove` or `review` status. Use a strict inclusion standard: if a record does not clearly show both the customer problem and a meaningful support response, route it to `review` or `remove` instead of forcing it into training data.

The source dataset must include:

- clean examples suitable for training;
- incomplete threads;
- duplicate and near-duplicate conversations;
- irrelevant or off-topic content;
- escalations;
- billing issues;
- technical troubleshooting;
- missing customer context;
- missing resolution context;
- truncated messages;
- repeated conversations with slight wording changes;
- malformed timestamps;
- ambiguous cases flagged for review.

## Standardization requirements

Transform retained examples into a uniform conversation format while preserving original intent, tone and resolution. Normalize structure, not meaning.

The standardized dataset must:

- separate user request, assistant response and resolution context;
- keep role labels consistent across chat, email and note-derived examples;
- preserve product area and issue category metadata;
- exclude records with missing meaningful response or missing support-use-case context;
- avoid hallucinating resolution details that are not present in source fields;
- include quality flags where source quirks remain safe but notable.

## Final validation requirements

Add a validation pass that checks both structure and semantic suitability:

- required fields are present and non-empty where required;
- JSONL records are parseable one object per line;
- standardized records contain at least one user message and one assistant message;
- `review` and `remove` records do not appear in JSONL training data;
- duplicate groups are reported;
- malformed timestamps are flagged in audit instead of silently normalized;
- product area and issue category values come from documented vocabularies;
- records with unsupported/off-topic content are removed or routed to review;
- validation report includes passed, failed and warning counts.

## Acceptance criteria

- [x] `data/northstar_relay_support_records.csv` exists with the exact raw schema listed above.
- [x] Source CSV contains at least 150 synthetic records with stable unique `record_id` values.
- [x] Source records cover chat, email, internal note and mixed-format channels.
- [x] Source records include clean examples, incomplete threads, duplicate/near-duplicate records, off-topic content, escalations, billing issues, troubleshooting issues, missing context, truncated text, malformed timestamps and ambiguous review cases.
- [x] Every source record has `audit_status` set to exactly one of `keep`, `remove`, `review`.
- [x] Audit artifact reports total counts for keep/remove/review and lists common exclusion reasons.
- [x] Duplicate and near-duplicate groups are represented with `duplicate_group_id` and summarized in the audit artifact.
- [x] `data/northstar_relay_standardized_conversations.jsonl` exists and includes only retained `keep` records.
- [x] Standardized JSONL uses consistent role labels and separates user request, assistant response and resolution context.
- [x] Schema mapping notes explain how raw fields map into standardized conversation fields.
- [x] Final validation checks structure and semantic suitability, not only formatting.
- [x] Validation catches empty required fields, malformed JSONL, malformed timestamps, duplicate leakage and unsupported/off-topic records.
- [x] Documentation includes source record audit summary, keep/remove/review inventory, duplicate and exclusion list, quality check report and training readiness summary.
- [x] Tests or a validation command use only Python stdlib or existing project dependencies; do not add `pandas`, local ML frameworks or external provider calls.
- [x] `uv run pytest` passes if tests are added; otherwise the documented validation command passes.

## Suggested implementation notes

- Prefer committed deterministic data over runtime random generation. If a generator is added, use a fixed seed and keep generated artifacts committed.
- Use Python stdlib `csv`, `json`, `datetime` and `pathlib` for generation/validation unless an existing project helper already fits.
- Keep generator/validator modules small; if code approaches 200 lines, split data constants from validation logic.
- Treat `review` as a real outcome, not a failure. Ambiguous records should remain visible for human decision instead of being silently kept or removed.
- Do not over-optimize for model training metrics in this issue. Goal is data quality, schema consistency and training readiness checks.

## Blocked by

None - can start immediately
