#!/usr/bin/env python3
"""Recalculate error rates for data/errors_ecoli3_readcount without overwrites."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from evaluate_dataset_error import DEFAULT_MINIMAP2, evaluate


DEFAULT_DATA_DIR = Path(__file__).resolve().parents[3] / "data/errors_ecoli3_readcount"
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "results/ecoli3_readcount_recalculated"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--threads", type=int, default=16)
    parser.add_argument("--minimap2", type=Path, default=DEFAULT_MINIMAP2)
    return parser.parse_args()


def load_manifest(path: Path) -> dict[str, str]:
    with path.open(newline="") as handle:
        reader = csv.reader(handle, delimiter="\t")
        next(reader, None)
        return {row[0]: row[1] for row in reader if len(row) >= 2}


def main() -> None:
    args = parse_args()
    if args.threads < 1:
        raise ValueError("--threads must be positive")
    data_dir = args.data_dir.resolve()
    output_dir = args.output_dir.resolve()
    if output_dir.exists():
        raise FileExistsError(
            f"Refusing to reuse {output_dir}; choose a new --output-dir"
        )
    output_dir.mkdir(parents=True)

    manifest = load_manifest(data_dir / "simulation_manifest.tsv")
    reference = Path(manifest["reference"])
    models = manifest["short_models"].split()
    inputs: list[tuple[str, Path, str]] = []
    for model in models:
        slug = model.lower()
        inputs.append((model, data_dir / slug / f"{slug}_reads.fastq.gz", "sr"))
    inputs.append(
        (
            "PBSIM_P6C4",
            Path(manifest["merged_long_fastq"]),
            "map-pb",
        )
    )

    rows = []
    for name, reads, preset in inputs:
        dataset_id = f"errors_ecoli3_{name.lower()}"
        print(f"Evaluating {name} with {preset} ...", flush=True)
        row = evaluate(
            args.minimap2,
            args.threads,
            dataset_id,
            reads,
            reference,
            preset,
            output_dir / f"{dataset_id}.minimap2.log",
        )
        row = {"model": name, **row}
        rows.append(row)

    output = output_dir / "sequencing_error_rates_recalculated.tsv"
    with output.open("x", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
