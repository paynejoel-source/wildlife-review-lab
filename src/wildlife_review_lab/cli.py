from __future__ import annotations

import argparse
from pathlib import Path

from wildlife_review_lab.review import (
    build_review_manifest_rows,
    load_review_manifest,
    summarize_review_manifest,
    write_review_manifest,
    write_review_summary,
    write_review_template,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wildlife-review-lab",
        description="Review and validation toolkit scaffold for wildlife AI outputs.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    template_parser = subparsers.add_parser("template", help="Write a blank review CSV template.")
    template_parser.add_argument("--output", required=True, help="Destination CSV path.")

    ingest_parser = subparsers.add_parser(
        "ingest-reports",
        help="Create a review manifest from report JSON files.",
    )
    ingest_parser.add_argument("--reports-dir", required=True, help="Directory containing report JSON files.")
    ingest_parser.add_argument("--output", required=True, help="Destination CSV path.")

    summarize_parser = subparsers.add_parser(
        "summarize",
        help="Summarize a reviewed CSV manifest into a JSON report.",
    )
    summarize_parser.add_argument("--input", required=True, help="Reviewed CSV manifest.")
    summarize_parser.add_argument("--output", required=True, help="Destination JSON path.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "template":
        destination = write_review_template(Path(args.output))
        print(f"Wrote review template: {destination}")
        return 0

    if args.command == "ingest-reports":
        rows = build_review_manifest_rows(Path(args.reports_dir))
        destination = write_review_manifest(rows, Path(args.output))
        print(f"Wrote review manifest: {destination}")
        return 0

    if args.command == "summarize":
        rows = load_review_manifest(Path(args.input))
        summary = summarize_review_manifest(rows)
        destination = write_review_summary(summary, Path(args.output))
        print(f"Wrote review summary: {destination}")
        return 0

    parser.error(f"Unsupported command: {args.command}")
    return 2
