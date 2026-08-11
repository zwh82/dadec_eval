#!/usr/bin/env python3
"""Evaluate raw long-read error rates for benchmark dataset YAML files."""

from __future__ import annotations

import argparse
import csv
import gzip
import subprocess
from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MINIMAP2 = Path("/home/wenhai/miniconda3/envs/hero/bin/minimap2")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("configs", nargs="+", type=Path, help="Dataset YAML file(s)")
    parser.add_argument("--threads", type=int, default=16)
    parser.add_argument("--minimap2", type=Path, default=DEFAULT_MINIMAP2)
    parser.add_argument(
        "--output-dir", type=Path, default=Path(__file__).resolve().parent / "results"
    )
    return parser.parse_args()


def resolve_project_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


def load_dataset(config_path: Path) -> tuple[str, Path, Path, str]:
    with config_path.open() as handle:
        config = yaml.safe_load(handle)
    dataset_id = config["dataset"]["id"]
    reads = resolve_project_path(config["inputs"]["long_reads"])
    genome_map = resolve_project_path(config["inputs"]["genome_map"])

    references: list[Path] = []
    with genome_map.open(newline="") as handle:
        for row in csv.reader(handle, delimiter="\t"):
            if len(row) >= 2 and row[1].strip():
                references.append(resolve_project_path(row[1].strip()))
    if len(references) != 1:
        raise ValueError(f"Expected one reference in {genome_map}, found {len(references)}")

    lowered = dataset_id.lower()
    if "ont" in lowered or "nano" in lowered:
        preset = "map-ont"
    elif "pac" in lowered or "pb" in lowered:
        preset = "map-pb"
    else:
        raise ValueError(f"Cannot infer minimap2 preset from dataset id: {dataset_id}")
    return dataset_id, reads, references[0], preset


def open_text(path: Path):
    return gzip.open(path, "rt") if path.suffix == ".gz" else path.open()


def count_reads(path: Path) -> int:
    with open_text(path) as handle:
        first = handle.read(1)
        handle.seek(0)
        if first == ">":
            return sum(line.startswith(">") for line in handle)
        if first == "@":
            lines = sum(1 for _ in handle)
            if lines % 4:
                raise ValueError(f"FASTQ line count is not divisible by four: {path}")
            return lines // 4
    raise ValueError(f"Unrecognized FASTA/FASTQ format: {path}")


def evaluate(
    minimap2: Path,
    threads: int,
    dataset_id: str,
    reads: Path,
    reference: Path,
    preset: str,
    log_path: Path,
) -> dict[str, str | int]:
    for label, path in (("reads", reads), ("reference", reference)):
        if not path.is_file():
            raise FileNotFoundError(f"{label} file is not readable: {path}")

    total_reads = count_reads(reads)
    command = [
        # -c requests base-level alignment.  Without it, PAF columns 10/11 are
        # chaining estimates and must not be used to calculate sequencing error.
        str(minimap2), "-x", preset, "-c", "--secondary=no", "-t", str(threads),
        str(reference), str(reads),
    ]
    aligned_queries: set[str] = set()
    alignment_records = matching_bases = block_bases = 0

    with log_path.open("w") as log_handle:
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=log_handle, text=True, bufsize=1
        )
        assert process.stdout is not None
        for line_number, line in enumerate(process.stdout, start=1):
            fields = line.rstrip("\n").split("\t")
            if len(fields) < 12:
                process.kill()
                raise ValueError(f"Malformed PAF record {line_number} for {dataset_id}")
            alignment_records += 1
            aligned_queries.add(fields[0])
            matching_bases += int(fields[9])
            block_bases += int(fields[10])
        return_code = process.wait()
    if return_code:
        raise RuntimeError(f"minimap2 failed for {dataset_id}; see {log_path}")
    if block_bases == 0:
        raise RuntimeError(f"No aligned bases for {dataset_id}; see {log_path}")

    aligned_reads = len(aligned_queries)
    return {
        "dataset": dataset_id,
        "preset": preset,
        "total_reads": total_reads,
        "aligned_reads": aligned_reads,
        "alignment_rate": f"{aligned_reads / total_reads:.10f}",
        "alignment_records": alignment_records,
        "matching_bases": matching_bases,
        "alignment_block_bases": block_bases,
        "error_rate": f"{1.0 - matching_bases / block_bases:.10f}",
        "error_rate_percent": f"{100.0 * (1.0 - matching_bases / block_bases):.6f}",
        "reads": str(reads),
        "reference": str(reference),
    }


def main() -> None:
    args = parse_args()
    if args.threads < 1:
        raise ValueError("--threads must be positive")
    if not args.minimap2.is_file():
        raise FileNotFoundError(f"minimap2 not found: {args.minimap2}")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for config_path in args.configs:
        dataset_id, reads, reference, preset = load_dataset(config_path.resolve())
        print(f"Evaluating {dataset_id} with {preset} ...", flush=True)
        rows.append(
            evaluate(
                args.minimap2, args.threads, dataset_id, reads, reference, preset,
                args.output_dir / f"{dataset_id}.minimap2.log",
            )
        )

    output = args.output_dir / "long_read_error_rates.tsv"
    with output.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
