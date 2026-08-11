#!/usr/bin/env python3
"""Run HiFiEval on raw reads to generate the raw UC baseline from scratch.

The raw truth PAF is supplied as both the pre-correction and post-correction
alignment. No correct-correction (CC) or over-correction (OC) event can be
created. HiFiEval's UC is position-deduplicated, whereas ``raw_errors`` retains
the original error-event multiplicity. The legacy supplementary table placed
``raw_errors`` in the Raw/UC cell, so both quantities are reported explicitly.
"""

import argparse
import csv
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "benchmark" / "scripts"))

from run_hifieval_eval import load_config  # noqa: E402


ERROR_TYPES = ("all", "insertion", "deletion", "mismatch")


def validate_raw_baseline(base_eval):
    with base_eval.open(newline="") as handle:
        rows = {
            row["error_type"]: row
            for row in csv.DictReader(handle, delimiter="\t")
            if row["chrName"] == "all"
        }
    missing = set(ERROR_TYPES) - set(rows)
    if missing:
        raise ValueError(f"{base_eval}: missing error types {sorted(missing)}")

    for error_type in ERROR_TYPES:
        row = rows[error_type]
        raw_errors = int(row["raw_errors"])
        corrected_errors = int(row["corrected_errors"])
        oc = int(row["oc"])
        cc = int(row["cc"])
        if (corrected_errors, oc, cc) != (raw_errors, 0, 0):
            raise ValueError(
                f"unexpected raw baseline for {error_type}: "
                f"raw={raw_errors}, corrected={corrected_errors}, "
                f"OC={oc}, CC={cc}"
            )
    return rows


def write_summary(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(
            (
                "error_type",
                "OC",
                "table_raw_UC",
                "hifieval_deduplicated_UC",
                "CC",
            )
        )
        for error_type in ERROR_TYPES:
            writer.writerow(
                (
                    error_type,
                    0,
                    rows[error_type]["raw_errors"],
                    rows[error_type]["uc"],
                    0,
                )
            )


def main():
    parser = argparse.ArgumentParser(
        description="Run HiFiEval with the raw truth PAF as both inputs"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=PROJECT_ROOT
        / "benchmark/config/runs/ecoli3/hifieval/20x_dadec_hifieval.yaml",
        help="Any HiFiEval config for the dataset; only raw_paf, reference and hifieval are used",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "benchmark/results/hifieval/ecoli3_20x/raw_baseline",
    )
    parser.add_argument(
        "--reuse-existing",
        action="store_true",
        help="validate an existing raw.base.eval.tsv without rerunning HiFiEval",
    )
    args = parser.parse_args()

    config = load_config(args.config.resolve())
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    prefix = output_dir / "raw"

    command = [
        sys.executable,
        str(config.hifieval),
        "-o",
        str(prefix),
        "-r",
        str(config.raw_paf),
        "-c",
        str(config.raw_paf),
        "-h",
        str(config.reference),
    ]
    log_path = output_dir / "run.log"
    base_eval = prefix.with_suffix(".base.eval.tsv")
    if args.reuse_existing:
        if not base_eval.is_file():
            raise FileNotFoundError(f"cannot reuse missing output: {base_eval}")
        print(f"Reusing existing HiFiEval output: {base_eval}", flush=True)
    else:
        print("Running:", " ".join(command), flush=True)
        with log_path.open("w") as log_handle:
            subprocess.run(
                command,
                check=True,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
            )

    rows = validate_raw_baseline(base_eval)
    summary = output_dir / "raw_uc.tsv"
    write_summary(summary, rows)
    print(f"Validated raw baseline: {base_eval}")
    print(f"Wrote {summary}")
    print(f"Full HiFiEval log: {log_path}")


if __name__ == "__main__":
    main()
