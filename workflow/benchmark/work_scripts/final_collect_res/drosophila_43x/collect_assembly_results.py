#!/usr/bin/env python3
"""Collect QUAST and resource results from the Drosophila 43x assemblies."""

from __future__ import annotations

import csv
import io
import os
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[3]
ASSEMBLY_ROOT = ROOT / "benchmark/runs/drosophila_43x/assembly"
RESULT_ROOT = ROOT / "benchmark/results/drosophila_43x/assembly"
METHODS = {
    "dadec": "DADEC",
    "fmlrc": "FMLRC",
    "f_hero": "F_HERO",
    "ratatosk": "Ratatosk",
    "r_hero": "R_HERO",
    "lordec": "LoRDEC",
    "l_hero": "L_HERO",
    "colormap": "CoLoRMap",
    "proovread": "Proovread",
}
METRICS = (
    ("mismatches_per_100_kbp", "# mismatches per 100 kbp"),
    ("indels_per_100_kbp", "# indels per 100 kbp"),
    ("haplotype_coverage_percent", "Genome fraction (%)"),
    ("local_misassemblies", "# misassemblies"),
    ("nga50_kbp", "NGA50"),
    ("contigs_number", "# contigs (>= 0 bp)"),
    ("total_length_bp", "Total length (>= 0 bp)"),
)
FIELDS = (
    "method", "assembler", "report_status", "resource_status", *[x[0] for x in METRICS],
    "quast_report", "resource_log", "provenance",
)


def parse_report(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    with path.open() as handle:
        for row in csv.reader(handle, delimiter="\t"):
            if len(row) >= 2:
                values.setdefault(row[0], row[1])
    return values


def relative(path: Path) -> str:
    return os.fspath(path.relative_to(ROOT)) if path.exists() else ""


def collect() -> list[dict[str, str]]:
    rows = []
    for method_dir, method in METHODS.items():
        method_root = ASSEMBLY_ROOT / method_dir
        for assembler in ("hifiasm", "canu"):
            assembly_root = method_root / assembler
            report = assembly_root / "quast/report.tsv"
            resource_candidates = sorted((assembly_root / "resources").glob("*.time.txt"))
            resource = resource_candidates[0] if resource_candidates else assembly_root / "resources/missing.time.txt"
            provenance = assembly_root / "provenance.json"
            row = {field: "" for field in FIELDS}
            row.update({
                "method": method,
                "assembler": assembler,
                "report_status": "present" if report.is_file() else "missing",
                "resource_status": "present" if resource.is_file() else "missing",
                "quast_report": relative(report),
                "resource_log": relative(resource),
                "provenance": relative(provenance),
            })
            if report.is_file():
                metrics = parse_report(report)
                for field, key in METRICS:
                    row[field] = metrics.get(key, "")
            rows.append(row)
    return rows


def tsv(rows: list[dict[str, str]]) -> str:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=FIELDS, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def write(rows: list[dict[str, str]], name: str, subset: list[dict[str, str]]) -> None:
    path = RESULT_ROOT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(tsv(subset))


def main() -> int:
    rows = collect()
    write(rows, "all_assembly_results.tsv", rows)
    write(rows, "hifiasm_results.tsv", [r for r in rows if r["assembler"] == "hifiasm"])
    write(rows, "canu_results.tsv", [r for r in rows if r["assembler"] == "canu"])
    manifest_fields = ("method", "assembler", "quast_report", "resource_log", "provenance", "report_status", "resource_status")
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=manifest_fields, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    writer.writerows({field: row[field] for field in manifest_fields} for row in rows)
    (RESULT_ROOT / "run_manifest.tsv").write_text(stream.getvalue())
    complete = sum(r["report_status"] == "present" for r in rows)
    print(f"Collected {complete}/{len(rows)} assembler evaluations into {RESULT_ROOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
