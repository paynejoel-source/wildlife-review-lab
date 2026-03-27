from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REVIEW_FIELDS = [
    "relative_clip_path",
    "camera_name",
    "predicted_label",
    "prediction_confidence",
    "reviewed_label",
    "review_status",
    "notes",
]


def normalize_label(value: str | None) -> str:
    if value is None:
        return ""
    return str(value).strip().lower().replace("-", "_").replace(" ", "_")


def write_review_template(destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REVIEW_FIELDS)
        writer.writeheader()
    return destination


def iter_report_payloads(reports_dir: Path) -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    for path in sorted(reports_dir.rglob("*.json")):
        if any(part in {"hourly", "state", "review", "camtrap_dp", "validation"} for part in path.parts):
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if {"relative_clip_path", "camera_name"}.issubset(payload.keys()):
            payloads.append(payload)
    return payloads


def build_review_manifest_rows(reports_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for payload in iter_report_payloads(reports_dir):
        rows.append(
            {
                "relative_clip_path": str(payload.get("relative_clip_path", "")),
                "camera_name": str(payload.get("camera_name", "")),
                "predicted_label": str(payload.get("top_prediction") or ""),
                "prediction_confidence": payload.get("top_prediction_confidence", ""),
                "reviewed_label": "",
                "review_status": "pending",
                "notes": "",
            }
        )
    return rows


def write_review_manifest(rows: list[dict[str, Any]], destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REVIEW_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return destination


def load_review_manifest(source: Path) -> list[dict[str, str]]:
    with source.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [{key: str(value or "") for key, value in row.items()} for row in reader]


def summarize_review_manifest(rows: list[dict[str, str]]) -> dict[str, Any]:
    status_counts: Counter[str] = Counter()
    agreement_counts: Counter[str] = Counter()
    camera_counts: Counter[str] = Counter()
    mismatches: list[dict[str, str]] = []

    for row in rows:
        review_status = row.get("review_status", "").strip() or "pending"
        status_counts[review_status] += 1
        camera_counts[row.get("camera_name", "").strip() or "unknown"] += 1

        predicted = normalize_label(row.get("predicted_label"))
        reviewed = normalize_label(row.get("reviewed_label"))
        if not reviewed:
            agreement = "unreviewed"
        elif predicted == reviewed:
            agreement = "match"
        else:
            agreement = "mismatch"
            mismatches.append(row)
        agreement_counts[agreement] += 1

    reviewed_total = agreement_counts.get("match", 0) + agreement_counts.get("mismatch", 0)
    agreement_rate = (agreement_counts.get("match", 0) / reviewed_total) if reviewed_total else 0.0

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_cases": len(rows),
        "status_counts": dict(status_counts),
        "agreement_counts": dict(agreement_counts),
        "agreement_rate": round(agreement_rate, 6),
        "camera_counts": dict(camera_counts),
        "mismatches": mismatches,
    }


def write_review_summary(summary: dict[str, Any], destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return destination
