from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from wildlife_review_lab.review import (
    build_review_manifest_rows,
    load_review_manifest,
    summarize_review_manifest,
    write_review_manifest,
    write_review_summary,
    write_review_template,
)


class ReviewTests(unittest.TestCase):
    def test_write_review_template(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            destination = Path(temp_dir) / "review.csv"
            write_review_template(destination)
            self.assertTrue(destination.is_file())
            self.assertIn("relative_clip_path", destination.read_text(encoding="utf-8"))

    def test_build_review_manifest_rows_from_reports(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            reports_dir = Path(temp_dir) / "reports"
            reports_dir.mkdir(parents=True, exist_ok=True)
            payload = {
                "status": "success",
                "relative_clip_path": "previews/back_yard/example.mp4",
                "camera_name": "back_yard",
                "top_prediction": "white_tailed_deer",
                "top_prediction_confidence": 0.93,
                "species_counts": {"white_tailed_deer": 2, "bobcat": 1},
                "animal_detection_count": 2,
                "human_present": False,
                "vehicle_present": False,
            }
            (reports_dir / "example.json").write_text(json.dumps(payload), encoding="utf-8")

            rows = build_review_manifest_rows(reports_dir)

            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["source_system"], "deepfaune_new_england")
            self.assertEqual(rows[0]["predicted_label"], "white_tailed_deer")
            self.assertEqual(rows[0]["candidate_labels"], "white_tailed_deer;bobcat")
            self.assertEqual(rows[0]["review_status"], "pending")

    def test_summarize_review_manifest(self) -> None:
        rows = [
            {
                "relative_clip_path": "a.mp4",
                "camera_name": "back_yard",
                "predicted_label": "white_tailed_deer",
                "prediction_confidence": "0.93",
                "reviewed_label": "white_tailed_deer",
                "review_status": "confirmed",
                "notes": "",
            },
            {
                "relative_clip_path": "b.mp4",
                "camera_name": "front_yard",
                "predicted_label": "bobcat",
                "prediction_confidence": "0.61",
                "reviewed_label": "domestic_cat",
                "review_status": "rejected",
                "notes": "",
            },
        ]

        summary = summarize_review_manifest(rows)

        self.assertEqual(summary["total_cases"], 2)
        self.assertEqual(summary["agreement_counts"]["match"], 1)
        self.assertEqual(summary["agreement_counts"]["mismatch"], 1)
        self.assertEqual(summary["agreement_rate"], 0.5)
        self.assertEqual(summary["mismatch_pairs"]["bobcat->domestic_cat"], 1)

    def test_write_and_load_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            destination = Path(temp_dir) / "manifest.csv"
            rows = [
                {
                    "relative_clip_path": "a.mp4",
                    "source_system": "deepfaune_new_england",
                    "camera_name": "back_yard",
                    "report_status": "success",
                    "predicted_label": "white_tailed_deer",
                    "prediction_confidence": 0.93,
                    "candidate_labels": "white_tailed_deer",
                    "animal_detection_count": 1,
                    "human_present": False,
                    "vehicle_present": False,
                    "reviewed_label": "",
                    "review_status": "pending",
                    "notes": "",
                }
            ]
            write_review_manifest(rows, destination)
            loaded = load_review_manifest(destination)
            self.assertEqual(loaded[0]["relative_clip_path"], "a.mp4")

    def test_write_review_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            destination = Path(temp_dir) / "summary.json"
            write_review_summary({"total_cases": 1}, destination)
            self.assertEqual(json.loads(destination.read_text(encoding="utf-8"))["total_cases"], 1)


if __name__ == "__main__":
    unittest.main()
