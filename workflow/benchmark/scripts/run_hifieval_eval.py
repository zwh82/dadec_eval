#!/usr/bin/env python3
"""Run the reproducible Hifieval evaluation configured by one YAML file."""

import argparse
import hashlib
import json
import math
import os
import shlex
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import yaml


HEADER_TRANSFORMS = {"none", "strip_after_colon"}


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def resolve_path(value, project_root):
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = project_root / path
    return path.resolve()


def require(mapping, key, context):
    if key not in mapping or mapping[key] in (None, ""):
        raise ValueError("missing {}.{}".format(context, key))
    return mapping[key]


@dataclass(frozen=True)
class EvalConfig:
    config_path: Path
    project_root: Path
    dataset_id: str
    run_id: str
    method: str
    corrected_fasta: Path
    raw_paf: Path
    reference: Path
    truth_maf: Path
    minimap2: Path
    hifieval: Path
    readseval: Path
    output_dir: Path
    environment: str
    threads: int
    header_transform: str
    read_mapping_mode: str
    min_free_disk_gb: float
    checksum_inputs: bool


def load_config(path):
    config_path = Path(path).expanduser().resolve()
    with config_path.open() as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError("configuration must contain a YAML mapping")
    if data.get("schema_version") != 1:
        raise ValueError("schema_version must be 1")

    project_root = resolve_path(
        require(data, "project_root", "config"), config_path.parent
    )
    dataset = require(data, "dataset", "config")
    run = require(data, "run", "config")
    inputs = require(data, "inputs", "config")
    tools = require(data, "tools", "config")
    if not all(isinstance(item, dict) for item in (dataset, run, inputs, tools)):
        raise ValueError("dataset, run, inputs, and tools must be YAML mappings")

    threads = int(data.get("threads", 1))
    if threads < 1:
        raise ValueError("threads must be at least 1")
    min_free_disk_gb = float(data.get("min_free_disk_gb", 1))
    if min_free_disk_gb < 0:
        raise ValueError("min_free_disk_gb cannot be negative")
    transform = data.get("header_transform", "none")
    if transform not in HEADER_TRANSFORMS:
        raise ValueError(
            "header_transform must be one of {}".format(
                ", ".join(sorted(HEADER_TRANSFORMS))
            )
        )
    read_mapping_mode = data.get("read_mapping_mode", "truth_interval")
    if read_mapping_mode not in {"truth_interval", "legacy_endpoint"}:
        raise ValueError(
            "read_mapping_mode must be truth_interval or legacy_endpoint"
        )

    return EvalConfig(
        config_path=config_path,
        project_root=project_root,
        dataset_id=str(require(dataset, "id", "dataset")),
        run_id=str(require(run, "id", "run")),
        method=str(require(run, "method", "run")),
        corrected_fasta=resolve_path(
            require(inputs, "corrected_fasta", "inputs"), project_root
        ),
        raw_paf=resolve_path(require(inputs, "raw_paf", "inputs"), project_root),
        reference=resolve_path(
            require(inputs, "reference", "inputs"), project_root
        ),
        truth_maf=resolve_path(
            require(inputs, "truth_maf", "inputs"), project_root
        ),
        minimap2=resolve_path(require(tools, "minimap2", "tools"), project_root),
        hifieval=resolve_path(require(tools, "hifieval", "tools"), project_root),
        readseval=resolve_path(
            require(tools, "readseval", "tools"), project_root
        ),
        output_dir=resolve_path(
            require(data, "output_dir", "config"), project_root
        ),
        environment=str(data.get("environment", "dadec_eval")),
        threads=threads,
        header_transform=transform,
        read_mapping_mode=read_mapping_mode,
        min_free_disk_gb=min_free_disk_gb,
        checksum_inputs=bool(data.get("checksum_inputs", True)),
    )


def normalize_read_id(read_id, transform):
    if transform == "strip_after_colon":
        return read_id.split(":", 1)[0]
    return read_id


def sample_fasta_ids(path, transform="none", limit=100):
    identifiers = []
    with Path(path).open() as handle:
        for line in handle:
            if line.startswith(">"):
                read_id = line[1:].split(None, 1)[0]
                identifiers.append(normalize_read_id(read_id, transform))
                if len(identifiers) >= limit:
                    break
    return identifiers


def sample_maf_read_ids(path, limit=100):
    identifiers = []
    sequence_index = 0
    with Path(path).open() as handle:
        for line in handle:
            if line.startswith("a"):
                sequence_index = 0
            elif line.startswith("s "):
                sequence_index += 1
                if sequence_index == 2:
                    fields = line.split()
                    if len(fields) >= 2:
                        identifiers.append(fields[1])
                        if len(identifiers) >= limit:
                            break
    return identifiers


def match_maf_read_ids(path, requested_ids):
    """Scan MAF truth until every sampled corrected-read ID is found."""
    requested = set(requested_ids)
    found = set()
    sequence_index = 0
    inspected = 0
    with Path(path).open() as handle:
        for line in handle:
            if line.startswith("a"):
                sequence_index = 0
            elif line.startswith("s "):
                sequence_index += 1
                if sequence_index == 2:
                    fields = line.split()
                    if len(fields) >= 2:
                        inspected += 1
                        if fields[1] in requested:
                            found.add(fields[1])
                            if found == requested:
                                break
    return found, inspected


def nearest_existing_parent(path):
    candidate = Path(path)
    while not candidate.exists():
        candidate = candidate.parent
    return candidate


def file_stat(path):
    stat = Path(path).stat()
    return {
        "path": str(Path(path).resolve()),
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
    }


def executable_version(path):
    result = subprocess.run(
        [str(path), "--version"],
        check=True,
        capture_output=True,
        text=True,
    )
    return (result.stdout or result.stderr).strip().splitlines()[0]


def preflight(config):
    inputs = {
        "corrected_fasta": config.corrected_fasta,
        "raw_paf": config.raw_paf,
        "reference": config.reference,
        "truth_maf": config.truth_maf,
    }
    for label, path in inputs.items():
        if not path.is_file() or path.stat().st_size == 0:
            raise FileNotFoundError("{} is missing or empty: {}".format(label, path))
    if not config.minimap2.is_file() or not os.access(config.minimap2, os.X_OK):
        raise FileNotFoundError(
            "minimap2 is missing or not executable: {}".format(config.minimap2)
        )
    for label, path in (
        ("hifieval", config.hifieval),
        ("readseval", config.readseval),
    ):
        if not path.is_file() or not os.access(path, os.R_OK):
            raise FileNotFoundError("{} script is not readable: {}".format(label, path))
    if Path(sys.prefix).name != config.environment:
        raise RuntimeError(
            "expected conda environment {!r}, running from {!r}".format(
                config.environment, Path(sys.prefix).name
            )
        )

    fasta_ids = sample_fasta_ids(
        config.corrected_fasta, config.header_transform
    )
    if not fasta_ids:
        raise ValueError("no FASTA identifiers found in {}".format(config.corrected_fasta))
    matched_ids, inspected_maf_ids = match_maf_read_ids(
        config.truth_maf, fasta_ids
    )
    if inspected_maf_ids == 0:
        raise ValueError("no read truth identifiers found in {}".format(config.truth_maf))
    missing_ids = sorted(set(fasta_ids).difference(matched_ids))
    if missing_ids:
        raise ValueError(
            "{} of {} sampled corrected FASTA IDs are absent from MAF truth "
            "(examples: {})".format(
                len(missing_ids),
                len(set(fasta_ids)),
                ", ".join(missing_ids[:5]),
            )
        )

    disk_root = nearest_existing_parent(config.output_dir)
    free_disk_gb = shutil.disk_usage(disk_root).free / 1024**3
    if free_disk_gb < config.min_free_disk_gb:
        raise RuntimeError(
            "only {:.1f} GiB free at {}; {:.1f} GiB required".format(
                free_disk_gb, disk_root, config.min_free_disk_gb
            )
        )
    return {
        "status": "ok",
        "dataset": config.dataset_id,
        "run_id": config.run_id,
        "environment": config.environment,
        "python": sys.executable,
        "minimap2": str(config.minimap2),
        "minimap2_version": executable_version(config.minimap2),
        "inputs": {label: file_stat(path) for label, path in inputs.items()},
        "sampled_fasta_ids": len(fasta_ids),
        "inspected_maf_ids": inspected_maf_ids,
        "sample_id_overlap": len(matched_ids),
        "sample_matching_id": sorted(matched_ids)[0],
        "free_disk_gb": round(free_disk_gb, 2),
        "required_free_disk_gb": config.min_free_disk_gb,
    }


def stream_clean_fasta(source, destination, transform):
    destination = Path(destination)
    temporary = destination.with_name(destination.name + ".tmp")
    temporary.parent.mkdir(parents=True, exist_ok=True)
    with Path(source).open() as source_handle, temporary.open("w") as output_handle:
        for line in source_handle:
            if line.startswith(">"):
                read_id = line[1:].split(None, 1)[0]
                output_handle.write(
                    ">{}\n".format(normalize_read_id(read_id, transform))
                )
            else:
                output_handle.write(line)
    os.replace(temporary, destination)


def build_minimap2_command(config, corrected_fasta, corrected_paf, threads):
    return [
        str(config.minimap2),
        "-t",
        str(threads),
        "-c",
        "--secondary=no",
        "--paf-no-hit",
        "--cs",
        str(config.reference),
        str(corrected_fasta),
    ]


def build_hifieval_command(config, corrected_paf, prefix):
    return [
        sys.executable,
        str(config.hifieval),
        "-o",
        str(prefix),
        "-r",
        str(config.raw_paf),
        "-c",
        str(corrected_paf),
        "-h",
        str(config.reference),
    ]


def build_readseval_command(config, corrected_paf, prefix):
    return [
        sys.executable,
        str(config.readseval),
        "-f",
        "-o",
        str(prefix),
        "-r",
        str(config.raw_paf),
        "-c",
        str(corrected_paf),
        "--maf",
        str(config.truth_maf),
        "--mapping-mode",
        config.read_mapping_mode,
    ]


def stage_token(command, dependencies):
    return {
        "command": [str(value) for value in command],
        "dependencies": [file_stat(path) for path in dependencies],
    }


def command_without_option_values(command, options):
    """Return a command with non-semantic option values normalized."""
    normalized = list(command)
    for index, value in enumerate(normalized[:-1]):
        if value in options:
            normalized[index + 1] = "<ignored>"
    return normalized


def tokens_are_equivalent(saved, current, ignored_command_options=()):
    if not ignored_command_options:
        return saved == current
    if not isinstance(saved, dict) or not isinstance(current, dict):
        return False
    saved_copy = dict(saved)
    current_copy = dict(current)
    saved_copy["command"] = command_without_option_values(
        saved_copy.get("command", []), ignored_command_options
    )
    current_copy["command"] = command_without_option_values(
        current_copy.get("command", []), ignored_command_options
    )
    return saved_copy == current_copy


def stage_is_current(
    marker, outputs, token, ignored_command_options=()
):
    marker = Path(marker)
    if not marker.is_file() or any(
        not Path(path).is_file() or Path(path).stat().st_size == 0
        for path in outputs
    ):
        return False
    try:
        saved = json.loads(marker.read_text())
    except (OSError, ValueError):
        return False
    return saved.get("status") == "complete" and tokens_are_equivalent(
        saved.get("token"), token, ignored_command_options
    )


def atomic_write_json(path, data):
    path = Path(path)
    temporary = path.with_name(path.name + ".tmp")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, path)


def run_logged(command, log_path, stdout_path=None):
    start = time.monotonic()
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a") as log_handle:
        log_handle.write("[{}] $ {}\n".format(utc_now(), shlex.join(command)))
        log_handle.flush()
        if stdout_path is None:
            subprocess.run(
                command,
                check=True,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                text=True,
            )
        else:
            stdout_path = Path(stdout_path)
            stdout_path.parent.mkdir(parents=True, exist_ok=True)
            with stdout_path.open("w") as output_handle:
                subprocess.run(
                    command,
                    check=True,
                    stdout=output_handle,
                    stderr=log_handle,
                    text=True,
                )
        elapsed = time.monotonic() - start
        log_handle.write("[{}] completed in {:.3f} seconds\n".format(utc_now(), elapsed))
    return elapsed


def mark_stage(marker, token, elapsed_seconds):
    atomic_write_json(
        marker,
        {
            "status": "complete",
            "completed_utc": utc_now(),
            "elapsed_seconds": round(elapsed_seconds, 3),
            "token": token,
        },
    )


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def checksums_with_cache(paths, cache_path):
    cache_path = Path(cache_path)
    try:
        cache = json.loads(cache_path.read_text())
    except (OSError, ValueError):
        cache = {}
    result = {}
    for path in paths:
        stat = file_stat(path)
        key = stat["path"]
        cached = cache.get(key, {})
        if cached.get("size") == stat["size"] and cached.get("mtime_ns") == stat["mtime_ns"]:
            value = cached["sha256"]
        else:
            value = sha256(path)
        result[key] = {**stat, "sha256": value}
    atomic_write_json(cache_path, result)
    return result


def validate_base_eval(path):
    with Path(path).open() as handle:
        rows = [line.rstrip("\n").split("\t") for line in handle if line.strip()]
    expected_header = [
        "error_type",
        "chrName",
        "raw_errors",
        "corrected_errors",
        "oc",
        "cc",
        "uc",
        "FDR",
        "FNR",
        "TPR",
    ]
    if not rows or rows[0] != expected_header:
        raise ValueError("unexpected base-evaluation header in {}".format(path))
    if any(len(row) != 10 for row in rows[1:]):
        raise ValueError("non-rectangular base-evaluation table: {}".format(path))
    for row in rows[1:]:
        if any(not math.isfinite(float(value)) for value in row[7:10]):
            raise ValueError("non-finite metric in {}".format(path))


def validate_outputs(unfiltered_prefix, filtered_prefix):
    required = [
        Path(str(unfiltered_prefix) + ".base.eval.tsv"),
        Path(str(unfiltered_prefix) + ".hp.ErrorRate.tsv"),
        Path(str(filtered_prefix) + ".base.eval.tsv"),
        Path(str(filtered_prefix) + ".read.eval.tsv"),
    ]
    for path in required:
        if not path.is_file() or path.stat().st_size == 0:
            raise FileNotFoundError("expected output is missing or empty: {}".format(path))
    validate_base_eval(required[0])
    validate_base_eval(required[2])
    with required[1].open() as handle:
        hp_rows = [line.rstrip("\n").split("\t") for line in handle if line.strip()]
    if not hp_rows or hp_rows[0] != ["#HP Len", "OC rate", "UC rate"]:
        raise ValueError("unexpected homopolymer table header: {}".format(required[1]))
    if any(len(row) != 3 for row in hp_rows[1:]):
        raise ValueError("non-rectangular homopolymer table: {}".format(required[1]))


def run_pipeline(config, force=False, threads=None):
    report = preflight(config)
    threads = config.threads if threads is None else threads
    if threads < 1:
        raise ValueError("--threads must be at least 1")

    output = config.output_dir
    work_dir = output / "work"
    paf_dir = output / "paf"
    log_dir = output / "logs"
    state_dir = output / ".state"
    unfiltered_dir = output / "unfiltered"
    filtered_dir = output / "filtered"
    for directory in (
        work_dir,
        paf_dir,
        log_dir,
        state_dir,
        unfiltered_dir,
        filtered_dir,
    ):
        directory.mkdir(parents=True, exist_ok=True)
    complete_marker = output / ".complete"
    if complete_marker.exists():
        complete_marker.unlink()

    if config.header_transform == "none":
        prepared_fasta = config.corrected_fasta
    else:
        prepared_fasta = work_dir / "corrected.cleaned.fa"
        clean_command = [
            "internal:stream_clean_fasta",
            str(config.corrected_fasta),
            str(prepared_fasta),
            config.header_transform,
        ]
        clean_token = stage_token(clean_command, [config.corrected_fasta])
        clean_marker = state_dir / "clean_fasta.json"
        if force or not stage_is_current(clean_marker, [prepared_fasta], clean_token):
            start = time.monotonic()
            stream_clean_fasta(
                config.corrected_fasta,
                prepared_fasta,
                config.header_transform,
            )
            mark_stage(clean_marker, clean_token, time.monotonic() - start)

    corrected_paf = paf_dir / "corrected.paf"
    minimap_command = build_minimap2_command(
        config, prepared_fasta, corrected_paf, threads
    )
    align_token = stage_token(
        minimap_command, [config.minimap2, config.reference, prepared_fasta]
    )
    align_marker = state_dir / "align_corrected.json"
    if force or not stage_is_current(
        align_marker,
        [corrected_paf],
        align_token,
        ignored_command_options=("-t",),
    ):
        temporary_paf = corrected_paf.with_name(corrected_paf.name + ".tmp")
        if temporary_paf.exists():
            temporary_paf.unlink()
        elapsed = run_logged(
            minimap_command,
            log_dir / "minimap2.log",
            stdout_path=temporary_paf,
        )
        if temporary_paf.stat().st_size == 0:
            raise RuntimeError("minimap2 produced an empty corrected PAF")
        os.replace(temporary_paf, corrected_paf)
        mark_stage(align_marker, align_token, elapsed)

    unfiltered_prefix = unfiltered_dir / config.method
    hifieval_command = build_hifieval_command(
        config, corrected_paf, unfiltered_prefix
    )
    hifieval_outputs = [
        Path(str(unfiltered_prefix) + suffix)
        for suffix in (
            ".summary.tsv",
            ".rdlvl.eval.tsv",
            ".metric.eval.tsv",
            ".base.eval.tsv",
            ".hp.bed",
            ".hp.ErrorRate.tsv",
        )
    ]
    hifieval_token = stage_token(
        hifieval_command,
        [config.hifieval, config.raw_paf, corrected_paf, config.reference],
    )
    hifieval_marker = state_dir / "hifieval_unfiltered.json"
    if force or not stage_is_current(
        hifieval_marker, hifieval_outputs, hifieval_token
    ):
        elapsed = run_logged(
            hifieval_command, log_dir / "hifieval_unfiltered.log"
        )
        mark_stage(hifieval_marker, hifieval_token, elapsed)

    filtered_prefix = filtered_dir / config.method
    readseval_command = build_readseval_command(
        config, corrected_paf, filtered_prefix
    )
    readseval_outputs = [
        Path(str(filtered_prefix) + ".read.eval.tsv"),
        Path(str(filtered_prefix) + ".base.eval.tsv"),
    ]
    readseval_token = stage_token(
        readseval_command,
        [config.readseval, config.raw_paf, corrected_paf, config.truth_maf],
    )
    readseval_marker = state_dir / "readseval_filtered.json"
    if force or not stage_is_current(
        readseval_marker, readseval_outputs, readseval_token
    ):
        elapsed = run_logged(
            readseval_command, log_dir / "readseval_filtered.log"
        )
        mark_stage(readseval_marker, readseval_token, elapsed)

    validate_outputs(unfiltered_prefix, filtered_prefix)
    input_paths = [
        config.config_path,
        config.corrected_fasta,
        config.raw_paf,
        config.reference,
        config.truth_maf,
        config.minimap2,
        config.hifieval,
        config.readseval,
    ]
    checksums = (
        checksums_with_cache(input_paths, state_dir / "checksums.json")
        if config.checksum_inputs
        else {str(path): file_stat(path) for path in input_paths}
    )
    stages = {}
    for marker in sorted(state_dir.glob("*.json")):
        if marker.name != "checksums.json":
            stages[marker.stem] = json.loads(marker.read_text())
    provenance = {
        "status": "complete",
        "completed_utc": utc_now(),
        "dataset": config.dataset_id,
        "run_id": config.run_id,
        "method": config.method,
        "threads": threads,
        "header_transform": config.header_transform,
        "read_mapping_mode": config.read_mapping_mode,
        "preflight": report,
        "inputs_and_tools": checksums,
        "stages": stages,
        "outputs": {
            "corrected_paf": str(corrected_paf),
            "unfiltered_prefix": str(unfiltered_prefix),
            "filtered_prefix": str(filtered_prefix),
        },
    }
    atomic_write_json(output / "provenance.json", provenance)
    complete_marker.write_text(utc_now() + "\n")
    return provenance


def build_parser():
    parser = argparse.ArgumentParser(
        description="Run one configured Hifieval evaluation"
    )
    parser.add_argument("config", help="Hifieval evaluation YAML")
    parser.add_argument(
        "--preflight",
        action="store_true",
        help="validate inputs, environment, IDs, tools, and disk space only",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="rerun completed stages even when their inputs are unchanged",
    )
    parser.add_argument("--threads", type=int, help="override minimap2 threads")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    config = load_config(args.config)
    if args.preflight:
        print(json.dumps(preflight(config), indent=2, sort_keys=True))
        return 0
    provenance = run_pipeline(config, force=args.force, threads=args.threads)
    print(
        "Hifieval evaluation complete: {}".format(
            provenance["outputs"]["unfiltered_prefix"]
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print("run_hifieval_eval: error: {}".format(exc), file=sys.stderr)
        raise SystemExit(2)
