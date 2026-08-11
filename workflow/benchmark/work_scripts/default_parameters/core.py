#!/home/wenhai/miniconda3/envs/snakemake/bin/python
"""Shared target discovery, semantic audit, and manifest helpers."""

from __future__ import annotations

import copy
import csv
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import yaml


ROOT = Path(__file__).resolve().parents[3]
BENCHMARK = ROOT / "benchmark"
DEFAULT_CONFIG = Path(__file__).with_name("config.yaml")
COMMON_CONFIG = BENCHMARK / "config/common.yaml"
RUNS_ROOT = BENCHMARK / "runs"
RUN_ONE = BENCHMARK / "run_one.sh"
METHOD_ORDER = ("fmlrc", "ratatosk", "lordec")
METHOD_FIELDS = {
    "fmlrc": ("fmlrc_k1", "fmlrc_k2"),
    "ratatosk": ("ratatosk_k1", "ratatosk_k2"),
    "lordec": ("lordec_k", "lordec_solid"),
}
METAQUAST_REPORTS = {
    "0.99": Path("metaquast/combined_reference/report.tsv"),
    "0.9999": Path("metaquast.ambiguity9999/combined_reference/report.tsv"),
}
QUAST_REPORTS = {"NA": Path("quast/report.tsv")}

sys.path.insert(0, str(BENCHMARK / "scripts"))
from method_config import resolve_coverage_parameters  # noqa: E402
from parse_metaquast import parse_report  # noqa: E402
from parse_resources import parse_resource_text  # noqa: E402
from run_layout import derive_run_group  # noqa: E402


@dataclass(frozen=True)
class Target:
    dataset: str
    coverage: str
    run_label: str
    method: str
    parameters: dict[str, int]
    dataset_config: Path
    run_config_dir: Path
    evaluation_tool: str

    @property
    def key(self) -> tuple[str, str, str]:
        return self.dataset, self.coverage, self.method

    @property
    def target_id(self) -> str:
        return ":".join(self.key)

    @property
    def run_group(self) -> str:
        return f"{self.dataset}_{self.run_label}"

    @property
    def generated_run_base(self) -> str:
        return f"{self.run_group}_{self.method}_tool_default"

    @property
    def signature(self) -> str:
        return method_signature(self.method, self.parameters)


@dataclass(frozen=True)
class RunCandidate:
    root: Path
    provenance_path: Path
    provenance: dict[str, Any]


@dataclass
class AuditRecord:
    target: Target
    status: str
    reason: str
    config_source: str
    job_config: Path | None
    run_group: str
    run_id: str
    run_root: Path
    comparator_count: int
    missing_scores: tuple[str, ...] = ()

    @property
    def priority(self) -> str:
        return "comparator" if self.comparator_count else "remaining"


MANIFEST_FIELDS = [
    "target_id", "dataset", "coverage", "run_label", "method",
    "parameters", "evaluation_tool", "status", "reason", "priority",
    "comparator_count", "config_source", "job_config", "dataset_config",
    "run_group", "run_id", "run_root", "missing_scores", "command",
]


def load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"Expected a YAML mapping: {path}")
    return value


def deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def build_targets(root: Path = ROOT, matrix_path: Path = DEFAULT_CONFIG) -> list[Target]:
    matrix = load_yaml(matrix_path)
    methods = matrix.get("methods") or {}
    if tuple(methods) != METHOD_ORDER:
        raise ValueError(f"methods must be ordered exactly as {METHOD_ORDER}")
    targets: list[Target] = []
    seen: set[tuple[str, str, str]] = set()
    for dataset_entry in matrix.get("datasets") or []:
        dataset_config = root / dataset_entry["config"]
        dataset_data = load_yaml(dataset_config)
        dataset_id = str(dataset_data["dataset"]["id"])
        if dataset_id != str(dataset_entry["id"]):
            raise ValueError(f"Dataset id mismatch in {dataset_config}: {dataset_id}")
        evaluation_tool = str(dataset_data.get("evaluation", {}).get("tool", "metaquast"))
        if evaluation_tool not in {"quast", "metaquast"}:
            raise ValueError(f"Unsupported evaluation tool: {evaluation_tool}")
        labels = {str(k): str(v) for k, v in (dataset_entry.get("run_labels") or {}).items()}
        run_config_dir = root / dataset_entry["run_config_dir"]
        for coverage, reads in dataset_data["inputs"]["short_reads"].items():
            if reads in (None, ""):
                continue
            coverage = str(coverage)
            run_label = labels.get(coverage, coverage)
            for method in METHOD_ORDER:
                target = Target(
                    dataset=dataset_id,
                    coverage=coverage,
                    run_label=run_label,
                    method=method,
                    parameters={key: int(value) for key, value in methods[method].items()},
                    dataset_config=dataset_config,
                    run_config_dir=run_config_dir,
                    evaluation_tool=evaluation_tool,
                )
                if target.key in seen:
                    raise ValueError(f"Duplicate target: {target.target_id}")
                seen.add(target.key)
                targets.append(target)
    return targets


def relevant_parameters(values: dict[str, Any], method: str) -> dict[str, int | None]:
    return {field: values.get(field) for field in METHOD_FIELDS[method]}


def method_signature(method: str, values: dict[str, Any]) -> str:
    if method == "fmlrc":
        return f"k{values['fmlrc_k1']}_k{values['fmlrc_k2']}"
    if method == "ratatosk":
        return f"k{values['ratatosk_k1']}_k{values['ratatosk_k2']}"
    if method == "lordec":
        return f"k{values['lordec_k']}_ls{values['lordec_solid']}"
    raise ValueError(f"Unsupported method: {method}")


def parameters_match(values: dict[str, Any], target: Target) -> bool:
    return all(values.get(field) == expected for field, expected in target.parameters.items())


def effective_job_parameters(target: Target, job_path: Path, root: Path = ROOT) -> dict[str, Any]:
    merged = load_yaml(root / "benchmark/config/common.yaml")
    merged = deep_merge(merged, load_yaml(target.dataset_config))
    merged = deep_merge(merged, load_yaml(job_path))
    _, values = resolve_coverage_parameters(merged, target.coverage)
    return values


def exact_job_configs(target: Target, root: Path = ROOT) -> list[Path]:
    matches: list[Path] = []
    if not target.run_config_dir.is_dir():
        return matches
    for path in sorted(target.run_config_dir.glob("*.yaml")):
        data = load_yaml(path)
        run = data.get("run") or {}
        if str(run.get("coverage")) != target.coverage or run.get("method") != target.method:
            continue
        if parameters_match(effective_job_parameters(target, path, root), target):
            matches.append(path)
    return matches


def generated_job_config(target: Target) -> str:
    lines = [
        f"evaluation: {{tool: {target.evaluation_tool}}}",
        "run: {id: %s, coverage: %s, method: %s, parameter_set: tool_default}" % (
            target.generated_run_base, target.coverage, target.method,
        ),
        "parameter_profile: study",
    ]
    lines.extend(f"{key}: {value}" for key, value in target.parameters.items())
    return "\n".join(lines) + "\n"


def planned_layout(
    target: Target, job_config: Path | None, runs_root: Path = RUNS_ROOT,
) -> tuple[str, str, Path]:
    if job_config is None:
        run_base = target.generated_run_base
    else:
        run = load_yaml(job_config).get("run") or {}
        run_base = str(run.get("id") or target.generated_run_base)
    run_id = f"{run_base}_{target.signature}"
    run_group = derive_run_group(run_base, target.method)
    return run_group, run_id, runs_root / run_group / run_id


def discover_runs(runs_root: Path = RUNS_ROOT) -> list[RunCandidate]:
    result: list[RunCandidate] = []
    for path in sorted(runs_root.glob("*/*/benchmark/provenance.json")):
        try:
            provenance = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        result.append(RunCandidate(path.parents[1], path, provenance))
    return result


def candidate_values(candidate: RunCandidate, coverage: str) -> dict[str, Any] | None:
    return (candidate.provenance.get("parameters_by_coverage") or {}).get(coverage)


def candidate_matches_target(candidate: RunCandidate, target: Target) -> bool:
    provenance = candidate.provenance
    values = candidate_values(candidate, target.coverage)
    return bool(
        provenance.get("dataset") == target.dataset
        and target.method in (provenance.get("methods") or [])
        and values
        and parameters_match(values, target)
    )


def candidate_matches_group(candidate: RunCandidate, target: Target) -> bool:
    provenance = candidate.provenance
    return bool(
        provenance.get("dataset") == target.dataset
        and target.method in (provenance.get("methods") or [])
        and candidate_values(candidate, target.coverage)
    )


def report_paths(candidate: RunCandidate, target: Target) -> dict[str, Path]:
    base = candidate.root / "output" / f"short_{target.coverage}" / target.method
    variants = METAQUAST_REPORTS if target.evaluation_tool == "metaquast" else QUAST_REPORTS
    return {score: base / relative for score, relative in variants.items()}


def assess_candidate(candidate: RunCandidate, target: Target) -> tuple[str, str, tuple[str, ...]]:
    corrected = candidate.root / "output" / f"short_{target.coverage}" / target.method / "corrected.fa"
    resources = candidate.root / "benchmark" / f"short_{target.coverage}" / target.method / "resources.time.txt"
    if not corrected.is_file() or corrected.stat().st_size == 0:
        return "invalid", f"missing or empty corrected output: {corrected}", ()
    if not resources.is_file() or resources.stat().st_size == 0:
        return "invalid", f"missing or empty resources: {resources}", ()
    try:
        parsed_resources = parse_resource_text(resources.read_text())
    except (OSError, ValueError) as error:
        return "invalid", f"invalid resources: {error}", ()
    if parsed_resources["exit_code"] != 0:
        return "invalid", f"non-zero resource exit code: {parsed_resources['exit_code']}", ()
    missing: list[str] = []
    for score, path in report_paths(candidate, target).items():
        if not path.is_file() or path.stat().st_size == 0:
            missing.append(score)
            continue
        try:
            parse_report(path)
        except (OSError, ValueError) as error:
            return "invalid", f"invalid report {path}: {error}", ()
    if missing:
        return "resume_evaluation", "missing evaluation reports", tuple(missing)
    return "complete", "validated correction, resources, and evaluation", ()


def has_unprovenanced_artifacts(run_root: Path) -> bool:
    for relative in ("output", "benchmark"):
        directory = run_root / relative
        if directory.is_dir() and any(path.is_file() and path.stat().st_size for path in directory.rglob("*")):
            return True
    return False


def audit_target(target: Target, runs: list[RunCandidate], root: Path = ROOT) -> AuditRecord:
    configs = exact_job_configs(target, root)
    if len(configs) > 1:
        group, run_id, run_root = planned_layout(target, configs[0])
        return AuditRecord(target, "invalid", "multiple exact job configs", "ambiguous", None,
                           group, run_id, run_root, 0)
    job_config = configs[0] if configs else None
    config_source = "existing" if job_config else "generated"
    group, run_id, run_root = planned_layout(target, job_config)
    matching = [candidate for candidate in runs if candidate_matches_target(candidate, target)]
    comparators = []
    for candidate in runs:
        if not candidate_matches_group(candidate, target) or candidate_matches_target(candidate, target):
            continue
        status, _, _ = assess_candidate(candidate, target)
        if status in {"complete", "resume_evaluation"}:
            comparators.append(candidate)
    if len(matching) > 1:
        return AuditRecord(target, "invalid", "multiple semantic default runs", config_source,
                           job_config, group, run_id, run_root, len(comparators))
    if matching:
        candidate = matching[0]
        status, reason, missing = assess_candidate(candidate, target)
        return AuditRecord(
            target, status, reason, config_source, job_config,
            candidate.root.parent.name,
            str(candidate.provenance.get("run_id") or candidate.root.name),
            candidate.root, len(comparators), missing,
        )
    if has_unprovenanced_artifacts(run_root):
        return AuditRecord(target, "invalid", "planned run has artifacts but no matching provenance",
                           config_source, job_config, group, run_id, run_root, len(comparators))
    return AuditRecord(target, "new", "no matching semantic run", config_source,
                       job_config, group, run_id, run_root, len(comparators))


def audit_all(root: Path = ROOT, matrix_path: Path = DEFAULT_CONFIG) -> list[AuditRecord]:
    runs = discover_runs(root / "benchmark/runs")
    return [audit_target(target, runs, root) for target in build_targets(root, matrix_path)]


def record_row(record: AuditRecord) -> dict[str, str | int]:
    target = record.target
    config_display = str(record.job_config) if record.job_config else "<generated>"
    command = f"DATASET_CONFIG={target.dataset_config} {RUN_ONE} {config_display}"
    return {
        "target_id": target.target_id,
        "dataset": target.dataset,
        "coverage": target.coverage,
        "run_label": target.run_label,
        "method": target.method,
        "parameters": json.dumps(target.parameters, sort_keys=True, separators=(",", ":")),
        "evaluation_tool": target.evaluation_tool,
        "status": record.status,
        "reason": record.reason,
        "priority": record.priority,
        "comparator_count": record.comparator_count,
        "config_source": record.config_source,
        "job_config": config_display,
        "dataset_config": str(target.dataset_config),
        "run_group": record.run_group,
        "run_id": record.run_id,
        "run_root": str(record.run_root),
        "missing_scores": ",".join(record.missing_scores),
        "command": command,
    }


def write_manifest(path: Path, records: Iterable[AuditRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with open(temporary, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_FIELDS, delimiter="\t")
        writer.writeheader()
        writer.writerows(record_row(record) for record in records)
    os.replace(temporary, path)


def shard_records(records: list[AuditRecord], count: int, index: int) -> list[AuditRecord]:
    if count < 1:
        raise ValueError("shard count must be positive")
    if not 0 <= index < count:
        raise ValueError("shard index must satisfy 0 <= index < shard count")
    ordered = sorted(records, key=lambda r: (r.target.dataset, r.target.coverage, r.target.method))
    return [record for position, record in enumerate(ordered) if position % count == index]


def safe_slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._-")
