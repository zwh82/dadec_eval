#!/usr/bin/env python3
import argparse
import csv
import json
import sys
from pathlib import Path

from common import atomic_write_json


def parse_report(path):
    with open(path, "r", encoding="utf-8") as handle:
        reader = csv.reader(handle, delimiter="\t")
        rows = [row for row in reader if row]
    if not rows:
        raise ValueError(f"Empty report: {path}")
    header = rows[0]
    if "taxID" not in header:
        raise ValueError(f"Report lacks taxID column: {path}")
    tax_idx = header.index("taxID")
    parsed = {}
    for row in rows[1:]:
        if len(row) != len(header):
            raise ValueError(f"Malformed report row in {path}: {row}")
        tax_id = row[tax_idx]
        if tax_id in parsed:
            raise ValueError(f"Duplicate taxID {tax_id} in {path}")
        parsed[tax_id] = row
    return header, parsed


def compare_reports(actual, expected):
    actual_header, actual_rows = parse_report(actual)
    expected_header, expected_rows = parse_report(expected)
    diffs = []
    if actual_header != expected_header:
        diffs.append({"kind": "header", "actual": actual_header, "expected": expected_header})
    missing = sorted(set(expected_rows) - set(actual_rows))
    extra = sorted(set(actual_rows) - set(expected_rows))
    if missing:
        diffs.append({"kind": "missing_taxid", "taxids": missing[:50], "count": len(missing)})
    if extra:
        diffs.append({"kind": "extra_taxid", "taxids": extra[:50], "count": len(extra)})
    for tax_id in sorted(set(actual_rows) & set(expected_rows)):
        if actual_rows[tax_id] != expected_rows[tax_id]:
            diffs.append({
                "kind": "row_mismatch",
                "taxID": tax_id,
                "actual": actual_rows[tax_id],
                "expected": expected_rows[tax_id],
            })
            if len(diffs) >= 100:
                break
    return {
        "match": not diffs,
        "actual_rows": len(actual_rows),
        "expected_rows": len(expected_rows),
        "diffs": diffs,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--actual", required=True)
    p.add_argument("--expected", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--fail-on-mismatch", action="store_true")
    args = p.parse_args()
    result = compare_reports(Path(args.actual), Path(args.expected))
    atomic_write_json(args.output, result)
    if args.fail_on_mismatch and not result["match"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
