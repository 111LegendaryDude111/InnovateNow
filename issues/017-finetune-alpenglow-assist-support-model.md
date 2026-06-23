# Fine-tune Alpenglow Assist support model

- Type: HITL
- User stories covered:
  - Как support team Alpenglow Support Systems, я хочу customer-facing assistant, который отвечает на onboarding, troubleshooting, account access, billing basics и workflow questions в кратком brand-safe стиле.
  - Как ML Engineer, я хочу topic-balanced cleaned JSONL dataset, validation split and evaluation report, чтобы fine-tuning не страдал от duplicates, mislabeled topics and unsafe support behavior.
  - Как product owner Alpenglow Assist, я хочу versioned deployment package, чтобы финальный checkpoint можно было безопасно передать в support workflow integration.

## What to build

Подготовить end-to-end fine-tuning workflow для fictional SaaS `Alpenglow Support Systems` и продукта `Alpenglow Assist`: curated training dataset -> cleaned/deduplicated examples -> fine-tuning setup -> training iterations -> held-out evaluation -> deployment package metadata.

Эта задача `HITL`, потому что перед реальным запуском training нужно выбрать base model, provider/runtime, budget/compute policy and API-key handling. До этого можно подготовить synthetic dataset, validation/evaluation harness, setup file template and package metadata schema, но нельзя утверждать, что model checkpoint реально обучен.

Scope продукта для examples:

- onboarding;
- troubleshooting;
- account access;
- billing basics;
- workflow/how-to questions;
- safe escalation cases.

Assistant responses must be concise, helpful, customer-facing and brand-safe for mid-market SaaS users. Не использовать реальные customer data, реальные emails, phone numbers, secrets, account IDs or private data. Не логировать API keys or provider secrets.

## Required final files

Подготовить upload-ready файлы:

- `deliverables/alpenglow_assist_finetuning/alpenglow_assist_training_dataset.jsonl`
- `deliverables/alpenglow_assist_finetuning/fine_tuning_setup.json`
- `deliverables/alpenglow_assist_finetuning/training_evaluation_report.pdf`
- `deliverables/alpenglow_assist_finetuning/deployment_package.json`

If provider/base-model decision is still missing, `fine_tuning_setup.json`, `training_evaluation_report.pdf` and `deployment_package.json` must clearly mark training status as `blocked_pending_model_provider_decision`, not pretend a completed model exists.

## Training dataset requirements

Generate a comprehensive synthetic fine-tuning dataset as JSONL-style conversation examples. Each record must include:

```json
{
  "conversation_id": "AA-0001",
  "topic": "account_access",
  "intent": "password_reset_lockout",
  "user_message": "I cannot access my account after resetting my password.",
  "assistant_response": "Please try signing in with the new password and confirm your email is verified. If you still cannot access the account, I can help check for a lockout or reset issue.",
  "escalation_flag": false,
  "difficulty": "easy",
  "tone": "concise_support",
  "source_notes": "synthetic_clean_example",
  "split": "train"
}
```

Dataset must be cleaned, deduplicated and topic-balanced across the six scope categories. Include short and medium-length support conversations with realistic SaaS phrasing.

Generate candidate examples with intentional anomalies for cleaning, then exclude or flag them before final training output:

- exact duplicates;
- near-duplicates;
- contradictory answers;
- off-brand tone;
- incomplete responses;
- mislabeled topics;
- unsafe or overly technical support responses;
- cases that require escalation instead of direct answer.

The final training JSONL must not include contradictory, off-brand, incomplete, unsupported or duplicate examples.

## Fine-tuning setup requirements

Create `fine_tuning_setup.json` with:

- selected base model or `pending_human_decision` if not selected;
- training provider/runtime or `pending_human_decision` if not selected;
- training format: user message -> assistant response;
- validation split target, default 10-15%;
- deterministic split seed;
- checkpointing strategy;
- evaluation prompt set references;
- safety/tone criteria;
- allowed and forbidden dependencies/provider calls;
- secret handling notes.

Do not add heavy ML dependencies or local training frameworks unless the human decision explicitly approves them. Prefer provider/API fine-tuning or a documented offline mock plan only after approval.

## Training iteration requirements

After HITL approval of model/provider/runtime, run the fine-tuning process and document:

- training run IDs or local run identifiers;
- dataset version used;
- validation behavior;
- selected best checkpoint;
- observed failures such as verbosity, missed escalation guidance or inconsistent billing wording;
- iteration changes and rationale.

If actual training cannot run in the current environment, report it explicitly and keep artifacts in `blocked` state. Do not fabricate training metrics or checkpoint names.

## Evaluation requirements

Evaluate the model or blocked setup against realistic Alpenglow Assist support prompts covering:

- onboarding;
- troubleshooting;
- account access;
- billing basics;
- workflow/how-to questions;
- safe escalation cases.

Evaluation must include:

- held-out prompt results;
- quality assessment summary;
- failure-case list;
- tone consistency check;
- safety/escalation check;
- duplicate leakage check between train and validation;
- topic distribution report;
- readiness verdict.

## Deployment package requirements

Create `deployment_package.json` with:

- model version, e.g. `alpenglow-assist-v1.0.0`;
- checkpoint selection or blocked status;
- dataset artifact references and hashes/checksums if practical;
- evaluation report reference;
- integration readiness status;
- known limitations;
- rollback/fallback notes;
- owner and next-step fields.

## Acceptance criteria

- [x] Final JSONL dataset exists at `deliverables/alpenglow_assist_finetuning/alpenglow_assist_training_dataset.jsonl`.
- [x] Dataset records include `conversation_id`, `topic`, `intent`, `user_message`, `assistant_response`, `escalation_flag`, `difficulty`, `tone`, `source_notes` and `split`.
- [x] Dataset is synthetic only and contains no real customer PII, secrets or private account data.
- [x] Dataset covers onboarding, troubleshooting, account access, billing basics, workflow/how-to questions and safe escalation cases with documented topic-balanced distribution.
- [x] Cleaned dataset excludes exact duplicates, near-duplicates, contradictory answers, off-brand tone, incomplete responses and mislabeled topics.
- [x] Validation split is deterministic and duplicate groups do not cross train/validation boundaries.
- [x] `fine_tuning_setup.json` defines base model/provider/training format/validation strategy/checkpoint policy, or clearly marks these as blocked pending human decision.
- [ ] If provider/runtime is approved, training iterations are executed and documented without leaking secrets. Not applicable yet: provider/runtime approval is still missing.
- [x] If provider/runtime is not approved or unavailable, training artifacts clearly state blocked status and no fake metrics/checkpoints are created.
- [x] `training_evaluation_report.pdf` summarizes dataset quality, training iterations or blocker, evaluation prompts, held-out results, failure cases, tone/safety checks and readiness verdict.
- [x] `deployment_package.json` is versioned and references the selected checkpoint or blocked status.
- [x] Tests or validation command verify JSONL parseability, required fields, allowed vocabulary, topic balance, split integrity, duplicate removal and escalation coverage.
- [x] `uv run pytest` passes if tests are added; otherwise the documented validation command passes.

## Suggested implementation notes

- Keep generation deterministic with a fixed seed or committed final artifacts.
- Use Python stdlib for dataset generation/validation where possible; do not add `pandas`, `torch`, `tensorflow`, `transformers`, `datasets` or training SDKs without explicit approval.
- A simple PDF writer or existing lightweight dependency may be used for the report; do not add heavy reporting dependencies for one file.
- Treat escalation examples as training targets for safe handoff language, not as solved account/billing actions.
- Prefer truthful blocked artifacts over fake fine-tuning results when compute/provider access is unavailable.

## Blocked by

Human decision required: choose fine-tuning base model, provider/runtime, compute/budget policy, secret handling and whether this project is allowed to run actual training jobs.
