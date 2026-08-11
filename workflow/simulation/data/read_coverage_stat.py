#!/usr/bin/env python3
"""Calculate sequence coverage of short and/or long reads against a reference."""

from __future__ import annotations

import argparse
import gzip
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO


@dataclass
class SequenceStats:
    records: int = 0
    bases: int = 0
    non_n_bases: int = 0
    min_length: int | None = None
    max_length: int = 0

    def add(self, sequence: str) -> None:
        length = len(sequence)
        self.records += 1
        self.bases += length
        self.non_n_bases += length - sequence.count("N") - sequence.count("n")
        self.min_length = (
            length if self.min_length is None else min(self.min_length, length)
        )
        self.max_length = max(self.max_length, length)

    def merge(self, other: SequenceStats) -> None:
        if other.records == 0:
            return
        self.records += other.records
        self.bases += other.bases
        self.non_n_bases += other.non_n_bases
        self.min_length = (
            other.min_length
            if self.min_length is None
            else min(self.min_length, other.min_length)
        )
        self.max_length = max(self.max_length, other.max_length)


def open_text(path: Path) -> TextIO:
    if path.suffix.lower() == ".gz":
        return gzip.open(path, "rt")
    return path.open("rt")


def detect_format(path: Path) -> str:
    with open_text(path) as handle:
        for line in handle:
            if not line.strip():
                continue
            if line.startswith(">"):
                return "fasta"
            if line.startswith("@"):
                return "fastq"
            break
    raise ValueError(f"Cannot detect FASTA/FASTQ format: {path}")


def fasta_stats(path: Path) -> SequenceStats:
    stats = SequenceStats()
    sequence_parts: list[str] = []

    with open_text(path) as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            if line.startswith(">"):
                if sequence_parts:
                    stats.add("".join(sequence_parts))
                    sequence_parts.clear()
                continue
            if not sequence_parts and stats.records == 0 and line_number == 1:
                raise ValueError(f"Invalid FASTA header in {path}")
            sequence_parts.append(line)

    if sequence_parts:
        stats.add("".join(sequence_parts))
    if stats.records == 0:
        raise ValueError(f"No FASTA records found in {path}")
    return stats


def fastq_stats(path: Path) -> SequenceStats:
    stats = SequenceStats()

    with open_text(path) as handle:
        line_number = 0
        while True:
            header = handle.readline()
            if not header:
                break
            line_number += 1
            if not header.strip():
                continue

            sequence = handle.readline().strip()
            separator = handle.readline()
            quality = handle.readline().strip()
            line_number += 3

            if not header.startswith("@") or not separator.startswith("+"):
                raise ValueError(
                    f"Invalid FASTQ record ending near line {line_number}: {path}"
                )
            if len(sequence) != len(quality):
                raise ValueError(
                    f"Sequence/quality length mismatch near line {line_number}: {path}"
                )
            stats.add(sequence)

    if stats.records == 0:
        raise ValueError(f"No FASTQ records found in {path}")
    return stats


def sequence_stats(path: Path) -> tuple[str, SequenceStats]:
    sequence_format = detect_format(path)
    if sequence_format == "fasta":
        return sequence_format, fasta_stats(path)
    return sequence_format, fastq_stats(path)


def sequence_stats_many(paths: list[Path]) -> tuple[list[str], SequenceStats]:
    formats: list[str] = []
    combined = SequenceStats()
    for path in paths:
        sequence_format, stats = sequence_stats(path)
        formats.append(sequence_format)
        combined.merge(stats)
    return formats, combined


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Calculate short-read, long-read, and combined sequence coverage as "
            "total read bases divided by reference genome length."
        )
    )
    parser.add_argument(
        "-r",
        "--reads",
        "-s",
        "--short-reads",
        dest="short_reads",
        action="append",
        default=[],
        type=Path,
        help=(
            "short reads (FASTA/FASTQ[.gz]); may be repeated for paired or "
            "multiple files"
        ),
    )
    parser.add_argument(
        "-l",
        "--long-reads",
        action="append",
        default=[],
        type=Path,
        help="long reads (FASTA/FASTQ[.gz]); may be repeated",
    )
    parser.add_argument(
        "-g", "--reference", required=True, type=Path, help="reference (FASTA[.gz])"
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="write the tab-separated report to this file instead of stdout",
    )
    return parser.parse_args()


def coverage_rows(
    prefix: str,
    paths: list[Path],
    formats: list[str],
    stats: SequenceStats,
    reference: SequenceStats,
) -> list[tuple[str, str]]:
    mean_read_length = stats.bases / stats.records
    return [
        (f"{prefix}_reads_files", ",".join(map(str, paths))),
        (f"{prefix}_reads_formats", ",".join(formats)),
        (f"{prefix}_read_count", str(stats.records)),
        (f"{prefix}_read_bases", str(stats.bases)),
        (f"{prefix}_mean_read_length_bp", f"{mean_read_length:.3f}"),
        (f"{prefix}_min_read_length_bp", str(stats.min_length)),
        (f"{prefix}_max_read_length_bp", str(stats.max_length)),
        (
            f"{prefix}_coverage_X_non_N_reference",
            f"{stats.bases / reference.non_n_bases:.6f}",
        ),
        (
            f"{prefix}_coverage_X_total_reference",
            f"{stats.bases / reference.bases:.6f}",
        ),
    ]


def main() -> int:
    args = parse_args()
    if not args.short_reads and not args.long_reads:
        raise ValueError(
            "Provide at least one of --short-reads/--reads or --long-reads"
        )

    for path in (*args.short_reads, *args.long_reads, args.reference):
        if not path.is_file():
            raise FileNotFoundError(f"Input file does not exist: {path}")

    reference_format, reference = sequence_stats(args.reference)
    if reference_format != "fasta":
        raise ValueError("Reference input must be FASTA")
    if reference.non_n_bases == 0:
        raise ValueError("Reference contains no effective (non-N) bases")

    reference_rows = [
        ("reference_file", str(args.reference)),
        ("reference_sequences", str(reference.records)),
        ("reference_total_bases", str(reference.bases)),
        ("reference_non_N_bases", str(reference.non_n_bases)),
    ]

    # Keep the original one-short-read report unchanged for existing scripts.
    if len(args.short_reads) == 1 and not args.long_reads:
        reads_format, reads = sequence_stats(args.short_reads[0])
        mean_read_length = reads.bases / reads.records
        rows = [
            ("reads_file", str(args.short_reads[0])),
            ("reference_file", str(args.reference)),
            ("reads_format", reads_format),
            ("read_count", str(reads.records)),
            ("read_bases", str(reads.bases)),
            ("mean_read_length_bp", f"{mean_read_length:.3f}"),
            ("min_read_length_bp", str(reads.min_length)),
            ("max_read_length_bp", str(reads.max_length)),
            ("reference_sequences", str(reference.records)),
            ("reference_total_bases", str(reference.bases)),
            ("reference_non_N_bases", str(reference.non_n_bases)),
            (
                "coverage_X_non_N_reference",
                f"{reads.bases / reference.non_n_bases:.6f}",
            ),
            (
                "coverage_X_total_reference",
                f"{reads.bases / reference.bases:.6f}",
            ),
        ]
    else:
        rows = reference_rows
        combined = SequenceStats()
        if args.short_reads:
            short_formats, short_stats = sequence_stats_many(args.short_reads)
            rows.extend(
                coverage_rows(
                    "short", args.short_reads, short_formats, short_stats, reference
                )
            )
            combined.merge(short_stats)
        if args.long_reads:
            long_formats, long_stats = sequence_stats_many(args.long_reads)
            rows.extend(
                coverage_rows(
                    "long", args.long_reads, long_formats, long_stats, reference
                )
            )
            combined.merge(long_stats)
        rows.extend(
            [
                ("combined_read_count", str(combined.records)),
                ("combined_read_bases", str(combined.bases)),
                (
                    "combined_coverage_X_non_N_reference",
                    f"{combined.bases / reference.non_n_bases:.6f}",
                ),
                (
                    "combined_coverage_X_total_reference",
                    f"{combined.bases / reference.bases:.6f}",
                ),
            ]
        )

    report = "metric\tvalue\n" + "".join(f"{key}\t{value}\n" for key, value in rows)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report)
    else:
        sys.stdout.write(report)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
