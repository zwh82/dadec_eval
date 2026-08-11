#!/home/wenhai/miniconda3/envs/dadec_eval/bin/python
"""Resume only missing 0.99/0.9999 MetaQUAST reports for completed runs.

The scanner excludes ablation runs, QUAST-only datasets, and runs without an
existing corrected.fa. Job configs are reconstructed from provenance so older
parameter variants continue in their original run directories.
"""

import argparse
import csv
import fnmatch
import json
import os
import subprocess
import tempfile
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNS_ROOT = ROOT / "benchmark/runs"
RUN_ONE = ROOT / "benchmark/run_one.sh"
SCORE_REPORTS = {
    "0.99": Path("metaquast/combined_reference/report.tsv"),
    "0.9999": Path("metaquast.ambiguity9999/combined_reference/report.tsv"),
}
DATASET_CONFIGS = {
    "30strains": ROOT / "benchmark/config/datasets/30strains.yaml",
    "30strains_legacy": ROOT / "benchmark/config/datasets/30strains_legacy.yaml",
    "100strains": ROOT / "benchmark/config/datasets/100strains.yaml",
    "ecoli3": ROOT / "benchmark/config/datasets/ecoli3.yaml",
    "ecoli_error": ROOT / "benchmark/config/datasets/ecoli_error_tech.yaml",
}
MANIFEST_FIELDS = [
    "dataset", "coverage", "method", "run_group", "run_id",
    "missing_scores", "dataset_config", "corrected",
]


def discover_missing(dataset_filters=(), run_glob=None):
    records = []
    for provenance_path in sorted(RUNS_ROOT.glob("*/*/benchmark/provenance.json")):
        run_root = provenance_path.parents[1]
        if "dadec_ablation" in run_root.name:
            continue
        provenance = json.loads(provenance_path.read_text())
        dataset = provenance.get("dataset")
        if provenance.get("evaluation_tool", "metaquast") != "metaquast":
            continue
        if dataset_filters and dataset not in dataset_filters:
            continue
        if run_glob and not fnmatch.fnmatch(run_root.name, run_glob):
            continue
        dataset_config = DATASET_CONFIGS.get(dataset)
        if not dataset_config or not dataset_config.is_file():
            raise FileNotFoundError(f"No dataset config mapped for {dataset!r}")
        parameters_by_coverage = provenance.get("parameters_by_coverage", {})
        for coverage, parameters in sorted(parameters_by_coverage.items()):
            for method in provenance.get("methods", []):
                method_root = run_root / "output" / f"short_{coverage}" / method
                corrected = method_root / "corrected.fa"
                if not corrected.is_file() or corrected.stat().st_size == 0:
                    continue
                missing = [
                    score for score, relative in SCORE_REPORTS.items()
                    if not (method_root / relative).is_file()
                ]
                if not missing:
                    continue
                signature = provenance.get("parameter_signature", "")
                run_id = provenance.get("run_id") or run_root.name
                suffix = f"_{signature}" if signature else ""
                if suffix and not run_id.endswith(suffix):
                    raise ValueError(
                        f"Run {run_id!r} does not end with provenance signature {signature!r}"
                    )
                run_base = run_id[:-len(suffix)] if suffix else run_id
                reference = run_root / "tmp/reference" / f"{dataset}.fa"
                if not reference.is_file() or reference.stat().st_size == 0:
                    raise FileNotFoundError(f"Prepared reference is missing: {reference}")
                records.append({
                    "dataset": dataset,
                    "coverage": coverage,
                    "method": method,
                    "run_group": run_root.parent.name,
                    "run_id": run_id,
                    "run_base": run_base,
                    "parameter_set": provenance.get("parameter_set", "legacy"),
                    "parameter_profile": provenance.get("parameter_profile", "study"),
                    "parameters": parameters,
                    "missing_scores": missing,
                    "dataset_config": dataset_config,
                    "corrected": corrected,
                    "run_root": run_root,
                })
    return records


def yaml_value(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    return str(value)


def write_job_config(record, path):
    lines = [
        "evaluation: {tool: metaquast}",
        "run: {id: %s, coverage: %s, method: %s, parameter_set: %s}" % (
            record["run_base"], record["coverage"], record["method"],
            record["parameter_set"],
        ),
        f"parameter_profile: {record['parameter_profile']}",
    ]
    lines.extend(
        f"{key}: {yaml_value(value)}"
        for key, value in sorted(record["parameters"].items())
        if value is not None
    )
    Path(path).write_text("\n".join(lines) + "\n")


def manifest_row(record):
    return {
        "dataset": record["dataset"],
        "coverage": record["coverage"],
        "method": record["method"],
        "run_group": record["run_group"],
        "run_id": record["run_id"],
        "missing_scores": ",".join(record["missing_scores"]),
        "dataset_config": str(record["dataset_config"]),
        "corrected": str(record["corrected"]),
    }


def write_manifest(path, records):
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    with open(temporary, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_FIELDS, delimiter="\t")
        writer.writeheader()
        writer.writerows(manifest_row(record) for record in records)
    os.replace(temporary, output)


def print_summary(records):
    print(f"Missing MetaQUAST evaluations: {len(records)}")
    for (dataset, score), count in sorted(Counter(
        (record["dataset"], score)
        for record in records
        for score in record["missing_scores"]
    ).items()):
        print(f"  {dataset:20s} score={score:6s} jobs={count}")
    for index, record in enumerate(records, 1):
        print(
            f"{index:3d}\t{record['run_group']}\t{record['run_id']}\t"
            f"scores={','.join(record['missing_scores'])}"
        )


def run_records(records, dry_run=False, keep_going=False, cores=None):
    failures = []
    with tempfile.TemporaryDirectory(prefix="dadec-missing-ambiguity-") as directory:
        temporary = Path(directory)
        for index, record in enumerate(records, 1):
            config_path = temporary / f"{index:03d}_{record['run_id']}.yaml"
            write_job_config(record, config_path)
            command = [str(RUN_ONE), str(config_path)]
            if dry_run:
                command.append("-n")
            environment = os.environ.copy()
            environment["DATASET_CONFIG"] = str(record["dataset_config"])
            environment["AMBIGUITY_SCORES"] = ",".join(record["missing_scores"])
            if cores:
                environment["CORES"] = str(cores)
            print(
                f"\n[{index}/{len(records)}] {record['run_id']} "
                f"ambiguity={environment['AMBIGUITY_SCORES']}",
                flush=True,
            )
            result = subprocess.run(command, cwd=ROOT, env=environment)
            if result.returncode:
                failures.append((record["run_id"], result.returncode))
                if not keep_going:
                    break
            elif not dry_run:
                method_root = record["run_root"] / "output" / f"short_{record['coverage']}" / record["method"]
                still_missing = [
                    score for score in record["missing_scores"]
                    if not (method_root / SCORE_REPORTS[score]).is_file()
                ]
                if still_missing:
                    failures.append((record["run_id"], f"missing reports: {still_missing}"))
                    if not keep_going:
                        break
    if failures:
        print("\nFailures:")
        for run_id, reason in failures:
            print(f"  {run_id}: {reason}")
        return 1
    return 0


def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--execute", action="store_true", help="Run missing MetaQUAST jobs sequentially.")
    mode.add_argument("--dry-run", action="store_true", help="Run a Snakemake dry-run for every missing job.")
    parser.add_argument("--dataset", action="append", default=[], help="Limit to a dataset id; repeatable.")
    parser.add_argument("--run-glob", help="Limit to matching run IDs.")
    parser.add_argument("--manifest", help="Write the current missing-job list as TSV.")
    parser.add_argument("--cores", type=int, help="Override CORES passed to run_one.sh.")
    parser.add_argument("--keep-going", action="store_true", help="Continue after a failed job.")
    args = parser.parse_args()
    records = discover_missing(args.dataset, args.run_glob)
    print_summary(records)
    if args.manifest:
        write_manifest(args.manifest, records)
        print(f"Manifest: {Path(args.manifest).resolve()}")
    if not records:
        return 0
    if args.execute or args.dry_run:
        return run_records(
            records, dry_run=args.dry_run,
            keep_going=args.keep_going,
            cores=args.cores,
        )
    print("\nList-only mode. Add --execute to run, or --dry-run to validate commands.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
