#!/usr/bin/env python3
import argparse
import csv
import re
from pathlib import Path


FIELDS = [
    "run_id", "parameter_set", "dataset", "long_coverage", "short_coverage", "method",
    "CPU(h)", "WallTime(h)", "Memory(GB)",
]


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


def wall_to_seconds(value):
    value = value.strip()
    if ":" not in value:
        return float(value)
    parts = [float(part) for part in value.split(":" )]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    raise ValueError(f"Invalid wall time: {value}")


def parse_resource_text(text):
    values = {}
    for line in text.splitlines():
        if "=" in line and not line.lstrip().startswith("Command"):
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()

    verbose = {
        "wall_seconds": r"Elapsed \(wall clock\) time \([^\n]+\):\s*(\S+)",
        "user_cpu_seconds": r"User time \(seconds\):\s*(\S+)",
        "system_cpu_seconds": r"System time \(seconds\):\s*(\S+)",
        "cpu_percent": r"Percent of CPU this job got:\s*(\S+)",
        "max_rss_kb": r"Maximum resident set size \(kbytes\):\s*(\S+)",
        "exit_code": r"Exit status:\s*(\S+)",
    }
    for key, pattern in verbose.items():
        if key not in values:
            match = re.search(pattern, text)
            if match:
                values[key] = match.group(1)

    required = ["wall_seconds", "user_cpu_seconds", "system_cpu_seconds", "max_rss_kb", "exit_code"]
    missing = [field for field in required if field not in values]
    if missing:
        raise ValueError(f"Missing resource fields: {', '.join(missing)}")

    user = float(values["user_cpu_seconds"])
    system = float(values["system_cpu_seconds"])
    return {
        "wall_seconds": wall_to_seconds(values["wall_seconds"]),
        "user_cpu_seconds": user,
        "system_cpu_seconds": system,
        "total_cpu_seconds": user + system,
        "max_rss_kb": int(values["max_rss_kb"]),
        "exit_code": int(values["exit_code"]),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--long-coverage", required=True)
    parser.add_argument("--run-id", default="legacy")
    parser.add_argument("--parameter-set", default="legacy")
    parser.add_argument("--coverages", nargs="+", required=True)
    parser.add_argument("--methods", nargs="+", required=True)
    parser.add_argument("--inputs", nargs="+", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if not (len(args.coverages) == len(args.methods) == len(args.inputs)):
        raise ValueError("coverages, methods and inputs must have equal lengths")
    rows = []
    for coverage, method, input_path in zip(args.coverages, args.methods, args.inputs):
        metrics = parse_resource_text(Path(input_path).read_text())
        rows.append({
            "run_id": args.run_id, "parameter_set": args.parameter_set,
            "dataset": args.dataset, "long_coverage": args.long_coverage,
            "short_coverage": coverage, "method": method,
            "CPU(h)": f'{metrics["total_cpu_seconds"] / 3600:.3f}',
            "WallTime(h)": f'{metrics["wall_seconds"] / 3600:.3f}',
            "Memory(GB)": f'{metrics["max_rss_kb"] / 1024 / 1024:.3f}',
        })
    rows.sort(key=lambda row: (coverage_sort_key(row["short_coverage"]), row["method"]))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
