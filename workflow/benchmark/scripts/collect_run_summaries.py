#!/usr/bin/env python3
import argparse
import csv
import fnmatch
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from aggregate import FIELDS, METAQUAST_FIELDS, RESOURCE_FIELDS
from parse_metaquast import parse_report
from parse_resources import parse_resource_text


def method_label(method):
    labels = {
        "dadec": "DADEC", "fmlrc": "FMLRC", "f_hero": "F_HERO",
        "ratatosk": "Ratatosk", "r_hero": "R_HERO", "lordec": "LoRDEC",
        "l_hero": "L_HERO", "colormap": "CoLoRMap", "proovread": "Proovread",
        "vechat": "VeChat", "dechat": "DeChat",
    }
    return labels.get(method, method)


def coverage_sort_key(label):
    value = str(label)
    if value.endswith("x") and value[:-1].isdigit():
        return (0, int(value[:-1]), value)
    if value.endswith("pct") and value[:-3].isdigit():
        return (1, int(value[:-3]), value)
    if value.endswith("percent") and value[:-7].isdigit():
        return (1, int(value[:-7]), value)
    return (2, value)


def collect(runs_root, dataset=None, long_coverage=None, short_coverage=None, method=None, run_glob=None):
    rows = []
    seen = set()
    provenance_paths = set(Path(runs_root).glob("*/benchmark/provenance.json"))
    provenance_paths.update(Path(runs_root).glob("*/*/benchmark/provenance.json"))
    for provenance_path in sorted(provenance_paths):
        run_root = provenance_path.parents[1]
        if run_glob and not fnmatch.fnmatch(run_root.name, run_glob):
            continue
        provenance = json.loads(provenance_path.read_text())
        run_id = provenance.get("run_id") or run_root.name
        parameter_set = provenance.get("parameter_set") or provenance.get("parameter_profile", "legacy")
        evaluation_tool = provenance.get("evaluation_tool", "metaquast")
        if evaluation_tool == "metaquast":
            score_variants = [
                ("0.99", Path("metaquast/combined_reference/report.tsv")),
                ("0.9999", Path("metaquast.ambiguity9999/combined_reference/report.tsv")),
            ]
        else:
            score_variants = [("NA", Path("quast/report.tsv"))]
        run_dataset = provenance["dataset"]
        run_long_coverage = provenance["long_coverage"]
        if dataset and run_dataset != dataset:
            continue
        if long_coverage and run_long_coverage != long_coverage:
            continue
        for coverage, values in sorted(provenance["parameters_by_coverage"].items()):
            if short_coverage and coverage != short_coverage:
                continue
            for run_method in provenance["methods"]:
                if method and run_method != method:
                    continue
                resources_path = run_root / "benchmark" / f"short_{coverage}" / run_method / "resources.time.txt"
                if not resources_path.exists():
                    continue
                resource = parse_resource_text(resources_path.read_text())
                for ambiguity_score, report_rel in score_variants:
                    report_path = run_root / "output" / f"short_{coverage}" / run_method / report_rel
                    if not report_path.exists():
                        continue
                    meta = parse_report(report_path)
                    row = {
                        "run_id": run_id,
                        "parameter_set": parameter_set,
                        "dataset": run_dataset,
                        "long_coverage": run_long_coverage,
                        "short_coverage": coverage,
                        "method": method_label(run_method),
                        "ambiguity_score": ambiguity_score,
                        "CPU(h)": f'{resource["total_cpu_seconds"] / 3600:.3f}',
                        "WallTime(h)": f'{resource["wall_seconds"] / 3600:.3f}',
                        "Memory(GB)": f'{resource["max_rss_kb"] / 1024 / 1024:.3f}',
                        **{field: str(meta[field]) for field in METAQUAST_FIELDS},
                    }
                    key = tuple(row[field] for field in (
                        "run_id", "dataset", "short_coverage", "method", "ambiguity_score"
                    ))
                    if key in seen:
                        raise ValueError(f"Duplicate run summary key: {key}")
                    seen.add(key)
                    rows.append(row)
    rows.sort(key=lambda row: (
        row["dataset"],
        coverage_sort_key(row["short_coverage"]),
        row["method"],
        row["ambiguity_score"],
        row["parameter_set"],
        row["run_id"],
    ))
    return rows


def best_rows(rows):
    groups = {}
    for row in rows:
        key = (
            row["dataset"], row["long_coverage"], row["short_coverage"],
            row["method"], row["ambiguity_score"]
        )
        groups.setdefault(key, []).append(row)
    result = []
    for key in sorted(groups):
        result.append(min(groups[key], key=lambda row: (
            -float(row["haplotype_coverage_percent"]),
            float(row["mismatches_per_100_kbp"]),
            float(row["indels_per_100_kbp"]),
            int(row["local_misassemblies"]),
            int(row["contigs_number"]),
            float(row["WallTime(h)"]),
        )))
    return result


def write(path, rows):
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = output.with_suffix(output.suffix + ".tmp")
    with open(tmp, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    tmp.replace(output)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs-root", default="benchmark/runs")
    parser.add_argument("--output-all", default="benchmark/results/all_parameter_runs.tsv")
    parser.add_argument("--output-best", default="benchmark/results/best_parameter_runs.tsv")
    parser.add_argument("--dataset", help="Only collect runs whose provenance dataset matches this value.")
    parser.add_argument("--long-coverage", help="Only collect runs whose provenance long_coverage matches this value.")
    parser.add_argument("--short-coverage", help="Only collect rows for this short-read coverage, for example 20x.")
    parser.add_argument("--method", help="Only collect this internal method name, for example dadec or fmlrc.")
    parser.add_argument("--run-glob", help="Only collect run directories whose name matches this shell-style glob.")
    args = parser.parse_args()
    rows = collect(
        args.runs_root,
        dataset=args.dataset,
        long_coverage=args.long_coverage,
        short_coverage=args.short_coverage,
        method=args.method,
        run_glob=args.run_glob,
    )
    write(args.output_all, rows)
    write(args.output_best, best_rows(rows))


if __name__ == "__main__":
    main()
