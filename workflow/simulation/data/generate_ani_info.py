#!/usr/bin/env python3
"""Generate ani_info.tsv from an existing fastANI matrix.

The output mANI is the largest ANI observed between each genome and any other
genome in the matrix.  Entries for which fastANI found no valid comparison are
reported as NA.
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


ACCESSION_RE = re.compile(r"(GC[AF]_\d+\.\d+)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "dataset_dir",
        type=Path,
        help="Dataset directory containing out.matrix and sim_genomes_info.txt",
    )
    parser.add_argument(
        "--matrix",
        type=Path,
        help="fastANI matrix (default: DATASET_DIR/out.matrix)",
    )
    parser.add_argument(
        "--metadata",
        type=Path,
        help="Genome metadata (default: DATASET_DIR/sim_genomes_info.txt)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output path (default: DATASET_DIR/ani_info.tsv)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the output if it already exists",
    )
    return parser.parse_args()


def load_species(metadata_path: Path) -> dict[str, str]:
    with metadata_path.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        required = {"id", "organism_name"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError(
                f"{metadata_path} must contain columns: {', '.join(sorted(required))}"
            )
        return {row["id"]: row["organism_name"] for row in reader}


def accession_from_path(genome_path: str) -> str:
    match = ACCESSION_RE.search(Path(genome_path).name)
    if not match:
        raise ValueError(f"Cannot extract GCF/GCA accession from: {genome_path}")
    return match.group(1)


def load_matrix(matrix_path: Path) -> tuple[list[str], list[list[float | None]]]:
    with matrix_path.open() as handle:
        first_line = handle.readline().strip()
        try:
            expected_count = int(first_line)
        except ValueError as exc:
            raise ValueError(f"Invalid fastANI matrix header in {matrix_path}") from exc

        genomes: list[str] = []
        lower_rows: list[list[float | None]] = []
        for line_number, line in enumerate(handle, start=2):
            fields = line.rstrip("\n").split("\t")
            if not fields or not fields[0]:
                raise ValueError(f"Missing genome path at {matrix_path}:{line_number}")
            values = [None if value == "NA" else float(value) for value in fields[1:]]
            if len(values) != len(genomes):
                raise ValueError(
                    f"Malformed triangular matrix at {matrix_path}:{line_number}: "
                    f"expected {len(genomes)} ANI values, found {len(values)}"
                )
            genomes.append(fields[0])
            lower_rows.append(values)

    if len(genomes) != expected_count:
        raise ValueError(
            f"Matrix header says {expected_count} genomes, but found {len(genomes)}"
        )
    return genomes, lower_rows


def maximum_ani(lower_rows: list[list[float | None]]) -> list[float | None]:
    maxima: list[float | None] = [None] * len(lower_rows)
    for row_index, values in enumerate(lower_rows):
        for column_index, value in enumerate(values):
            if value is None:
                continue
            for index in (row_index, column_index):
                if maxima[index] is None or value > maxima[index]:
                    maxima[index] = value
    return maxima


def main() -> None:
    args = parse_args()
    dataset_dir = args.dataset_dir.resolve()
    matrix_path = (args.matrix or dataset_dir / "out.matrix").resolve()
    metadata_path = (args.metadata or dataset_dir / "sim_genomes_info.txt").resolve()
    output_path = (args.output or dataset_dir / "ani_info.tsv").resolve()

    if output_path.exists() and not args.force:
        raise FileExistsError(f"Refusing to overwrite {output_path}; use --force")

    species_by_path = load_species(metadata_path)
    genomes, lower_rows = load_matrix(matrix_path)
    maxima = maximum_ani(lower_rows)

    missing_metadata = [path for path in genomes if path not in species_by_path]
    if missing_metadata:
        preview = "\n".join(missing_metadata[:5])
        raise ValueError(f"Genome paths missing from {metadata_path}:\n{preview}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(["Strain ID", "SpeciesNames", "mANI"])
        for genome, value in zip(genomes, maxima):
            writer.writerow(
                [
                    accession_from_path(genome),
                    species_by_path[genome],
                    "NA" if value is None or value == 0 else str(value),
                ]
            )

    print(f"Wrote {len(genomes)} genome records to {output_path}")


if __name__ == "__main__":
    main()
