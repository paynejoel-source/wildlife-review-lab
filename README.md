# Wildlife Review Lab

Credit split:

- repository design, implementation, and maintenance: `paynejoel-source`

Independent toolkit scaffold for the biggest missing gap in wildlife AI workflows:

- human review of model outputs
- site-specific validation
- labeled dataset curation
- error analysis across clips and cameras

This project is intentionally separate from inference pipelines such as `deepfaune-new-england`. It focuses on what happens after predictions are generated:

- selecting candidate clips for review
- producing reviewer-friendly manifests
- tracking expected vs. reviewed labels
- summarizing agreement, disagreement, and unresolved cases

## Why This Exists

Most wildlife AI projects stop at prediction. The harder and more important hole is:

- deciding what to trust
- reviewing uncertain results
- building labeled validation sets
- learning where a model fails at a real site

This repository is meant to fill that gap.

This repository is publishable both as a public GitHub project and as a Python package/release artifact.

## Planned Scope

- ingest reports from pipelines like DeepFaune New England
- build CSV review manifests for humans
- summarize reviewed outcomes into validation reports
- support false-positive analysis and species confusion tracking
- eventually support multiple upstream model pipelines

## Current Scaffold

The scaffold currently includes:

- a minimal Python package
- a CLI
- a first-class review manifest generator for DeepFaune New England clip reports
- a review summary command for labeled CSV manifests
- tests for the core review/validation flow
- minimal example artifacts based on one real local dog clip

## Quickstart

Create a virtual environment and install editable mode:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

Package-style install from the repo root:

```bash
python -m pip install .
```

Generate a blank review template:

```bash
wildlife-review-lab template --output review_cases.csv
```

Generate a review manifest from report JSON files:

```bash
wildlife-review-lab ingest-reports --reports-dir /path/to/reports --output review_manifest.csv
```

Current first-class source adapter:

- `deepfaune_new_england`

Example artifacts:

- [examples/deepfaune_single_dog_review_manifest.csv](examples/deepfaune_single_dog_review_manifest.csv)
- [examples/deepfaune_single_dog_review_summary.json](examples/deepfaune_single_dog_review_summary.json)

Summarize a reviewed manifest:

```bash
wildlife-review-lab summarize --input review_manifest.csv --output review_summary.json
```

## Positioning

This project is not a model repository. It is a workflow and evidence layer for people using wildlife AI in practice.

The included dog example is a minimal proof-of-work case only. It shows how one real local clip can move through manifest generation and reviewed-summary reporting. It is not a meaningful validation dataset, and it does not capture missed events or recall limits from upstream clip generation systems such as Frigate.

## Publishing

This repository includes Python package metadata in `pyproject.toml` and a GitHub Actions workflow for PyPI trusted publishing:

- `.github/workflows/publish-pypi.yml`
