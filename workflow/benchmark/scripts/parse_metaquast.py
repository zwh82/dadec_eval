#!/usr/bin/env python3
import argparse
import csv
from pathlib import Path


LABELS = {
    "# mismatches per 100 kbp": "mismatches_per_100_kbp",
    "# indels per 100 kbp": "indels_per_100_kbp",
    "Genome fraction (%)": "haplotype_coverage_percent",
    "# local misassemblies": "local_misassemblies",
    "# contigs": "contigs_number",
}
FIELDS = [
    "run_id", "parameter_set", "dataset", "long_coverage", "short_coverage", "method", "ambiguity_score",
    *LABELS.values(),
]


def parse_report(path):
    found = {}
    with open(path, newline="") as handle:
        for row in csv.reader(handle, delimiter="\t"):
            if not row:
                continue
            label = row[0].strip()
            if label not in LABELS:
                continue
            if label in found:
                raise ValueError(f"Duplicate MetaQUAST row {label!r} in {path}")
            values = [value.strip() for value in row[1:] if value.strip()]
            if len(values) != 1:
                raise ValueError(f"Expected one assembly value for {label!r}, found {len(values)}")
            found[label] = values[0]
    missing = [label for label in LABELS if label not in found]
    if missing:
        raise ValueError(f"Missing MetaQUAST rows in {path}: {', '.join(missing)}")
    return {
        LABELS[label]: float(value) if LABELS[label] in {
            "mismatches_per_100_kbp", "indels_per_100_kbp", "haplotype_coverage_percent"
        } else int(value)
        for label, value in found.items()
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--long-coverage", required=True)
    parser.add_argument("--run-id", default="legacy")
    parser.add_argument("--parameter-set", default="legacy")
    parser.add_argument("--coverages", nargs="+", required=True)
    parser.add_argument("--methods", nargs="+", required=True)
    parser.add_argument("--ambiguity-scores", nargs="+", required=True)
    parser.add_argument("--reports", nargs="+", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if not (len(args.coverages) == len(args.methods) == len(args.ambiguity_scores) == len(args.reports)):
        raise ValueError("coverages, methods, ambiguity scores and reports must have the same length")
    rows = []
    for coverage, method, score, report in zip(
        args.coverages, args.methods, args.ambiguity_scores, args.reports
    ):
        rows.append({
            "run_id": args.run_id,
            "parameter_set": args.parameter_set,
            "dataset": args.dataset,
            "long_coverage": args.long_coverage,
            "short_coverage": coverage,
            "method": method,
            "ambiguity_score": score,
            **parse_report(report),
        })
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
