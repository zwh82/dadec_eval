#!/usr/bin/env python3
import argparse
import csv
import hashlib
import importlib.util
import json
import statistics
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPT_DIR / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


metaquast = load("parse_metaquast")
resources = load("parse_resources")
METRICS = list(metaquast.LABELS.values())


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_legacy_report(path):
    values = {}
    for line in Path(path).read_text().splitlines():
        for label, field in metaquast.LABELS.items():
            if line.startswith(label) and not line.startswith(label + " ("):
                values[field] = line[len(label):].strip().split()[0]
    missing = [field for field in METRICS if field not in values]
    if missing:
        raise ValueError(f"Historical report is missing: {', '.join(missing)}")
    return {
        field: float(value) if field in {
            "mismatches_per_100_kbp", "indels_per_100_kbp", "haplotype_coverage_percent"
        } else int(value)
        for field, value in values.items()
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--historical", required=True)
    parser.add_argument("--raw", required=True)
    parser.add_argument("--replicates", nargs="+", required=True)
    parser.add_argument("--reports", nargs="+", required=True)
    parser.add_argument("--corrected", nargs="+", required=True)
    parser.add_argument("--resources", nargs="+", required=True)
    parser.add_argument("--table", required=True)
    parser.add_argument("--status", required=True)
    args = parser.parse_args()
    lengths = {len(args.replicates), len(args.reports), len(args.corrected), len(args.resources)}
    if len(lengths) != 1:
        raise ValueError("Replicate input lists must have equal lengths")

    historical = parse_legacy_report(args.historical)
    raw = metaquast.parse_report(args.raw)
    replicate_metrics = [metaquast.parse_report(path) for path in args.reports]
    replicate_hashes = [sha256(path) for path in args.corrected]
    replicate_resources = [resources.parse_resource_text(Path(path).read_text()) for path in args.resources]

    rows = [
        {"source": "historical_k31", "sha256": "NA", **historical},
        {"source": "raw", "sha256": sha256(args.raw), **raw},
    ]
    for replicate, digest, metrics, resource in zip(
        args.replicates, replicate_hashes, replicate_metrics, replicate_resources
    ):
        rows.append({
            "source": f"new_rep{replicate}", "sha256": digest, **metrics,
            "wall_seconds": resource["wall_seconds"],
            "max_rss_kb": resource["max_rss_kb"],
        })

    fields = ["source", "sha256", *METRICS, "wall_seconds", "max_rss_kb"]
    table = Path(args.table)
    table.parent.mkdir(parents=True, exist_ok=True)
    with open(table, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", restval="NA")
        writer.writeheader()
        writer.writerows(rows)

    metrics_repeatable = all(item == replicate_metrics[0] for item in replicate_metrics[1:])
    output_repeatable = len(set(replicate_hashes)) == 1
    historical_match = replicate_metrics[0] == historical
    wall_times = [item["wall_seconds"] for item in replicate_resources]
    mean_wall = statistics.mean(wall_times)
    payload = {
        "metrics_reproducible": metrics_repeatable,
        "byte_for_byte_reproducible": output_repeatable,
        "historical_metrics_exact_match": historical_match,
        "historical_metric_deltas": {
            field: replicate_metrics[0][field] - historical[field] for field in METRICS
        },
        "wall_seconds": wall_times,
        "wall_time_cv_percent": 0.0 if len(wall_times) < 2 or mean_wall == 0 else statistics.stdev(wall_times) / mean_wall * 100,
        "target_metric_reproducibility_pass": metrics_repeatable,
    }
    Path(args.status).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
