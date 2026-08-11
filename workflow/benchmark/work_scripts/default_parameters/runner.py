#!/home/wenhai/miniconda3/envs/snakemake/bin/python
"""Restart-safe runner used by the three tool-specific entry points."""

from __future__ import annotations

import argparse
import os
import subprocess
import tempfile
from collections import Counter
from pathlib import Path

from core import (
    METAQUAST_REPORTS,
    QUAST_REPORTS,
    METHOD_ORDER,
    ROOT,
    RUN_ONE,
    AuditRecord,
    audit_all,
    audit_target,
    discover_runs,
    generated_job_config,
    shard_records,
    write_manifest,
)


DEFAULT_MANIFEST = ROOT / "benchmark/results/default_parameter_status.tsv"
PENDING = {"new", "resume_evaluation"}


def print_summary(records: list[AuditRecord], method: str) -> None:
    print(f"Tool: {method}")
    print(f"Targets: {len(records)}")
    for (status, priority), count in sorted(Counter(
        (record.status, record.priority) for record in records
    ).items()):
        print(f"  {status:18s} priority={priority:10s} jobs={count}")
    for record in records:
        print(
            f"{record.target.target_id:34s} {record.status:18s} "
            f"priority={record.priority:10s} run={record.run_id}"
        )


def select_pending(records: list[AuditRecord], args: argparse.Namespace) -> list[AuditRecord]:
    selected = records
    if args.dataset:
        selected = [record for record in selected if record.target.dataset in args.dataset]
    if args.priority != "all":
        selected = [record for record in selected if record.priority == args.priority]
    invalid = [record for record in selected if record.status == "invalid"]
    if invalid:
        details = "; ".join(f"{r.target.target_id}: {r.reason}" for r in invalid)
        raise RuntimeError(f"Refusing to run with invalid targets: {details}")
    # Assign shards before removing completed rows so a shard's ownership does
    # not change as other nodes finish jobs and refresh the shared manifest.
    selected = shard_records(selected, args.shard_count, args.shard_index)
    selected = [record for record in selected if record.status in PENDING]
    if args.limit is not None:
        selected = selected[: args.limit]
    return selected


def invoke_record(
    record: AuditRecord,
    temporary: Path,
    dry_run: bool,
    cores: int,
    latency_wait: int,
    snakemake_args: list[str],
) -> int:
    if record.job_config:
        config_path = record.job_config
    else:
        config_path = temporary / f"{record.target.dataset}_{record.target.run_label}_{record.target.method}.yaml"
        config_path.write_text(generated_job_config(record.target))
    command = [str(RUN_ONE), str(config_path), "--latency-wait", str(latency_wait)]
    if record.status == "resume_evaluation":
        variants = METAQUAST_REPORTS if record.target.evaluation_tool == "metaquast" else QUAST_REPORTS
        base = record.run_root / "output" / f"short_{record.target.coverage}" / record.target.method
        command.extend(str(base / variants[score]) for score in record.missing_scores)
        command.extend([
            "--allowed-rules",
            "metaquast_corrected" if record.target.evaluation_tool == "metaquast" else "quast_corrected",
        ])
    if dry_run:
        command.extend(["-n", "--quiet"])
    command.extend(snakemake_args)
    environment = os.environ.copy()
    environment.setdefault("PYTHONWARNINGS", "ignore")
    environment["DATASET_CONFIG"] = str(record.target.dataset_config)
    environment["CORES"] = str(cores)
    if record.status == "resume_evaluation" and record.missing_scores:
        environment["AMBIGUITY_SCORES"] = ",".join(record.missing_scores)
    print("$ " + " ".join(map(str, command)), flush=True)
    return subprocess.run(command, cwd=ROOT, env=environment).returncode


def run_selected(records: list[AuditRecord], args: argparse.Namespace, manifest: Path) -> int:
    failures: list[tuple[str, str]] = []
    with tempfile.TemporaryDirectory(prefix="dadec-default-parameters-") as directory:
        temporary = Path(directory)
        for index, original in enumerate(records, 1):
            fresh = audit_target(original.target, discover_runs())
            if fresh.status == "complete":
                print(f"[{index}/{len(records)}] skip newly completed {fresh.target.target_id}")
                continue
            if fresh.status == "invalid":
                failures.append((fresh.target.target_id, fresh.reason))
                if not args.keep_going:
                    break
                continue
            print(f"\n[{index}/{len(records)}] {fresh.target.target_id} ({fresh.status})", flush=True)
            returncode = invoke_record(
                fresh,
                temporary,
                dry_run=args.dry_run,
                cores=args.cores,
                latency_wait=args.latency_wait,
                snakemake_args=args.snakemake_args,
            )
            if returncode:
                failures.append((fresh.target.target_id, f"exit code {returncode}"))
                if not args.keep_going:
                    break
            elif not args.dry_run:
                checked = audit_target(fresh.target, discover_runs())
                if checked.status != "complete":
                    failures.append((fresh.target.target_id, f"post-run status {checked.status}: {checked.reason}"))
                    if not args.keep_going:
                        break
            write_manifest(manifest, audit_all())
    if failures:
        print("\nFailures:")
        for target_id, reason in failures:
            print(f"  {target_id}: {reason}")
        return 1
    return 0


def main(method: str) -> int:
    if method not in METHOD_ORDER:
        raise ValueError(f"Unsupported method: {method}")
    parser = argparse.ArgumentParser(description=f"Audit or run {method} experiment-default jobs.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Validate selected pending DAGs without execution.")
    mode.add_argument("--execute", action="store_true", help="Execute selected pending jobs sequentially.")
    parser.add_argument("--dataset", action="append", default=[], help="Limit to a dataset id; repeatable.")
    parser.add_argument("--priority", choices=("all", "comparator", "remaining"), default="all")
    parser.add_argument("--shard-count", type=int, default=1)
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--cores", type=int, default=min(64, os.cpu_count() or 1))
    parser.add_argument("--latency-wait", type=int, default=60)
    parser.add_argument("--keep-going", action="store_true")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("snakemake_args", nargs=argparse.REMAINDER,
                        help="Additional Snakemake arguments after --.")
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be positive")
    if args.cores < 1 or args.latency_wait < 0:
        parser.error("--cores must be positive and --latency-wait non-negative")
    if args.snakemake_args[:1] == ["--"]:
        args.snakemake_args = args.snakemake_args[1:]

    all_records = audit_all()
    write_manifest(args.manifest, all_records)
    method_records = [record for record in all_records if record.target.method == method]
    print_summary(method_records, method)
    if not (args.dry_run or args.execute):
        print(f"Manifest: {args.manifest.resolve()}")
        print("List-only mode. Add --dry-run or --execute.")
        return 1 if any(record.status == "invalid" for record in method_records) else 0
    try:
        selected = select_pending(method_records, args)
    except (RuntimeError, ValueError) as error:
        parser.error(str(error))
    print(f"Selected pending jobs: {len(selected)}")
    if not selected:
        return 0
    return run_selected(selected, args, args.manifest)
