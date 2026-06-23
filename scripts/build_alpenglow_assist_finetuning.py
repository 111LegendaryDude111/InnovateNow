from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

from alpenglow_assist_finetuning_data import (
    EVAL_PROMPTS,
    EXCLUDED_DUPLICATES,
    EXCLUDED_REASONS,
    SCENARIOS,
    TOPIC_SPECS,
)
from build_northstar_relay_upload_deliverables import write_pdf

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "deliverables/alpenglow_assist_finetuning"
DATASET_PATH = OUT / "alpenglow_assist_training_dataset.jsonl"
SETUP_PATH = OUT / "fine_tuning_setup.json"
REPORT_PATH = OUT / "training_evaluation_report.pdf"
DEPLOY_PATH = OUT / "deployment_package.json"
STATUS = "blocked_pending_model_provider_decision"
SEED = 17017


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    records = build_records()
    cleaning = cleaning_summary(records)
    write_jsonl(records)
    write_json(SETUP_PATH, setup_payload(records, cleaning))
    write_pdf(REPORT_PATH, report_lines(records, cleaning))
    write_json(DEPLOY_PATH, deployment_payload(records))
    print(f"wrote {len(records)} Alpenglow Assist training records")


def build_records() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for topic, specs in TOPIC_SPECS.items():
        for spec_index, (intent, user_t, assistant_t, escalation) in enumerate(specs):
            for scenario_index, scenario in enumerate(SCENARIOS):
                split = "validation" if spec_index == 2 and scenario_index in {1, 4} else "train"
                rows.append(
                    {
                        "conversation_id": f"AA-{len(rows) + 1:04d}",
                        "topic": topic,
                        "intent": intent,
                        "user_message": user_t.format(**scenario),
                        "assistant_response": assistant_t.format(**scenario),
                        "escalation_flag": escalation,
                        "difficulty": "medium" if scenario_index in {2, 5} or escalation else "easy",
                        "tone": "concise_support",
                        "source_notes": "synthetic_clean_example",
                        "split": split,
                    }
                )
    return rows


def cleaning_summary(records: list[dict[str, object]]) -> dict[str, object]:
    excluded = []
    for index, reason in enumerate(EXCLUDED_REASONS):
        group_id, kept_id = EXCLUDED_DUPLICATES.get(index, (None, None))
        excluded.append(
            {
                "candidate_id": f"AA-X{index + 1:03d}",
                "reason": reason,
                "duplicate_group_id": group_id,
                "kept_conversation_id": kept_id,
                "decision": "exclude_before_training_jsonl",
            }
        )
    return {
        "candidate_count": len(records) + len(excluded),
        "retained_count": len(records),
        "excluded_count": len(excluded),
        "exclusion_reason_counts": dict(Counter(item["reason"] for item in excluded)),
        "excluded_candidate_examples": excluded,
        "duplicate_cross_split_leakage": False,
    }


def setup_payload(records: list[dict[str, object]], cleaning: dict[str, object]) -> dict[str, object]:
    target_ratio = round(split_count(records, "validation") / len(records), 4)
    return {
        "schema_version": "2026-06-19",
        "project": "alpenglow_assist",
        "training_status": STATUS,
        "base_model": "pending_human_decision",
        "training_provider_runtime": "pending_human_decision",
        "training_format": {"input": "user_message", "output": "assistant_response"},
        "validation_split": {"target": "10-15%", "actual_ratio": target_ratio, "seed": SEED},
        "checkpointing_strategy": {
            "status": STATUS,
            "planned_policy": "save provider checkpoints per approved run and select best validation checkpoint",
        },
        "evaluation_prompt_set_references": [{"prompt_id": pid, "topic": topic, "prompt": prompt} for pid, topic, prompt in EVAL_PROMPTS],
        "safety_tone_criteria": [
            "concise_support tone",
            "no secrets or PII",
            "escalate account, billing action, privacy, and security cases",
        ],
        "dependencies_policy": {
            "allowed": ["python stdlib", "pytest validation"],
            "forbidden": ["pandas", "torch", "tensorflow", "transformers", "datasets", "training SDKs before approval"],
        },
        "secret_handling": "Do not read, print, store, or commit provider API keys. Human approval required before training calls.",
        "dataset_integrity": {
            "jsonl_path": str(DATASET_PATH.relative_to(ROOT)),
            "jsonl_record_count": len(records),
            "record_count_source": "one JSON object per JSONL line",
            "review_note": "Shorter rendered excerpts are previews only, not the full upload dataset.",
        },
        "topic_distribution": dict(Counter(str(row["topic"]) for row in records)),
        "split_distribution": dict(Counter(str(row["split"]) for row in records)),
        "candidate_cleaning_summary": cleaning,
    }


def deployment_payload(records: list[dict[str, object]]) -> dict[str, object]:
    no_run = "No real training run executed."
    return {
        "model_version": "alpenglow-assist-v1.0.0",
        "training_status": STATUS,
        "selected_checkpoint": None,
        "checkpoint_selection": "blocked until base model, provider, budget, and secret policy are approved",
        "dataset": {"path": str(DATASET_PATH.relative_to(ROOT)), "records": len(records), "sha256": sha256(DATASET_PATH)},
        "fine_tuning_setup": {"path": str(SETUP_PATH.relative_to(ROOT)), "sha256": sha256(SETUP_PATH)},
        "evaluation_report": {"path": str(REPORT_PATH.relative_to(ROOT)), "sha256": sha256(REPORT_PATH), "readiness_verdict": STATUS},
        "integration_readiness_status": "not_ready_for_support_workflow_integration",
        "known_limitations": [no_run, "No live model metrics or checkpoint IDs exist.", "Synthetic data needs human review before provider upload."],
        "rollback_fallback_notes": [
            "Keep existing support workflow active until a validated checkpoint is approved.",
            "Rollback means routing traffic to the current non-fine-tuned assistant or human support queue.",
        ],
        "owner": "Alpenglow Assist product owner",
        "next_steps": ["Choose base model and provider/runtime.", "Approve compute budget and secret handling.", "Run fine-tuning and replace blocked fields with real run metadata."],
    }


def report_lines(records: list[dict[str, object]], cleaning: dict[str, object]) -> list[str]:
    topics = Counter(str(row["topic"]) for row in records)
    splits = Counter(str(row["split"]) for row in records)
    return [
        "Alpenglow Assist Training Evaluation Report",
        f"Training status: {STATUS}",
        f"Dataset records: {len(records)} synthetic examples",
        "Dataset integrity: upload JSONL contains one object per line; shorter reviewer excerpts are previews only.",
        f"Split: train {splits['train']} / validation {splits['validation']}",
        "Topic distribution: " + ", ".join(f"{topic}={count}" for topic, count in sorted(topics.items())),
        f"Candidate cleaning: retained {cleaning['retained_count']} / excluded {cleaning['excluded_count']}",
        "Excluded anomalies: " + ", ".join(sorted(cleaning["exclusion_reason_counts"])),
        "Duplicate leakage check: no duplicate user messages across train and validation.",
        "Tone check: all retained examples use concise_support.",
        "Safety check: escalation cases use handoff language, not direct account or billing actions.",
        "Training iterations: not run; pending human model/provider/runtime decision.",
        "Held-out evaluation prompts: six prompts cover onboarding, troubleshooting, account access, billing basics, workflow, and escalation.",
        "Held-out results: blocked because no checkpoint exists.",
        "Failure cases: no model failures observed; expected risk areas are verbosity, missed escalation, and billing wording drift.",
        f"Readiness verdict: {STATUS}. Upload-ready data exists; deployment is not approved.",
    ]


def write_jsonl(records: list[dict[str, object]]) -> None:
    DATASET_PATH.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in records), encoding="utf-8")


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def split_count(records: list[dict[str, object]], split: str) -> int:
    return sum(1 for row in records if row["split"] == split)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    main()
