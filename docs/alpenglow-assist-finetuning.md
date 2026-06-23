# Alpenglow Assist Fine-Tuning Package

Пакет готовит синтетический workflow для будущего fine-tuning customer-facing
support assistant продукта Alpenglow Assist. Реальное обучение не запускалось:
issue помечен как `HITL`, потому что еще не выбран base model, provider/runtime,
budget/compute policy и secret handling.

## Что Сделано

- создан deterministic generator `scripts/build_alpenglow_assist_finetuning.py`;
- создан upload-ready dataset
  `deliverables/alpenglow_assist_finetuning/alpenglow_assist_training_dataset.jsonl`;
- создан setup template
  `deliverables/alpenglow_assist_finetuning/fine_tuning_setup.json`;
- создан PDF report
  `deliverables/alpenglow_assist_finetuning/training_evaluation_report.pdf`;
- создан deployment metadata package
  `deliverables/alpenglow_assist_finetuning/deployment_package.json`;
- добавлены validation tests `tests/test_alpenglow_assist_finetuning.py`.

## Dataset

Dataset содержит 108 synthetic examples, по 18 records на каждую категорию:

- `onboarding`;
- `troubleshooting`;
- `account_access`;
- `billing_basics`;
- `workflow_how_to`;
- `safe_escalation`.

Split детерминированный: 96 `train` и 12 `validation`, по 2 validation examples
на каждую тему. Все records имеют single-turn format: `user_message` ->
`assistant_response`.

Count clarification: committed upload JSONL содержит 108 строк, one JSON object
per line. Если reviewer UI показывает 31 record, это preview/truncated excerpt,
а не полный dataset. Проверка:

```bash
wc -l deliverables/alpenglow_assist_finetuning/alpenglow_assist_training_dataset.jsonl
```

Каждая JSONL строка содержит:

```json
{
  "conversation_id": "AA-0001",
  "topic": "onboarding",
  "intent": "first_workspace_setup",
  "user_message": "...",
  "assistant_response": "...",
  "escalation_flag": false,
  "difficulty": "easy",
  "tone": "concise_support",
  "source_notes": "synthetic_clean_example",
  "split": "train"
}
```

## Cleaning

Generator фиксирует cleaning summary в `fine_tuning_setup.json`.

Candidate examples с такими проблемами исключены до финального JSONL:

- exact duplicates;
- near duplicates;
- contradictory answers;
- off-brand tone;
- incomplete responses;
- mislabeled topics;
- unsafe or overly technical responses;
- direct answers where escalation is required.

Финальный JSONL не содержит duplicate user messages, duplicate
user/assistant pairs, secrets, emails, phone numbers or real customer data.

## Training Status

Статус всех training/deployment artifacts:
`blocked_pending_model_provider_decision`.

Это означает:

- no provider calls;
- no checkpoint IDs;
- no fabricated metrics;
- no API keys read or logged;
- deployment is not ready for support workflow integration.

После human decision нужно выбрать base model/provider, запустить реальный
training job, заменить blocked fields на run metadata, добавить реальные
evaluation outputs и подтвердить readiness.

## Validation

Запуск проверки:

```bash
uv run pytest tests/test_alpenglow_assist_finetuning.py
```

Regenerate artifacts:

```bash
uv run python scripts/build_alpenglow_assist_finetuning.py
```
