#!/usr/bin/env python3
"""Collect configuration-audited short-read coverage benchmark results."""

from __future__ import annotations

import argparse
import csv
import io
import json
import math
import os
import sys
import tempfile
from pathlib import Path

import yaml


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[3]
BENCHMARK = ROOT / "benchmark"
sys.path.insert(0, str(BENCHMARK / "scripts"))

from method_config import resolve_coverage_parameters  # noqa: E402
from parse_metaquast import parse_report  # noqa: E402
from parse_resources import parse_resource_text  # noqa: E402


METHODS = (
    "dadec", "fmlrc", "f_hero", "ratatosk", "r_hero",
    "lordec", "l_hero", "colormap", "proovread",
)
METHOD_LABELS = {
    "dadec": "DADEC", "fmlrc": "FMLRC", "f_hero": "F_HERO",
    "ratatosk": "Ratatosk", "r_hero": "R_HERO", "lordec": "LoRDEC",
    "l_hero": "L_HERO", "colormap": "CoLoRMap", "proovread": "Proovread",
}
RELEVANT_FIELDS = {
    "dadec": ("dadec_k1", "dadec_k2", "dadec_split", "dadec_threshold", "dadec_abundance1", "dadec_abundance2"),
    "fmlrc": ("fmlrc_k1", "fmlrc_k2"),
    "f_hero": ("fmlrc_k1", "fmlrc_k2", "hero_split", "hero_iterations"),
    "ratatosk": ("ratatosk_k1", "ratatosk_k2"),
    "r_hero": ("ratatosk_k1", "ratatosk_k2", "hero_split", "hero_iterations"),
    "lordec": ("lordec_k", "lordec_solid"),
    "l_hero": ("lordec_k", "lordec_solid", "hero_split", "hero_iterations"),
    "colormap": (),
    "proovread": (),
}
DATASETS = {
    "30s_ua": {
        "dataset_id": "30strains_legacy",
        "coverages": ("10x", "20x", "30x", "40x", "50x"),
        "evaluation": "metaquast",
        "ambiguity_score": "0.9999",
    },
    "30s_ba": {
        "dataset_id": "30strains",
        "coverages": ("10x", "20x", "30x", "40x", "50x"),
        "evaluation": "metaquast",
        "ambiguity_score": "0.9999",
    },
    "arabidopsis": {
        "dataset_id": "arabidopsis",
        "coverages": ("3x", "5x", "8x", "10x", "15x", "20x", "25x", "30x", "32x"),
        "evaluation": "quast",
        "ambiguity_score": "NA",
    },
}
METRIC_FIELDS = (
    "mismatches_per_100_kbp", "indels_per_100_kbp",
    "haplotype_coverage_percent", "local_misassemblies", "contigs_number",
)
RESOURCE_FIELDS = ("CPU(h)", "WallTime(h)", "Memory(GB)")
ALL_FIELDS = (
    "dataset_label", "dataset_id", "short_coverage", "method", "method_id",
    "run_id", "software_revision", "config_match", "candidate_status",
    "expected_parameters", "actual_parameters", "evaluation_tool",
    "ambiguity_score", "report_status", "resource_status",
    *RESOURCE_FIELDS, *METRIC_FIELDS, "residual_errors_per_100_kbp",
    "metric_rank_within_config", "is_metric_best", "is_recommended",
    "selection_reason", "run_config", "provenance", "report", "resource_log",
)
STATUS_FIELDS = (
    "dataset_label", "dataset_id", "short_coverage", "method", "method_id",
    "candidate_count", "exact_config_count", "exact_config_with_report_count",
    "recommended_run_id", "status", "note",
)


def load_yaml(path: Path) -> dict:
    value = yaml.safe_load(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"expected YAML mapping: {path}")
    return value


def deep_merge(base: dict, overlay: dict) -> dict:
    result = json.loads(json.dumps(base))
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def compact_parameters(values: dict, method: str) -> dict:
    return {field: values.get(field) for field in RELEVANT_FIELDS[method]}


def expected_parameters(dataset_id: str, coverage: str, method: str) -> tuple[dict, Path]:
    common = load_yaml(BENCHMARK / "config/common.yaml")
    dataset_path = BENCHMARK / f"config/datasets/{dataset_id}.yaml"
    config_path = BENCHMARK / f"config/runs/{dataset_id}/{coverage}_{method}.yaml"
    if not config_path.is_file():
        raise FileNotFoundError(f"missing run config: {config_path}")
    merged = deep_merge(common, load_yaml(dataset_path))
    merged = deep_merge(merged, load_yaml(config_path))
    _, values = resolve_coverage_parameters(merged, coverage)
    return compact_parameters(values, method), config_path


def report_path(run_root: Path, coverage: str, method: str, evaluation: str) -> Path:
    base = run_root / "output" / f"short_{coverage}" / method
    if evaluation == "metaquast":
        return base / "metaquast.ambiguity9999/combined_reference/report.tsv"
    return base / "quast/report.tsv"


def software_revision(run_id: str) -> str:
    if "dev_fix_a" in run_id:
        return "dev_fix_a"
    if "dev_fix" in run_id:
        return "dev_fix"
    return "original_or_legacy"


def candidate_sort_key(row: dict) -> tuple:
    def number(field, default=math.inf):
        try:
            return float(row[field])
        except (KeyError, TypeError, ValueError):
            return default
    return (
        number("residual_errors_per_100_kbp"),
        -number("haplotype_coverage_percent", default=-math.inf),
        number("local_misassemblies"),
        number("contigs_number"),
        number("WallTime(h)"),
        row["run_id"],
    )


def discover_candidates(dataset_label: str, spec: dict) -> tuple[list[dict], list[dict]]:
    dataset_id = spec["dataset_id"]
    rows: list[dict] = []
    status_rows: list[dict] = []
    for coverage in spec["coverages"]:
        runs_root = BENCHMARK / f"runs/{dataset_id}_{coverage}"
        for method in METHODS:
            expected, config_path = expected_parameters(dataset_id, coverage, method)
            candidates = []
            if runs_root.is_dir():
                for provenance_path in sorted(runs_root.glob("*/benchmark/provenance.json")):
                    provenance = json.loads(provenance_path.read_text())
                    if method not in (provenance.get("methods") or []):
                        continue
                    actual_all = (provenance.get("parameters_by_coverage") or {}).get(coverage)
                    if not isinstance(actual_all, dict):
                        continue
                    run_root = provenance_path.parents[1]
                    actual = compact_parameters(actual_all, method)
                    exact = actual == expected
                    report = report_path(run_root, coverage, method, spec["evaluation"])
                    resource = run_root / "benchmark" / f"short_{coverage}" / method / "resources.time.txt"
                    report_exists = report.is_file()
                    resource_exists = resource.is_file()
                    metrics = {field: "" for field in METRIC_FIELDS}
                    resources = {field: "" for field in RESOURCE_FIELDS}
                    if report_exists:
                        parsed = parse_report(report)
                        metrics.update({field: str(parsed[field]) for field in METRIC_FIELDS})
                    if resource_exists:
                        parsed_resource = parse_resource_text(resource.read_text())
                        resources.update({
                            "CPU(h)": f'{parsed_resource["total_cpu_seconds"] / 3600:.3f}',
                            "WallTime(h)": f'{parsed_resource["wall_seconds"] / 3600:.3f}',
                            "Memory(GB)": f'{parsed_resource["max_rss_kb"] / 1024 / 1024:.3f}',
                        })
                    residual = ""
                    if report_exists:
                        residual = f'{float(metrics["mismatches_per_100_kbp"]) + float(metrics["indels_per_100_kbp"]):.2f}'
                    if not exact:
                        candidate_status = "nonmatching_config"
                    elif not report_exists:
                        candidate_status = "missing_report"
                    elif not resource_exists:
                        candidate_status = "missing_resource"
                    else:
                        candidate_status = "complete"
                    row = {
                        "dataset_label": dataset_label,
                        "dataset_id": dataset_id,
                        "short_coverage": coverage,
                        "method": METHOD_LABELS[method],
                        "method_id": method,
                        "run_id": provenance.get("run_id") or run_root.name,
                        "software_revision": software_revision(provenance.get("run_id") or run_root.name),
                        "config_match": "exact" if exact else "nonmatching",
                        "candidate_status": candidate_status,
                        "expected_parameters": json.dumps(expected, sort_keys=True, separators=(",", ":")),
                        "actual_parameters": json.dumps(actual, sort_keys=True, separators=(",", ":")),
                        "evaluation_tool": spec["evaluation"],
                        "ambiguity_score": spec["ambiguity_score"],
                        "report_status": "present" if report_exists else "missing",
                        "resource_status": "present" if resource_exists else "missing",
                        **resources,
                        **metrics,
                        "residual_errors_per_100_kbp": residual,
                        "metric_rank_within_config": "",
                        "is_metric_best": "no",
                        "is_recommended": "no",
                        "selection_reason": "",
                        "run_config": relative(config_path),
                        "provenance": relative(provenance_path),
                        "report": relative(report),
                        "resource_log": relative(resource),
                    }
                    candidates.append(row)
                    rows.append(row)

            eligible = [row for row in candidates if row["config_match"] == "exact" and row["report_status"] == "present"]
            eligible.sort(key=candidate_sort_key)
            for rank, row in enumerate(eligible, 1):
                row["metric_rank_within_config"] = str(rank)
            metric_best = eligible[0] if eligible else None
            if metric_best:
                metric_best["is_metric_best"] = "yes"
            recommended = None
            reason = ""
            if eligible:
                pool = eligible
                if method == "dadec":
                    current = [row for row in eligible if row["software_revision"] == "dev_fix_a"]
                    if current:
                        pool = current
                        reason = "exact config; current dev_fix_a revision; best residual-error rank within revision"
                recommended = min(pool, key=candidate_sort_key)
                if not reason:
                    reason = "exact config; best residual-error rank"
                recommended["is_recommended"] = "yes"
                recommended["selection_reason"] = reason

            exact_count = sum(row["config_match"] == "exact" for row in candidates)
            exact_report_count = len(eligible)
            if recommended:
                status = "selected"
                note = reason
                recommended_id = recommended["run_id"]
            elif exact_count:
                status = "missing_report"
                note = "exact-config candidate exists but has no required evaluation report"
                recommended_id = ""
            elif candidates:
                status = "no_config_match"
                note = "runs exist but none matches the effective YAML configuration"
                recommended_id = ""
            else:
                status = "missing_run"
                note = "no provenance-bearing run found"
                recommended_id = ""
            status_rows.append({
                "dataset_label": dataset_label,
                "dataset_id": dataset_id,
                "short_coverage": coverage,
                "method": METHOD_LABELS[method],
                "method_id": method,
                "candidate_count": str(len(candidates)),
                "exact_config_count": str(exact_count),
                "exact_config_with_report_count": str(exact_report_count),
                "recommended_run_id": recommended_id,
                "status": status,
                "note": note,
            })
    return rows, status_rows


def tsv_text(rows: list[dict], fields: tuple[str, ...]) -> str:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    writer.writerows({field: row.get(field, "") for field in fields} for row in rows)
    return stream.getvalue()


def output_bundle(rows: list[dict], statuses: list[dict]) -> dict[str, str]:
    config_matched = [row for row in rows if row["config_match"] == "exact"]
    selected = [row for row in rows if row["is_recommended"] == "yes"]
    manifest_fields = (
        "dataset_label", "short_coverage", "method", "run_id", "software_revision",
        "selection_reason", "run_config", "provenance", "report", "resource_log",
        "report_status", "resource_status",
    )
    return {
        "all_candidates.tsv": tsv_text(rows, ALL_FIELDS),
        "config_matched_candidates.tsv": tsv_text(config_matched, ALL_FIELDS),
        "selected_results.tsv": tsv_text(selected, ALL_FIELDS),
        "coverage_method_status.tsv": tsv_text(statuses, STATUS_FIELDS),
        "run_manifest.tsv": tsv_text(selected, manifest_fields),
    }


def write_or_check(output_root: Path, bundles: dict[str, dict[str, str]], check_only: bool) -> None:
    failures = []
    for dataset_label, files in bundles.items():
        destination = output_root / dataset_label
        if check_only:
            for name, expected in files.items():
                path = destination / name
                if not path.is_file() or path.read_text() != expected:
                    failures.append(str(path))
            continue
        destination.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".coverage_collect.", dir=destination) as temporary:
            temporary_path = Path(temporary)
            for name, content in files.items():
                (temporary_path / name).write_text(content)
            for name in files:
                os.replace(temporary_path / name, destination / name)
    if failures:
        raise ValueError("generated outputs differ or are missing: " + ", ".join(failures))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=BENCHMARK / "results/coverage_depths")
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument(
        "--datasets",
        nargs="+",
        choices=tuple(DATASETS),
        default=tuple(DATASETS),
        help="dataset bundles to collect (default: all)",
    )
    args = parser.parse_args()

    bundles = {}
    for dataset_label in args.datasets:
        spec = DATASETS[dataset_label]
        rows, statuses = discover_candidates(dataset_label, spec)
        bundles[dataset_label] = output_bundle(rows, statuses)
        selected = sum(row["is_recommended"] == "yes" for row in rows)
        missing = sum(row["status"] != "selected" for row in statuses)
        print(f"{dataset_label}: {len(rows)} candidates, {selected} selected, {missing} missing coverage-method cells")
    write_or_check(args.output_root, bundles, args.check_only)
    print("Check passed" if args.check_only else f"Wrote {args.output_root}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError) as exc:
        print(f"collect_results: error: {exc}", file=sys.stderr)
        raise SystemExit(2)
