#!/home/wenhai/miniconda3/envs/snakemake/bin/python
"""Compare experiment-default runs with the best non-default run per score."""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
from typing import Any

from core import (
    METAQUAST_REPORTS,
    QUAST_REPORTS,
    ROOT,
    Target,
    assess_candidate,
    audit_all,
    build_targets,
    candidate_matches_group,
    candidate_matches_target,
    candidate_values,
    discover_runs,
    parse_report,
    parse_resource_text,
    report_paths,
)


QUALITY_FIELDS = (
    "haplotype_coverage_percent",
    "mismatches_per_100_kbp",
    "indels_per_100_kbp",
    "local_misassemblies",
    "contigs_number",
    "WallTime(h)",
)
METRIC_FIELDS = (
    "CPU(h)", "WallTime(h)", "Memory(GB)",
    "mismatches_per_100_kbp", "indels_per_100_kbp",
    "haplotype_coverage_percent", "local_misassemblies", "contigs_number",
)
COMPARISON_FIELDS = [
    "dataset", "coverage", "run_label", "method", "evaluation_tool",
    "ambiguity_score", "score_status", "default_run_id", "comparator_run_id",
    "default_parameters", "comparator_parameters",
    *[f"default_{field}" for field in METRIC_FIELDS],
    *[f"comparator_{field}" for field in METRIC_FIELDS],
    *[f"delta_{field}" for field in METRIC_FIELDS],
]
DECISION_FIELDS = [
    "dataset", "coverage", "run_label", "method", "evaluation_tool",
    "decision", "score_statuses", "default_run_id", "comparator_run_ids",
    "hero_candidate",
]


def quality_key(row: dict[str, Any]) -> tuple[float | int, ...]:
    return (
        -float(row["haplotype_coverage_percent"]),
        float(row["mismatches_per_100_kbp"]),
        float(row["indels_per_100_kbp"]),
        int(row["local_misassemblies"]),
        int(row["contigs_number"]),
        float(row["WallTime(h)"]),
    )


def metric_row(candidate, target: Target, score: str) -> dict[str, Any]:
    resources = candidate.root / "benchmark" / f"short_{target.coverage}" / target.method / "resources.time.txt"
    parsed_resources = parse_resource_text(resources.read_text())
    report = report_paths(candidate, target)[score]
    metrics = parse_report(report)
    return {
        "CPU(h)": parsed_resources["total_cpu_seconds"] / 3600,
        "WallTime(h)": parsed_resources["wall_seconds"] / 3600,
        "Memory(GB)": parsed_resources["max_rss_kb"] / 1024 / 1024,
        **metrics,
    }


def display_number(value: Any) -> str:
    if value in (None, ""):
        return ""
    if isinstance(value, int):
        return str(value)
    return f"{float(value):.9g}"


def comparison_row(
    target: Target,
    score: str,
    default_candidate,
    comparator_candidate,
) -> dict[str, str]:
    base = {
        "dataset": target.dataset,
        "coverage": target.coverage,
        "run_label": target.run_label,
        "method": target.method,
        "evaluation_tool": target.evaluation_tool,
        "ambiguity_score": score,
        "default_run_id": "",
        "comparator_run_id": "",
        "default_parameters": "",
        "comparator_parameters": "",
    }
    for prefix in ("default", "comparator", "delta"):
        for field in METRIC_FIELDS:
            base[f"{prefix}_{field}"] = ""
    if default_candidate is None:
        base["score_status"] = "default_missing"
        return base
    default_metrics = metric_row(default_candidate, target, score)
    base["default_run_id"] = str(default_candidate.provenance.get("run_id") or default_candidate.root.name)
    base["default_parameters"] = json.dumps(
        candidate_values(default_candidate, target.coverage), sort_keys=True, separators=(",", ":")
    )
    for field in METRIC_FIELDS:
        base[f"default_{field}"] = display_number(default_metrics[field])
    if comparator_candidate is None:
        base["score_status"] = "no_comparator"
        return base
    comparator_metrics = metric_row(comparator_candidate, target, score)
    base["comparator_run_id"] = str(
        comparator_candidate.provenance.get("run_id") or comparator_candidate.root.name
    )
    base["comparator_parameters"] = json.dumps(
        candidate_values(comparator_candidate, target.coverage), sort_keys=True, separators=(",", ":")
    )
    for field in METRIC_FIELDS:
        base[f"comparator_{field}"] = display_number(comparator_metrics[field])
        base[f"delta_{field}"] = display_number(
            float(default_metrics[field]) - float(comparator_metrics[field])
        )
    default_key = quality_key(default_metrics)
    comparator_key = quality_key(comparator_metrics)
    if default_key < comparator_key:
        base["score_status"] = "default_better"
    elif default_key == comparator_key:
        base["score_status"] = "tie"
    else:
        base["score_status"] = "not_better"
    return base


def decide_score_statuses(statuses: list[str]) -> str:
    if any(status == "default_missing" for status in statuses):
        return "default_missing"
    if all(status == "no_comparator" for status in statuses):
        return "no_comparator"
    if any(status == "no_comparator" for status in statuses):
        return "mixed_scores"
    if all(status == "default_better" for status in statuses):
        return "default_better"
    if all(status in {"not_better", "tie"} for status in statuses):
        return "not_better"
    return "mixed_scores"


def build_comparisons() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    targets = build_targets()
    runs = discover_runs()
    comparison_rows: list[dict[str, str]] = []
    decision_rows: list[dict[str, str]] = []
    for target in targets:
        defaults = []
        comparators = []
        for candidate in runs:
            if candidate_matches_target(candidate, target):
                status, _, _ = assess_candidate(candidate, target)
                if status == "complete":
                    defaults.append(candidate)
            elif candidate_matches_group(candidate, target):
                status, _, _ = assess_candidate(candidate, target)
                if status == "complete":
                    comparators.append(candidate)
        if len(defaults) > 1:
            raise ValueError(f"Multiple complete semantic defaults for {target.target_id}")
        default_candidate = defaults[0] if defaults else None
        scores = tuple(METAQUAST_REPORTS if target.evaluation_tool == "metaquast" else QUAST_REPORTS)
        target_rows = []
        for score in scores:
            comparator_candidate = None
            if comparators:
                comparator_candidate = min(
                    comparators, key=lambda candidate: quality_key(metric_row(candidate, target, score))
                )
            row = comparison_row(target, score, default_candidate, comparator_candidate)
            comparison_rows.append(row)
            target_rows.append(row)
        statuses = [row["score_status"] for row in target_rows]
        decision = decide_score_statuses(statuses)
        decision_rows.append({
            "dataset": target.dataset,
            "coverage": target.coverage,
            "run_label": target.run_label,
            "method": target.method,
            "evaluation_tool": target.evaluation_tool,
            "decision": decision,
            "score_statuses": ",".join(
                f"{row['ambiguity_score']}={row['score_status']}" for row in target_rows
            ),
            "default_run_id": target_rows[0]["default_run_id"],
            "comparator_run_ids": ",".join(sorted({
                row["comparator_run_id"] for row in target_rows if row["comparator_run_id"]
            })),
            "hero_candidate": "yes" if decision == "default_better" else "no",
        })
    return comparison_rows, decision_rows


def write_tsv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with open(temporary, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--comparison-output", type=Path,
        default=ROOT / "benchmark/results/default_parameter_comparison.tsv",
    )
    parser.add_argument(
        "--decision-output", type=Path,
        default=ROOT / "benchmark/results/default_parameter_decisions.tsv",
    )
    parser.add_argument("--require-complete", action="store_true")
    args = parser.parse_args()
    if args.require_complete:
        incomplete = [record for record in audit_all() if record.status != "complete"]
        if incomplete:
            print(f"Refusing final comparison: {len(incomplete)} default targets are incomplete")
            return 1
    comparisons, decisions = build_comparisons()
    write_tsv(args.comparison_output, COMPARISON_FIELDS, comparisons)
    write_tsv(args.decision_output, DECISION_FIELDS, decisions)
    counts: dict[str, int] = {}
    for row in decisions:
        counts[row["decision"]] = counts.get(row["decision"], 0) + 1
    print(f"Comparison rows: {len(comparisons)}")
    print(f"Decision rows: {len(decisions)}")
    for decision, count in sorted(counts.items()):
        print(f"  {decision:18s} {count:3d}")
    print(f"Comparison: {args.comparison_output.resolve()}")
    print(f"Decisions: {args.decision_output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
