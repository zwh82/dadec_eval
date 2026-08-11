#!/usr/bin/env python3
"""Collect E. coli short-read-quality sensitivity results.

The dataset YAML uses 20x--23x as technology identifiers.  The simulation
manifest shows that every short-read dataset is actually 30x, so this script
keeps both fields and never reports the identifier as biological coverage.
"""

from __future__ import annotations

import argparse
import csv
import io
import sys
from pathlib import Path


TECHNOLOGY_BY_KEY = {
    "20x": "MiSeq",
    "21x": "NextSeq",
    "22x": "NovaSeq",
    "23x": "HiSeq",
}
STRICT_AMBIGUITY = 0.9999


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def number(value: str, default: float = float("inf")) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def revision(run_id: str) -> str:
    if "_dev_fix_a_" in run_id:
        return "dev_fix_a"
    if "_dev_fix_" in run_id:
        return "dev_fix"
    return "original"


def render(rows: list[dict[str, object]], fields: list[str]) -> str:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    writer.writerows({field: row.get(field, "") for field in fields} for row in rows)
    return buffer.getvalue()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true", help="fail if outputs differ from source data")
    parser.add_argument("--summary-path", type=Path, help="override the all-parameter summary input")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    script_dir = Path(__file__).resolve().parent
    root = script_dir.parents[3]
    results_dir = root / "benchmark/results"
    output_dir = results_dir / "ecoli3_error_readcount_quality"
    summary_path = args.summary_path or results_dir / "ecoli3_error_readcount_all_parameter_runs.tsv"
    quality_path = root / "data/errors_ecoli3_readcount/sequencing_error_rates.tsv"

    if not summary_path.exists() or not quality_path.exists():
        missing = [str(path) for path in (summary_path, quality_path) if not path.exists()]
        raise SystemExit("Missing required input(s): " + ", ".join(missing))

    quality = {row["model"]: row for row in read_tsv(quality_path)}
    candidates: list[dict[str, object]] = []
    for row in read_tsv(summary_path):
        coverage_key = row["short_coverage"]
        technology = TECHNOLOGY_BY_KEY.get(coverage_key)
        if technology is None:
            raise SystemExit(f"Unexpected short-coverage identifier {coverage_key!r} in {row['run_id']}")
        metadata = quality.get(technology)
        if metadata is None:
            raise SystemExit(f"Missing sequencing-quality metadata for {technology}")
        if metadata["coverage"] != "30":
            raise SystemExit(f"Expected actual 30x short-read coverage for {technology}, got {metadata['coverage']}")

        item: dict[str, object] = dict(row)
        item.update(
            technology=technology,
            config_coverage_key=coverage_key,
            actual_short_coverage=f"{metadata['coverage']}x",
            short_read_length_bp=metadata["read_length"],
            requested_reads=metadata["requested_reads"],
            aligned_reads=metadata["aligned_reads"],
            short_read_error_rate=metadata["recalculated_error_rate"],
            short_read_error_percent=f"{100 * float(metadata['recalculated_error_rate']):.6f}",
            original_short_read_error_rate=metadata["error_rate"],
            original_short_read_error_percent=f"{100 * float(metadata['error_rate']):.6f}",
            dadec_revision=revision(row["run_id"]),
            residual_errors_per_100_kbp=f"{number(row['mismatches_per_100_kbp']) + number(row['indels_per_100_kbp']):.2f}",
            is_strict_ambiguity="yes" if abs(number(row["ambiguity_score"]) - STRICT_AMBIGUITY) < 1e-8 else "no",
        )
        candidates.append(item)

    strict = [row for row in candidates if row["is_strict_ambiguity"] == "yes"]
    grouped: dict[tuple[str, str], list[dict[str, object]]] = {}
    for row in strict:
        grouped.setdefault((str(row["technology"]), str(row["method"])), []).append(row)

    selected: list[dict[str, object]] = []
    revision_order = {"dev_fix_a": 0, "dev_fix": 1, "original": 2}
    for key, rows in grouped.items():
        rows.sort(
            key=lambda row: (
                revision_order.get(str(row["dadec_revision"]), 9) if row["method"] == "DADEC" else 0,
                number(str(row["residual_errors_per_100_kbp"])),
                -number(str(row["haplotype_coverage_percent"]), default=-float("inf")),
                str(row["run_id"]),
            )
        )
        chosen = dict(rows[0])
        chosen["selection_reason"] = (
            "strict ambiguity; prefer current dev_fix_a revision; then lowest residual error"
            if chosen["method"] == "DADEC"
            else "strict ambiguity; lowest residual error"
        )
        selected.append(chosen)

    selected.sort(key=lambda row: (number(str(row["short_read_error_rate"])), str(row["method"])))
    candidates.sort(key=lambda row: (number(str(row["short_read_error_rate"])), str(row["method"]), -number(str(row["ambiguity_score"])), str(row["run_id"])))

    config_dir = root / "benchmark/config/runs/ecoli3_error_readcount"
    expected_methods = sorted({path.stem.split("_", 1)[1] for path in config_dir.glob("*.yaml")})
    display = {"dadec": "DADEC", "l_hero": "L-HERO", "f_hero": "F-HERO", "r_hero": "R-HERO"}
    status: list[dict[str, object]] = []
    for coverage_key, technology in TECHNOLOGY_BY_KEY.items():
        for method_key in expected_methods:
            method = display.get(method_key, method_key.upper())
            match = next((row for row in selected if row["technology"] == technology and str(row["method"]).lower().replace("-", "_") == method.lower().replace("-", "_")), None)
            status.append({
                "technology": technology,
                "config_coverage_key": coverage_key,
                "actual_short_coverage": "30x",
                "method": method,
                "status": "selected" if match else "missing",
                "run_id": match["run_id"] if match else "",
            })

    common_fields = [
        "technology", "short_read_error_rate", "short_read_error_percent",
        "original_short_read_error_rate", "original_short_read_error_percent",
        "short_read_length_bp", "actual_short_coverage", "config_coverage_key",
        "requested_reads", "aligned_reads", "method", "dadec_revision",
        "ambiguity_score", "mismatches_per_100_kbp", "indels_per_100_kbp",
        "residual_errors_per_100_kbp", "haplotype_coverage_percent",
        "local_misassemblies", "contigs_number", "CPU(h)", "WallTime(h)",
        "Memory(GB)", "long_coverage", "parameter_set", "run_id",
    ]
    outputs = {
        output_dir / "all_candidates.tsv": render(candidates, common_fields + ["is_strict_ambiguity"]),
        output_dir / "selected_results.tsv": render(selected, common_fields + ["selection_reason"]),
        output_dir / "quality_sensitivity.tsv": render(selected, common_fields),
        output_dir / "technology_method_status.tsv": render(status, ["technology", "config_coverage_key", "actual_short_coverage", "method", "status", "run_id"]),
    }

    mismatches: list[str] = []
    if args.check_only:
        for path, content in outputs.items():
            if not path.exists() or path.read_text() != content:
                mismatches.append(str(path.relative_to(root)))
        if mismatches:
            print("Out-of-date or missing outputs:", *mismatches, sep="\n  ", file=sys.stderr)
            return 1
        print(f"All {len(outputs)} outputs match their source data.")
        return 0

    output_dir.mkdir(parents=True, exist_ok=True)
    for path, content in outputs.items():
        path.write_text(content)
    print(f"Wrote {len(outputs)} files to {output_dir.relative_to(root)}")
    print(f"Selected {len(selected)} result(s) from {len(candidates)} candidate row(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
