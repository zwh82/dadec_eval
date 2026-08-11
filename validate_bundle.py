#!/usr/bin/env python3
"""Validate the DADEC paper-evaluation bundle and write a concise report."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parent
MAX_FILE_BYTES = 20 * 1024 * 1024
FORBIDDEN_SUFFIXES = {".fa", ".fasta", ".fna", ".fastq", ".fq", ".paf", ".bed", ".bam", ".bai", ".sam", ".h5"}
REQUIRED_EVIDENCE = {
    "correction": "results/ecoli3_20x/comparative_ambiguity9999.tsv",
    "raw baselines": "results/raw_long_reads/summary.tsv",
    "short-read coverage": "results/coverage_depths/arabidopsis/selected_results.tsv",
    "short-read quality": "results/ecoli3_error_readcount_quality/quality_sensitivity.tsv",
    "hifieval ecoli3": "results/hifieval/ecoli3_20x/summary.tsv",
    "hifieval arabidopsis": "results/hifieval/arabidopsis_sim_32x/summary.tsv",
    "classification": "results/classification/30strains_legacy_collected/selected_results.tsv",
    "assembly": "results/drosophila_43x/assembly/all_assembly_results.tsv",
    "ablation": "results/arabidopsis_32x/arabidopsis_32x_dadec_ablation_k39_k39_s4_a3_a2_t0p1_dev_fix_a.tsv",
    "30S-BA metadata": "metadata/metagenome/30S-BA/metadata.tsv",
    "30S-NU metadata": "metadata/metagenome/30S-NU/metadata.tsv",
    "100S-BA metadata": "metadata/metagenome/100S-BA/metadata.tsv",
    "100S-NU metadata": "metadata/metagenome/100S-NU/metadata.tsv",
    "metagenome metadata sources": "metadata/metagenome/SOURCE_MANIFEST.tsv",
}
REQUIRED_DOCS = {
    "source code inventory": "docs/SOURCE_CODE_MAP.tsv",
    "result inventory": "docs/RESULT_INVENTORY.tsv",
    "dataset registry": "docs/DATASETS.tsv",
    "issue log": "docs/ISSUES.md",
}
REQUIRED_SELECTED_RUN_EVIDENCE = {
    "main correction selected runs": "runs/ecoli3_20x",
    "coverage selected runs": "runs/arabidopsis_5x",
    "quality selected runs": "runs/ecoli3_error_readcount_hiseq",
    "Zymo depth selected runs": "runs/zymo_5pct",
}
MARKDOWN_LINK_RE = re.compile(r"\[[^]]+\]\(([^)]+)\)")


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def main() -> int:
    errors: list[str] = []
    notes: list[str] = []
    manifest_path = ROOT / "MANIFEST.tsv"
    rows = list(csv.DictReader(manifest_path.open(), delimiter="\t"))
    for row in rows:
        path = ROOT / row["path"]
        if not path.is_file():
            errors.append(f"missing manifest file: {row['path']}")
            continue
        if path.stat().st_size != int(row["bytes"]):
            errors.append(f"size mismatch: {row['path']}")
        elif digest(path) != row["sha256"]:
            errors.append(f"hash mismatch: {row['path']}")

    config_count = 0
    for path in sorted((ROOT / "config").rglob("*.yaml")):
        config_count += 1
        try:
            yaml.safe_load(path.read_text())
        except Exception as exc:  # report all malformed historical configurations together
            errors.append(f"invalid YAML {path.relative_to(ROOT)}: {exc}")

    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            errors.append(f"forbidden intermediate/data file: {path.relative_to(ROOT)}")
        if path.stat().st_size > MAX_FILE_BYTES:
            errors.append(f"file exceeds 20 MiB policy: {path.relative_to(ROOT)}")

    for analysis, relative in REQUIRED_EVIDENCE.items():
        if not (ROOT / relative).is_file():
            errors.append(f"missing {analysis} evidence: {relative}")

    for label, relative in REQUIRED_DOCS.items():
        if not (ROOT / relative).is_file():
            errors.append(f"missing {label}: {relative}")

    for label, relative in REQUIRED_SELECTED_RUN_EVIDENCE.items():
        path = ROOT / relative
        if not path.is_dir() or not any(item.is_file() for item in path.rglob("*")):
            errors.append(f"missing {label}: {relative}")

    mapping = ROOT / "docs" / "PAPER_EVALUATION_MAP.tsv"
    if not mapping.is_file():
        errors.append("missing paper-to-evidence map")
    else:
        mapped = list(csv.DictReader(mapping.open(), delimiter="\t"))
        notes.append(f"paper evaluation mappings: {len(mapped)}")
        for row in mapped:
            for field in ("code", "config", "result"):
                value = row.get(field, "")
                if value and not (ROOT / value).exists():
                    errors.append(f"mapping path missing ({field}): {value}")
            if not row.get("input_source", "").strip():
                errors.append(f"mapping input source missing: {row.get('analysis', 'unknown')}")
            collectors = row.get("collector_or_plot", "")
            if not collectors.strip():
                errors.append(f"mapping collector missing: {row.get('analysis', 'unknown')}")
            for value in (item.strip() for item in collectors.split(";")):
                if value and not (ROOT / value).exists():
                    errors.append(f"mapping collector path missing: {value}")

    external_rows = list(csv.DictReader((ROOT / "EXTERNAL_DATA.tsv").open(), delimiter="\t"))
    missing_external = sum(row["exists"] != "true" for row in external_rows)

    source_map_path = ROOT / "docs" / "SOURCE_CODE_MAP.tsv"
    if source_map_path.is_file():
        source_rows = list(csv.DictReader(source_map_path.open(), delimiter="\t"))
        for row in source_rows:
            if row["status"] != "included":
                continue
            bundled = ROOT / row["bundle_path"]
            if not bundled.is_file():
                errors.append(f"source inventory path missing: {row['bundle_path']}")
            elif digest(bundled) != row["sha256"]:
                errors.append(f"source inventory hash mismatch: {row['bundle_path']}")
        notes.append(f"source inventory rows: {len(source_rows)}")

    result_map_path = ROOT / "docs" / "RESULT_INVENTORY.tsv"
    if result_map_path.is_file():
        result_rows = list(csv.DictReader(result_map_path.open(), delimiter="\t"))
        for row in result_rows:
            bundled = ROOT / row["bundle_path"]
            if not bundled.is_file():
                errors.append(f"result inventory path missing: {row['bundle_path']}")
            elif digest(bundled) != row["sha256"]:
                errors.append(f"result inventory hash mismatch: {row['bundle_path']}")
        notes.append(f"result inventory rows: {len(result_rows)}")

    datasets_path = ROOT / "docs" / "DATASETS.tsv"
    if datasets_path.is_file():
        dataset_rows = list(csv.DictReader(datasets_path.open(), delimiter="\t"))
        required = {"dataset", "type", "source_or_accession", "download_or_generation", "configuration"}
        for number, row in enumerate(dataset_rows, start=2):
            for field in required:
                if not row.get(field, "").strip():
                    errors.append(f"dataset registry row {number} missing {field}")
        notes.append(f"dataset registry rows: {len(dataset_rows)}")

    readme = (ROOT / "README.md").read_text()
    if "> [!IMPORTANT]" not in readme:
        errors.append("README missing IMPORTANT configuration callout")
    for target in MARKDOWN_LINK_RE.findall(readme):
        if "://" in target or target.startswith("#"):
            continue
        if not (ROOT / target).exists():
            errors.append(f"README link target missing: {target}")

    issues_path = ROOT / "docs" / "ISSUES.md"
    if issues_path.is_file() and "Do not edit" not in issues_path.read_text():
        errors.append("issue log is missing the no-silent-correction policy")
    notes.extend([
        f"manifest files: {len(rows)}",
        f"YAML configs parsed: {config_count}",
        f"external paths inventoried: {len(external_rows)} ({missing_external} currently unavailable)",
    ])
    status = "PASS" if not errors else "FAIL"
    report = [f"status: {status}", *notes]
    if errors:
        report.extend(["errors:", *[f"- {error}" for error in errors]])
    text = "\n".join(report) + "\n"
    (ROOT / "validation_report.txt").write_text(text)
    print(text, end="")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
