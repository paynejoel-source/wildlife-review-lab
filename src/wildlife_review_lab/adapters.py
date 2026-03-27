from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def iter_dfne_reports(reports_dir: Path) -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    for path in sorted(reports_dir.rglob("*.json")):
        if any(part in {"hourly", "state", "review", "camtrap_dp", "validation"} for part in path.parts):
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if {"relative_clip_path", "camera_name", "status", "species_counts"}.issubset(payload.keys()):
            payloads.append(payload)
    return payloads


def build_dfne_review_rows(reports_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for payload in iter_dfne_reports(reports_dir):
        species_counts = payload.get("species_counts", {}) or {}
        top_species = sorted(
            species_counts.items(),
            key=lambda item: (-int(item[1]), str(item[0])),
        )
        rows.append(
            {
                "source_system": "deepfaune_new_england",
                "relative_clip_path": str(payload.get("relative_clip_path", "")),
                "camera_name": str(
                    payload.get("camera_name")
                    or Path(str(payload.get("relative_clip_path", ""))).parent.name
                ),
                "report_status": str(payload.get("status", "")),
                "predicted_label": str(payload.get("top_prediction") or ""),
                "prediction_confidence": payload.get("top_prediction_confidence", ""),
                "candidate_labels": ";".join(str(label) for label, _count in top_species[:5]),
                "animal_detection_count": payload.get("animal_detection_count", 0),
                "human_present": bool(payload.get("human_present", False)),
                "vehicle_present": bool(payload.get("vehicle_present", False)),
                "reviewed_label": "",
                "review_status": "pending",
                "notes": "",
            }
        )
    return rows
