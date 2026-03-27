from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from wildlife_review_lab.adapters import build_dfne_review_rows


REVIEW_FIELDS = [
    "source_system",
    "relative_clip_path",
    "camera_name",
    "report_status",
    "predicted_label",
    "prediction_confidence",
    "candidate_labels",
    "animal_detection_count",
    "human_present",
    "vehicle_present",
    "reviewed_label",
    "review_status",
    "notes",
]

REVIEW_STATUSES = {
    "pending",
    "confirmed",
    "rejected",
    "uncertain",
    "needs_second_review",
    "not_reviewable",
}


def parse_confidence(value: str | float | int | None) -> float | None:
    if value in ("", None):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def confidence_bucket(value: float | None) -> str:
    if value is None:
        return "unknown"
    if value < 0.5:
        return "<0.50"
    if value < 0.75:
        return "0.50-0.74"
    if value < 0.9:
        return "0.75-0.89"
    return ">=0.90"


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


def build_review_manifest_rows(reports_dir: Path, source_system: str = "deepfaune_new_england") -> list[dict[str, Any]]:
    if source_system != "deepfaune_new_england":
        raise ValueError(f"Unsupported source system: {source_system}")
    return build_dfne_review_rows(reports_dir)


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
    mismatch_pairs: Counter[str] = Counter()
    confidence_bucket_counts: Counter[str] = Counter()
    camera_mismatch_counts: Counter[str] = Counter()
    camera_reviewed_counts: Counter[str] = Counter()
    contamination_counts: Counter[str] = Counter()
    mismatches: list[dict[str, str]] = []

    for row in rows:
        review_status = row.get("review_status", "").strip() or "pending"
        if review_status not in REVIEW_STATUSES:
            review_status = "pending"
        status_counts[review_status] += 1
        camera_name = row.get("camera_name", "").strip() or "unknown"
        camera_counts[camera_name] += 1

        confidence = parse_confidence(row.get("prediction_confidence"))
        confidence_bucket_counts[confidence_bucket(confidence)] += 1

        if str(row.get("human_present", "")).strip().lower() == "true":
            contamination_counts["human_present"] += 1
        if str(row.get("vehicle_present", "")).strip().lower() == "true":
            contamination_counts["vehicle_present"] += 1

        predicted = normalize_label(row.get("predicted_label"))
        reviewed = normalize_label(row.get("reviewed_label"))
        if not reviewed:
            agreement = "unreviewed"
        elif predicted == reviewed:
            agreement = "match"
            camera_reviewed_counts[camera_name] += 1
        else:
            agreement = "mismatch"
            mismatch_pairs[f"{predicted or 'none'}->{reviewed or 'none'}"] += 1
            camera_reviewed_counts[camera_name] += 1
            camera_mismatch_counts[camera_name] += 1
            mismatches.append(row)
        agreement_counts[agreement] += 1

    reviewed_total = agreement_counts.get("match", 0) + agreement_counts.get("mismatch", 0)
    agreement_rate = (agreement_counts.get("match", 0) / reviewed_total) if reviewed_total else 0.0
    camera_error_rates = {
        camera: round(camera_mismatch_counts[camera] / reviewed_count, 6)
        for camera, reviewed_count in camera_reviewed_counts.items()
        if reviewed_count
    }

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_cases": len(rows),
        "status_counts": dict(status_counts),
        "agreement_counts": dict(agreement_counts),
        "agreement_rate": round(agreement_rate, 6),
        "camera_counts": dict(camera_counts),
        "mismatch_pairs": dict(mismatch_pairs),
        "confidence_bucket_counts": dict(confidence_bucket_counts),
        "camera_reviewed_counts": dict(camera_reviewed_counts),
        "camera_mismatch_counts": dict(camera_mismatch_counts),
        "camera_error_rates": camera_error_rates,
        "contamination_counts": dict(contamination_counts),
        "mismatches": mismatches,
    }


def write_review_summary(summary: dict[str, Any], destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return destination
