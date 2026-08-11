#!/usr/bin/env python3
"""Collect the raw-read UC baseline from completed HiFiEval evaluations.

For uncorrected reads, every error relative to the simulation truth remains
uncorrected. Therefore raw UC equals HiFiEval's raw_errors count, while OC and
CC are not applicable because no correction operation was performed.
"""

import argparse
import csv
from pathlib import Path


ERROR_TYPES = ("all", "insertion", "deletion", "mismatch")


def read_raw_errors(path):
    with path.open(newline="") as handle:
        rows = csv.DictReader(handle, delimiter="\t")
        result = {
            row["error_type"]: int(row["raw_errors"])
            for row in rows
            if row["chrName"] == "all" and row["error_type"] in ERROR_TYPES
        }
    missing = set(ERROR_TYPES) - set(result)
    if missing:
        raise ValueError(f"{path}: missing aggregate error types {sorted(missing)}")
    return result


def collect_and_validate(results_dir):
    observations = {}
    for method_dir in sorted(results_dir.iterdir()):
        if not method_dir.is_dir():
            continue
        path = method_dir / "unfiltered" / f"{method_dir.name}.base.eval.tsv"
        if path.is_file():
            observations[method_dir.name] = read_raw_errors(path)
    if not observations:
        raise ValueError(f"{results_dir}: no completed HiFiEval base tables found")

    method_names = sorted(observations)
    baseline = observations[method_names[0]]
    for method in method_names[1:]:
        if observations[method] != baseline:
            differences = {
                error_type: (baseline[error_type], observations[method][error_type])
                for error_type in ERROR_TYPES
                if baseline[error_type] != observations[method][error_type]
            }
            raise ValueError(
                f"raw error counts disagree for {method}: {differences}; "
                "the methods may not share the same raw-read input"
            )
    return baseline, method_names


def write_output(path, counts):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(("error_type", "OC", "UC", "CC"))
        for error_type in ERROR_TYPES:
            writer.writerow((error_type, "NA", counts[error_type], "NA"))


def main():
    parser = argparse.ArgumentParser(
        description="Collect the raw-read UC baseline from HiFiEval base tables"
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=Path("benchmark/results/hifieval/ecoli3_20x"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("benchmark/results/hifieval/ecoli3_20x/raw_uc.tsv"),
    )
    args = parser.parse_args()

    counts, methods = collect_and_validate(args.results_dir)
    write_output(args.output, counts)
    print(f"Validated identical raw counts across {len(methods)} methods")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
