#!/usr/bin/env python3
import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from aggregate import FIELDS, KEY_FIELDS

def coverage_sort_key(label):
    value = str(label)
    if value == "NA":
        return (-1, 0, value)
    if value.endswith("x") and value[:-1].isdigit():
        return (0, int(value[:-1]), value)
    if value.endswith("pct") and value[:-3].isdigit():
        return (1, int(value[:-3]), value)
    if value.endswith("percent") and value[:-7].isdigit():
        return (1, int(value[:-7]), value)
    return (2, 0, value)

def collect(results_root):
    root = Path(results_root)
    rows = []
    seen = set()
    for table in sorted(root.glob("*/tables/benchmark_summary.tsv")):
        with open(table, newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            if reader.fieldnames != FIELDS:
                raise ValueError(f"Unexpected schema in {table}: {reader.fieldnames}")
            for row in reader:
                if row["dataset"] != table.parents[1].name:
                    raise ValueError(f"Dataset/path mismatch in {table}")
                key = tuple(row[field] for field in KEY_FIELDS)
                if key in seen:
                    raise ValueError(f"Duplicate summary key: {key}")
                seen.add(key)
                rows.append(row)
    rows.sort(key=lambda row: (
        row["dataset"], row["method"] != "raw",
        coverage_sort_key(row["short_coverage"]),
    ))
    return rows

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-root", default="benchmark/results")
    parser.add_argument("--output", default="benchmark/results/all_datasets_summary.tsv")
    args = parser.parse_args()
    rows = collect(args.results_root)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)

if __name__ == "__main__":
    main()
