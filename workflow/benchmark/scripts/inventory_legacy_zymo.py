#!/usr/bin/env python3
"""Create a read-only inventory of the legacy Zymo result directory."""

from __future__ import annotations

import argparse
import csv
import re
from datetime import datetime
from pathlib import Path


DEFAULT_SOURCE = Path("/home/yczhang/zyc/final_result/zymo")
DEFAULT_OUTPUT = Path("benchmark/source_inventory/zymo")

QUAST_FIELDS = (
    "Assembly",
    "# contigs",
    "Largest contig",
    "Total length",
    "Reference length",
    "N50",
    "# misassemblies",
    "# local misassemblies",
    "Unaligned length",
    "Genome fraction (%)",
    "Duplication ratio",
    "# mismatches per 100 kbp",
    "# indels per 100 kbp",
    "Total aligned length",
)


def classify_path(relative_path: Path) -> tuple[str, str]:
    posix = relative_path.as_posix()
    name = relative_path.name
    suffix = relative_path.suffix.lower()

    if "trashme_" in posix:
        return "temporary", "BCALM/super-k-mer partition"
    if "/beifen/" in f"/{posix}" or posix.startswith("zymo_cor/beifen/"):
        return "backup", "legacy backup copy"
    if posix.startswith("data/ref/"):
        return "reference", "per-species or merged reference"
    if posix.startswith("data/"):
        if suffix in {".fa", ".fasta", ".fna", ".fq", ".fastq"}:
            return "input", "read/reference sequence input"
        if suffix in {".h5", ".npy"} or "_k" in name:
            return "intermediate", "index or k-mer intermediate"
        return "input_metadata", "input QC or metadata"
    if posix.startswith("zymo_cor/coverage_self/"):
        return "coverage_experiment", "5/10/20/30/40 subsampling experiment"
    if posix.startswith("zymo_cor/assambly/canu/"):
        return "assembly_canu", "Canu assembly or QUAST report"
    if posix.startswith("zymo_cor/assambly/hifiasm/"):
        return "assembly_hifiasm", "hifiasm assembly QUAST report"
    if suffix == ".sh":
        return "script", "legacy command script"
    if name in {"tmp_DADEC1.fa", "overlap.paf", "short.npy", "timetest.fa"}:
        return "intermediate", "large temporary or diagnostic artifact"
    if suffix in {".fa", ".fasta", ".fna", ".fq", ".fastq"}:
        return "corrected_reads", "corrected long-read output"
    if suffix in {".txt", ".csv", ".log"}:
        return "evaluation_or_log", "QUAST evaluation, resource report, or log"
    return "other", "unclassified artifact"


def parse_quast(path: Path) -> dict[str, str] | None:
    try:
        text = path.read_text(errors="replace")
    except OSError:
        return None
    if not text.startswith("All statistics are based on contigs"):
        return None

    values: dict[str, str] = {}
    for line in text.splitlines():
        parts = re.split(r"\s{2,}", line.strip(), maxsplit=1)
        if len(parts) == 2:
            values[parts[0]] = parts[1]
    return {field: values.get(field, "") for field in QUAST_FIELDS}


def infer_method(name: str) -> str:
    lower = name.lower()
    if "dadec" in lower:
        return "DADEC"
    if "dechat" in lower:
        return "DeChat"
    if "vechat" in lower:
        return "VeChat"
    if "f_hero" in lower:
        return "F_HERO"
    if "r_hero" in lower:
        return "R_HERO"
    if "l_hero" in lower:
        return "L_HERO"
    if "fmlrc" in lower:
        return "FMLRC"
    if "ratatosk" in lower:
        return "Ratatosk"
    if "lordec" in lower:
        return "LoRDEC"
    if "colormap" in lower:
        return "CoLoRMap"
    if "proovread" in lower:
        return "proovread"
    if "long_reads" in lower:
        return "Raw"
    return ""


def infer_scope(relative_path: Path) -> str:
    posix = relative_path.as_posix()
    if posix.startswith("zymo_cor/coverage_self/"):
        return "long_read_subsampling"
    if posix.startswith("zymo_cor/assambly/canu/"):
        return "canu_assembly"
    if posix.startswith("zymo_cor/assambly/hifiasm/"):
        return "hifiasm_assembly"
    if posix.startswith("data/"):
        return "raw_reads"
    if "/beifen/" in f"/{posix}":
        return "backup"
    return "corrected_reads"


def write_tsv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fieldnames, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    source = args.source.resolve()
    output = args.output.resolve()
    if not source.is_dir():
        raise SystemExit(f"Source directory does not exist: {source}")

    manifest_rows: list[dict[str, object]] = []
    quast_rows: list[dict[str, object]] = []

    for path in sorted(source.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(source)
        category, note = classify_path(relative)
        stat = path.stat()
        manifest_rows.append(
            {
                "relative_path": relative.as_posix(),
                "size_bytes": stat.st_size,
                "modified_time_iso": datetime.fromtimestamp(stat.st_mtime).astimezone().isoformat(),
                "category": category,
                "note": note,
            }
        )

        if path.suffix.lower() != ".txt":
            continue
        metrics = parse_quast(path)
        if metrics is None:
            continue
        row: dict[str, object] = {
            "relative_path": relative.as_posix(),
            "scope": infer_scope(relative),
            "method": infer_method(path.stem),
        }
        row.update(metrics)
        quast_rows.append(row)

    write_tsv(
        output / "source_files.tsv",
        ["relative_path", "size_bytes", "modified_time_iso", "category", "note"],
        manifest_rows,
    )
    write_tsv(
        output / "quast_metrics.tsv",
        ["relative_path", "scope", "method", *QUAST_FIELDS],
        quast_rows,
    )

    full_bases = 14_382_711_098
    reference_bases = 76_778_694
    coverage_rows: list[dict[str, object]] = []
    primary_pattern = re.compile(
        r"^(5|10|20|30|40)_(DADEC_k49_a21_s1|dechat|vechat)\.txt$"
    )
    for row in quast_rows:
        relative = Path(str(row["relative_path"]))
        if relative.parent.as_posix() != "zymo_cor/coverage_self":
            continue
        match = primary_pattern.match(relative.name)
        if not match:
            continue
        fraction = int(match.group(1))
        coverage_rows.append(
            {
                "sample_label": fraction,
                "interpretation": f"{fraction}% of full long-read set",
                "estimated_raw_depth_x": f"{full_bases / reference_bases * fraction / 100:.2f}",
                "method": row["method"],
                "contigs_or_reads": row["# contigs"],
                "genome_fraction_pct": row["Genome fraction (%)"],
                "duplication_ratio": row["Duplication ratio"],
                "mismatches_per_100_kbp": row["# mismatches per 100 kbp"],
                "indels_per_100_kbp": row["# indels per 100 kbp"],
                "misassemblies": row["# misassemblies"],
                "local_misassemblies": row["# local misassemblies"],
                "source_report": row["relative_path"],
            }
        )
    coverage_rows.sort(key=lambda row: (int(row["sample_label"]), str(row["method"])))
    write_tsv(
        output / "coverage_summary.tsv",
        [
            "sample_label",
            "interpretation",
            "estimated_raw_depth_x",
            "method",
            "contigs_or_reads",
            "genome_fraction_pct",
            "duplication_ratio",
            "mismatches_per_100_kbp",
            "indels_per_100_kbp",
            "misassemblies",
            "local_misassemblies",
            "source_report",
        ],
        coverage_rows,
    )

    primary_reports = {
        "data/long_reads_10_quast.txt",
        "zymo_cor/10_DADEC_k49_a21_s1.txt",
        "zymo_cor/fmlrc1.txt",
        "zymo_cor/F_HERO.txt",
        "zymo_cor/ratatosk1.txt",
        "zymo_cor/R_HERO.txt",
        "zymo_cor/lordec1.txt",
        "zymo_cor/L_HERO.txt",
        "zymo_cor/colormap_sp.txt",
        "zymo_cor/proovread.txt",
    }
    correction_rows = [
        row for row in quast_rows if str(row["relative_path"]) in primary_reports
    ]
    method_order = {
        "Raw": 0,
        "DADEC": 1,
        "FMLRC": 2,
        "F_HERO": 3,
        "Ratatosk": 4,
        "R_HERO": 5,
        "LoRDEC": 6,
        "L_HERO": 7,
        "CoLoRMap": 8,
        "proovread": 9,
    }
    correction_rows.sort(key=lambda row: method_order.get(str(row["method"]), 99))
    write_tsv(
        output / "correction_summary.tsv",
        ["relative_path", "scope", "method", *QUAST_FIELDS],
        correction_rows,
    )

    print(f"source_files={len(manifest_rows)}")
    print(f"quast_reports={len(quast_rows)}")
    print(f"coverage_rows={len(coverage_rows)}")
    print(f"correction_rows={len(correction_rows)}")
    print(f"output={output}")


if __name__ == "__main__":
    main()
