#!/usr/bin/env python3
import argparse
import csv
from pathlib import Path

RESOURCE_KEY_FIELDS = ["run_id", "parameter_set", "dataset", "long_coverage", "short_coverage", "method"]
KEY_FIELDS = [*RESOURCE_KEY_FIELDS, "ambiguity_score"]
RESOURCE_FIELDS = [
    "CPU(h)", "WallTime(h)", "Memory(GB)",
]
METAQUAST_FIELDS = [
    "mismatches_per_100_kbp", "indels_per_100_kbp",
    "haplotype_coverage_percent", "local_misassemblies", "contigs_number",
]
FIELDS = [*KEY_FIELDS, *RESOURCE_FIELDS, *METAQUAST_FIELDS]

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

def read_tsv(path):
    with open(path, newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))

def row_key(row, fields=KEY_FIELDS):
    return tuple(row[field] for field in fields)

def aggregate(resources_path, metaquast_path):
    resource_rows = read_tsv(resources_path)
    resources = {row_key(row, RESOURCE_KEY_FIELDS): row for row in resource_rows}
    if len(resources) != len(resource_rows):
        raise ValueError("Duplicate resource key")
    rows = []
    seen = set()
    for meta in read_tsv(metaquast_path):
        key = row_key(meta)
        if key in seen:
            raise ValueError(f"Duplicate MetaQUAST key: {key}")
        seen.add(key)
        resource = resources.get(row_key(meta, RESOURCE_KEY_FIELDS), {})
        rows.append({
            **{field: meta[field] for field in KEY_FIELDS},
            **{field: resource.get(field, "NA") for field in RESOURCE_FIELDS},
            **{field: meta[field] for field in METAQUAST_FIELDS},
        })
    rows.sort(key=lambda row: (
        row["dataset"],
        row["method"] != "raw",
        coverage_sort_key(row["short_coverage"]),
        row["method"], row["ambiguity_score"], row["parameter_set"], row["run_id"],
    ))
    return rows

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--resources", required=True)
    parser.add_argument("--metaquast", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    rows = aggregate(args.resources, args.metaquast)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)

if __name__ == "__main__":
    main()
