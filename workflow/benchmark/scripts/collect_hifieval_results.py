#!/usr/bin/env python3
"""Collect completed per-method Hifieval outputs into one rectangular TSV."""

import argparse
import csv
import json
import os
import sys
from pathlib import Path

from run_hifieval_eval import load_config
from run_hifieval_eval import sha256


METHOD_ORDER = [
    "dadec",
    "fmlrc",
    "f_hero",
    "ratatosk",
    "r_hero",
    "lordec",
    "l_hero",
    "colormap",
    "proovread",
]
REQUIRED_STAGES = {
    "align_corrected",
    "hifieval_unfiltered",
    "readseval_filtered",
}
OUTPUT_COLUMNS = [
    "method",
    "filter_state",
    "raw_errors",
    "corrected_errors",
    "read_oc",
    "read_uc",
    "read_cc",
    "base_oc",
    "base_uc",
    "base_cc",
    "FDR",
    "FNR",
    "TPR",
    "read_mapping_mode",
    "corrected_fasta",
]


def validate_provenance(config):
    complete = config.output_dir / ".complete"
    provenance_path = config.output_dir / "provenance.json"
    if not complete.is_file() or not provenance_path.is_file():
        raise RuntimeError(
            "{} has no completed Hifieval evaluation".format(config.method)
        )
    provenance = json.loads(provenance_path.read_text())
    if provenance.get("status") != "complete":
        raise RuntimeError("{} provenance is not complete".format(config.method))
    if provenance.get("method") != config.method:
        raise RuntimeError("{} provenance method mismatch".format(config.method))
    if provenance.get("read_mapping_mode") != config.read_mapping_mode:
        raise RuntimeError(
            "{} read-mapping mode changed since evaluation".format(config.method)
        )
    stages = provenance.get("stages", {})
    incomplete = sorted(
        stage
        for stage in REQUIRED_STAGES
        if stages.get(stage, {}).get("status") != "complete"
    )
    if incomplete:
        raise RuntimeError(
            "{} missing completed stages: {}".format(
                config.method, ", ".join(incomplete)
            )
        )

    recorded = provenance.get("inputs_and_tools", {})
    config_key = str(config.config_path)
    if config_key not in recorded:
        raise RuntimeError("{} provenance lacks its config".format(config.method))
    if recorded[config_key].get("sha256") != sha256(config.config_path):
        raise RuntimeError(
            "{} config changed since evaluation; rerun it".format(config.method)
        )
    for path_text, metadata in recorded.items():
        path = Path(path_text)
        if not path.is_file():
            raise RuntimeError(
                "{} recorded input is missing: {}".format(config.method, path)
            )
        stat = path.stat()
        if (
            stat.st_size != metadata.get("size")
            or stat.st_mtime_ns != metadata.get("mtime_ns")
        ):
            raise RuntimeError(
                "{} recorded input changed: {}".format(config.method, path)
            )
    return provenance


def read_base_all(path):
    with Path(path).open(newline="") as handle:
        rows = [
            row
            for row in csv.DictReader(handle, delimiter="\t")
            if row["error_type"] == "all" and row["chrName"] == "all"
        ]
    if len(rows) != 1:
        raise ValueError(
            "{} must contain exactly one all/all row".format(path)
        )
    return rows[0]


def read_read_counts(path):
    with Path(path).open(newline="") as handle:
        rows = {
            row["metric"]: row["count"]
            for row in csv.DictReader(handle, delimiter="\t")
        }
    required = {"read_oc", "read_uc", "read_cc"}
    missing = sorted(required.difference(rows))
    if missing:
        raise ValueError(
            "{} lacks metrics: {}".format(path, ", ".join(missing))
        )
    return rows


def collect_config(config):
    validate_provenance(config)
    read_counts = read_read_counts(
        config.output_dir / "filtered" / (config.method + ".read.eval.tsv")
    )
    rows = []
    for state in ("unfiltered", "filtered"):
        base = read_base_all(
            config.output_dir
            / state
            / (config.method + ".base.eval.tsv")
        )
        rows.append(
            {
                "method": config.method,
                "filter_state": state,
                "raw_errors": base["raw_errors"],
                "corrected_errors": base["corrected_errors"],
                "read_oc": read_counts["read_oc"],
                "read_uc": read_counts["read_uc"],
                "read_cc": read_counts["read_cc"],
                "base_oc": base["oc"],
                "base_uc": base["uc"],
                "base_cc": base["cc"],
                "FDR": base["FDR"],
                "FNR": base["FNR"],
                "TPR": base["TPR"],
                "read_mapping_mode": config.read_mapping_mode,
                "corrected_fasta": str(config.corrected_fasta),
            }
        )
    return rows


def config_path(config_dir, config_pattern, method):
    if "{method}" not in config_pattern:
        raise ValueError("--config-pattern must contain {method}")
    return Path(config_dir) / config_pattern.format(method=method)


def collect(config_dir, methods, config_pattern="20x_{method}_hifieval.yaml"):
    config_dir = Path(config_dir)
    rows = []
    for method in methods:
        config = load_config(config_path(config_dir, config_pattern, method))
        if config.method != method:
            raise ValueError(
                "{} config declares method {}".format(method, config.method)
            )
        rows.extend(collect_config(config))
    return rows


def write_summary(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=OUTPUT_COLUMNS, delimiter="\t"
        )
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)


def build_parser():
    parser = argparse.ArgumentParser(
        description="Collect completed multi-method Hifieval evaluations"
    )
    parser.add_argument("--config-dir", required=True)
    parser.add_argument(
        "--config-pattern",
        default="20x_{method}_hifieval.yaml",
        help="config filename pattern containing {method}",
    )
    parser.add_argument("--output", required=True)
    parser.add_argument("--methods", nargs="+", default=METHOD_ORDER)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    unknown = sorted(set(args.methods).difference(METHOD_ORDER))
    if unknown:
        raise ValueError("unknown methods: {}".format(", ".join(unknown)))
    rows = collect(args.config_dir, args.methods, args.config_pattern)
    write_summary(args.output, rows)
    print("Wrote {} rows to {}".format(len(rows), args.output))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError) as exc:
        print("collect_hifieval_results: error: {}".format(exc), file=sys.stderr)
        raise SystemExit(2)
