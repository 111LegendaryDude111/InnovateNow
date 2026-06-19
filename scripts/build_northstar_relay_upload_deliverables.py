from __future__ import annotations

import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "data/northstar_relay_dataset_audit.json"
JSONL_PATH = ROOT / "data/northstar_relay_standardized_conversations.jsonl"
DELIVERABLE_DIR = ROOT / "deliverables/northstar_relay_finetuning"
VALIDATED_JSONL_PATH = DELIVERABLE_DIR / "validated_finetuning_dataset.jsonl"
QUALITY_REPORT_PATH = DELIVERABLE_DIR / "dataset_quality_report.pdf"


def main() -> None:
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    DELIVERABLE_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(JSONL_PATH, VALIDATED_JSONL_PATH)
    write_pdf(QUALITY_REPORT_PATH, report_lines(audit))
    print(f"wrote {VALIDATED_JSONL_PATH}")
    print(f"wrote {QUALITY_REPORT_PATH}")


def report_lines(audit: dict[str, object]) -> list[str]:
    status_counts = audit["status_counts"]
    validation = audit["validation_report"]
    duplicate_groups = audit["duplicate_groups"]
    exclusion_counts = audit["exclusion_reason_counts"]
    top_exclusions = sorted(exclusion_counts.items(), key=lambda item: (-item[1], item[0]))[:8]
    return [
        "Northstar Relay Dataset Quality Report",
        "",
        "Record inclusion decisions",
        f"Source records: {audit['source_record_count']}",
        f"Approved keep records: {status_counts['keep']}",
        f"Review records excluded from training: {status_counts['review']}",
        f"Removed records excluded from training: {status_counts['remove']}",
        "",
        "Exclusions",
        *[f"- {reason}: {count}" for reason, count in top_exclusions],
        "",
        "Duplicates",
        f"Duplicate groups reported: {len(duplicate_groups)}",
        *[f"- {group['duplicate_group_id']}: keep {group['kept_record_id']}" for group in duplicate_groups],
        "",
        "Formatting and validation issues",
        f"Passed checks: {validation['passed_count']}",
        f"Failed checks: {validation['failed_count']}",
        f"Warnings: {validation['warning_count']}",
        f"Warning checks: {', '.join(validation['warning_checks'])}",
        "",
        "Final readiness status",
        "Ready for offline fine-tuning preparation experiments.",
        "Not approved for production model launch without real evaluation.",
        "Dataset is fully synthetic and contains no real customer data.",
    ]


def write_pdf(path: Path, lines: list[str]) -> None:
    content = ["BT", "/F1 11 Tf", "72 760 Td", "14 TL"]
    for line in lines:
        content.append(f"({escape_pdf_text(line)}) Tj")
        content.append("T*")
    content.append("ET")
    stream = "\n".join(content).encode("latin-1")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    path.write_bytes(build_pdf(objects))


def escape_pdf_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def build_pdf(objects: list[bytes]) -> bytes:
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n".encode("ascii"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")
    xref = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode("ascii"))
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode("ascii"))
    return bytes(pdf)


if __name__ == "__main__":
    main()
