#!/usr/bin/env python3
"""Collect reproducible Centrifuge classification metrics for 30S-UA."""
from __future__ import annotations

import csv
import io
import json
import os
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[2]
SOURCE = ROOT / "benchmark/results/classification/30strains_legacy"
DEST = ROOT / "benchmark/results/classification/30strains_legacy_collected"
COVERAGES = ("10x", "20x", "30x", "40x", "50x")
METHODS = {
    "dadec_dev": ("DADEC", "dadec_dev"),
    "fmlrc_current": ("FMLRC", "fmlrc_current"),
    "f_hero": ("F_HERO", "f_hero"),
    "ratatosk": ("Ratatosk", "ratatosk"),
    "r_hero": ("R_HERO", "r_hero"),
    "lordec": ("LoRDEC", "lordec"),
    "l_hero": ("L_HERO", "l_hero"),
    "colormap": ("CoLoRMap", "colormap"),
    "proovread": ("Proovread", "proovread"),
}
METRICS = ("precision", "recall", "accuracy", "F1", "macro_precision", "macro_recall", "macro_F1", "micro_precision", "micro_recall", "micro_F1", "micro_accuracy", "total_assignments")
FIELDS = ("coverage", "method", "method_dir", "status", *METRICS, "metrics_json", "report", "assignments", "provenance")

def rel(path: Path) -> str:
    return os.fspath(path.relative_to(ROOT)) if path.exists() else ""

def collect() -> list[dict[str, str]]:
    rows = []
    for coverage in COVERAGES:
        for method_dir, (method, _) in METHODS.items():
            base = SOURCE / coverage / method_dir
            metrics_path = base / "metrics.json"
            report = base / "report.tsv"
            assignments = base / "assignments.tsv"
            provenance = base / "provenance.json"
            row = {field: "" for field in FIELDS}
            row.update({"coverage": coverage, "method": method, "method_dir": method_dir, "metrics_json": rel(metrics_path), "report": rel(report), "assignments": rel(assignments), "provenance": rel(provenance)})
            if metrics_path.is_file():
                data = json.loads(metrics_path.read_text())
                row["status"] = str(data.get("status", "ok"))
                for key in METRICS:
                    if key in data:
                        row[key] = str(data[key])
            else:
                row["status"] = "missing_metrics"
            rows.append(row)
    return rows

def write(rows: list[dict[str, str]], path: Path, fields=FIELDS) -> None:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    writer.writerows({field: row.get(field, "") for field in fields} for row in rows)
    path.write_text(stream.getvalue())

def main() -> int:
    rows = collect()
    DEST.mkdir(parents=True, exist_ok=True)
    write(rows, DEST / "all_candidates.tsv")
    selected = [r for r in rows if r["status"] == "ok"]
    write(selected, DEST / "selected_results.tsv")
    status_rows = []
    for coverage in COVERAGES:
        for method_dir, (method, _) in METHODS.items():
            row = next(r for r in rows if r["coverage"] == coverage and r["method_dir"] == method_dir)
            status_rows.append({"coverage": coverage, "method": method, "status": row["status"], "selected_method_dir": method_dir, "metrics_json": row["metrics_json"]})
    write(status_rows, DEST / "coverage_method_status.tsv", ("coverage", "method", "status", "selected_method_dir", "metrics_json"))
    write(selected, DEST / "run_manifest.tsv", ("coverage", "method", "method_dir", "metrics_json", "report", "assignments", "provenance"))
    print(f"Collected {len(selected)}/{len(rows)} coverage-method results into {DEST}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
