#!/home/wenhai/miniconda3/envs/snakemake/bin/python
"""Backfill only missing canonical evaluations for non-default comparators."""

from __future__ import annotations

import argparse
import csv
import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from core import (
    METAQUAST_REPORTS,
    QUAST_REPORTS,
    ROOT,
    RUN_ONE,
    Target,
    assess_candidate,
    build_targets,
    candidate_matches_group,
    candidate_matches_target,
    candidate_values,
    deep_merge,
    discover_runs,
    effective_job_parameters,
    load_yaml,
    method_signature,
    relevant_parameters,
)


@dataclass
class ComparatorRecord:
    target: Target
    candidate: object
    status: str
    reason: str
    missing_scores: tuple[str, ...]
    job_config: Path | None


FIELDS = [
    "dataset", "coverage", "run_label", "method", "run_id", "run_root",
    "status", "reason", "missing_scores", "job_config", "dataset_config",
]


def candidate_run_base(candidate) -> str:
    run_id = str(candidate.provenance.get("run_id") or candidate.root.name)
    signature = str(candidate.provenance.get("parameter_signature") or "")
    suffix = f"_{signature}" if signature else ""
    if suffix and not run_id.endswith(suffix):
        raise ValueError(f"Run id {run_id!r} does not end in signature {signature!r}")
    return run_id[:-len(suffix)] if suffix else run_id


def find_job_config(target: Target, candidate) -> Path | None:
    values = candidate_values(candidate, target.coverage) or {}
    expected = relevant_parameters(values, target.method)
    run_base = candidate_run_base(candidate)
    matches = []
    for path in sorted(target.run_config_dir.glob("*.yaml")):
        data = load_yaml(path)
        run = data.get("run") or {}
        if (
            str(run.get("coverage")) != target.coverage
            or run.get("method") != target.method
            or str(run.get("id")) != run_base
        ):
            continue
        effective = effective_job_parameters(target, path)
        if relevant_parameters(effective, target.method) == expected:
            matches.append(path)
    if len(matches) > 1:
        raise ValueError(f"Multiple configs reconstruct comparator {candidate.root}")
    return matches[0] if matches else None


def generated_job_config(record: ComparatorRecord) -> str:
    target = record.target
    candidate = record.candidate
    provenance = candidate.provenance
    values = candidate_values(candidate, target.coverage) or {}
    lines = [
        f"evaluation: {{tool: {target.evaluation_tool}}}",
        "run: {id: %s, coverage: %s, method: %s, parameter_set: %s}" % (
            candidate_run_base(candidate), target.coverage, target.method,
            provenance.get("parameter_set", "legacy"),
        ),
        f"parameter_profile: {provenance.get('parameter_profile', 'study')}",
    ]
    lines.extend(f"{key}: {value}" for key, value in sorted(values.items()))
    return "\n".join(lines) + "\n"


def discover_comparators() -> list[ComparatorRecord]:
    runs = discover_runs()
    records: list[ComparatorRecord] = []
    seen: set[Path] = set()
    for target in build_targets():
        for candidate in runs:
            if (
                candidate.root in seen
                or not candidate_matches_group(candidate, target)
                or candidate_matches_target(candidate, target)
            ):
                continue
            status, reason, missing = assess_candidate(candidate, target)
            if status not in {"resume_evaluation", "invalid"}:
                continue
            records.append(ComparatorRecord(
                target, candidate, status, reason, missing,
                find_job_config(target, candidate),
            ))
            seen.add(candidate.root)
    return records


def write_manifest(path: Path, records: list[ComparatorRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with open(temporary, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, delimiter="\t")
        writer.writeheader()
        for record in records:
            candidate = record.candidate
            writer.writerow({
                "dataset": record.target.dataset,
                "coverage": record.target.coverage,
                "run_label": record.target.run_label,
                "method": record.target.method,
                "run_id": candidate.provenance.get("run_id") or candidate.root.name,
                "run_root": candidate.root,
                "status": record.status,
                "reason": record.reason,
                "missing_scores": ",".join(record.missing_scores),
                "job_config": record.job_config or "<generated>",
                "dataset_config": record.target.dataset_config,
            })
    os.replace(temporary, path)


def invoke(record: ComparatorRecord, temporary: Path, args) -> int:
    if record.job_config:
        config = record.job_config
    else:
        config = temporary / f"{record.candidate.root.name}.yaml"
        config.write_text(generated_job_config(record))
    command = [str(RUN_ONE), str(config), "--latency-wait", str(args.latency_wait)]
    variants = METAQUAST_REPORTS if record.target.evaluation_tool == "metaquast" else QUAST_REPORTS
    base = record.candidate.root / "output" / f"short_{record.target.coverage}" / record.target.method
    command.extend(str(base / variants[score]) for score in record.missing_scores)
    command.extend([
        "--allowed-rules",
        "metaquast_corrected" if record.target.evaluation_tool == "metaquast" else "quast_corrected",
    ])
    if args.dry_run:
        command.extend(["-n", "--quiet"])
    environment = os.environ.copy()
    environment.setdefault("PYTHONWARNINGS", "ignore")
    environment["DATASET_CONFIG"] = str(record.target.dataset_config)
    environment["CORES"] = str(args.cores)
    if record.target.evaluation_tool == "metaquast" and record.missing_scores:
        environment["AMBIGUITY_SCORES"] = ",".join(record.missing_scores)
    print("$ " + " ".join(map(str, command)), flush=True)
    return subprocess.run(command, cwd=ROOT, env=environment).returncode


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--execute", action="store_true")
    parser.add_argument("--dataset", action="append", default=[])
    parser.add_argument("--method", action="append", default=[])
    parser.add_argument("--limit", type=int)
    parser.add_argument("--cores", type=int, default=min(64, os.cpu_count() or 1))
    parser.add_argument("--latency-wait", type=int, default=60)
    parser.add_argument(
        "--manifest", type=Path,
        default=ROOT / "benchmark/results/default_parameter_comparator_status.tsv",
    )
    args = parser.parse_args()
    records = discover_comparators()
    write_manifest(args.manifest, records)
    if args.dataset:
        records = [record for record in records if record.target.dataset in args.dataset]
    if args.method:
        records = [record for record in records if record.target.method in args.method]
    if args.limit is not None:
        records = records[:args.limit]
    print(f"Comparator evaluations requiring attention: {len(records)}")
    for record in records:
        print(f"  {record.candidate.root.name}: {record.status} ({record.reason})")
    invalid = [record for record in records if record.status == "invalid"]
    if invalid:
        print("Refusing execution because at least one comparator is invalid")
        return 1
    if not (args.dry_run or args.execute):
        print("List-only mode. Add --dry-run or --execute.")
        return 0
    failures = []
    with tempfile.TemporaryDirectory(prefix="dadec-default-comparators-") as directory:
        temporary = Path(directory)
        for index, record in enumerate(records, 1):
            print(f"[{index}/{len(records)}] {record.candidate.root.name}")
            returncode = invoke(record, temporary, args)
            if returncode:
                failures.append((record.candidate.root.name, returncode))
                break
            if not args.dry_run:
                status, reason, _ = assess_candidate(record.candidate, record.target)
                if status != "complete":
                    failures.append((record.candidate.root.name, f"{status}: {reason}"))
                    break
    if failures:
        for name, reason in failures:
            print(f"FAILED {name}: {reason}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
