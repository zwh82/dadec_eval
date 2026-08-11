#!/usr/bin/env python3
"""Summarize DADEC stage-ablation QUAST metrics + resource usage into one wide table.

Reads <out-root>/stage_*/<evaluation-dir>/report.tsv (each ablation
combination) plus an optional baseline report.tsv (the full 1,2,3 run),
extracts the key metrics and writes a TSV with rows = metrics and columns =
stage combinations. Columns are ordered 1, 2, 3, 1,2, 1,3, 2,3, 1,2,3.
"""
import argparse
import glob
import os

# Metrics pulled from the QUAST report.tsv (this order is the output row order)
QUAST_METRICS = [
    "Genome fraction (%)",
    "Duplication ratio",
    "# mismatches per 100 kbp",
    "# indels per 100 kbp",
    "# local misassemblies",
    "N50",
    "NG50",
    "NGA50",
    "Total aligned length",
    "Largest alignment",
]
# Resource metrics pulled from resources.time.txt
RESOURCE_METRICS = ["wall_seconds", "max_rss_kb"]


def parse_report(path):
    """Parse a two-column QUAST report.tsv into {metric: value}."""
    values = {}
    with open(path) as handle:
        for line in handle:
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 2:
                values[parts[0].strip()] = parts[1].strip()
    return values


def _wall_to_seconds(text):
    """Convert 'h:mm:ss' / 'm:ss.ss' into seconds."""
    parts = text.split(":")
    try:
        parts = [float(p) for p in parts]
    except ValueError:
        return text
    seconds = 0.0
    for part in parts:
        seconds = seconds * 60 + part
    return f"{seconds:.2f}"


def parse_resources(path):
    """Parse a resource file for wall seconds and max RSS.

    Handles both formats:
    - /usr/bin/time -v verbose output (produced by this ablation script)
    - the pipeline's custom key=value format (produced by baseline runs)
    """
    result = {}
    if not path or not os.path.isfile(path):
        return result
    with open(path) as handle:
        for line in handle:
            line = line.strip()
            if line.startswith("wall_seconds="):
                result["wall_seconds"] = line.split("=", 1)[1].strip()
            elif line.startswith("max_rss_kb="):
                result["max_rss_kb"] = line.split("=", 1)[1].strip()
            elif line.startswith("Elapsed (wall clock) time"):
                result["wall_seconds"] = _wall_to_seconds(line.split(":", 1)[1].strip())
            elif line.startswith("Maximum resident set size"):
                result["max_rss_kb"] = line.rsplit(":", 1)[1].strip()
    return result


def column_from_dir(work, evaluation_dir):
    """Build a column (QUAST metrics + resources) from a stage_<tag> directory."""
    tag = os.path.basename(work)[len("stage_"):]
    label = tag.replace("_", ",")
    report = os.path.join(work, evaluation_dir, "report.tsv")
    if not os.path.isfile(report):
        report = os.path.join(work, evaluation_dir, "combined_reference", "report.tsv")
    column = {}
    if os.path.isfile(report):
        parsed = parse_report(report)
        for metric in QUAST_METRICS:
            column[metric] = parsed.get(metric, "")
    resources = parse_resources(os.path.join(work, "resources.time.txt"))
    for metric in RESOURCE_METRICS:
        column[metric] = resources.get(metric, "")
    return label, column


def sort_key(label):
    """Column order: first by number of stages, then lexicographically."""
    stages = label.split(",")
    return (len(stages), label)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-root", required=True,
                        help="Ablation output root directory containing stage_* subdirs")
    parser.add_argument("--evaluation-dir", default="quast",
                        help="Per-stage evaluation directory (default: quast)")
    parser.add_argument("--baseline-report", default=None,
                        help="QUAST report.tsv of the full 1,2,3 baseline (optional)")
    parser.add_argument("--baseline-resources", default=None,
                        help="resources.time.txt of the full 1,2,3 baseline (optional)")
    parser.add_argument("--output", required=True, help="Output summary TSV path")
    args = parser.parse_args()

    columns = {}  # label -> {metric: value}
    for work in sorted(glob.glob(os.path.join(args.out_root, "stage_*"))):
        if not os.path.isdir(work):
            continue
        label, column = column_from_dir(work, args.evaluation_dir)
        columns[label] = column

    if args.baseline_report and os.path.isfile(args.baseline_report):
        parsed = parse_report(args.baseline_report)
        base_col = {metric: parsed.get(metric, "") for metric in QUAST_METRICS}
        # The pipeline stores resources.time.txt under the benchmark/ subtree, not
        # next to the report, so prefer the explicitly passed --baseline-resources.
        base_res = parse_resources(args.baseline_resources)
        for metric in RESOURCE_METRICS:
            base_col[metric] = base_res.get(metric, "")
        columns["1,2,3"] = base_col

    labels = sorted(columns, key=sort_key)
    rows = QUAST_METRICS + RESOURCE_METRICS

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w") as out:
        out.write("\t".join(["metric"] + labels) + "\n")
        for metric in rows:
            out.write("\t".join([metric] + [columns[label].get(metric, "") for label in labels]) + "\n")

    print(f"Wrote {len(labels)} columns x {len(rows)} rows -> {args.output}")
    print("Columns: " + ", ".join(labels))


if __name__ == "__main__":
    main()
