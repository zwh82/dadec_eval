#!/usr/bin/env python3
"""Validation and result helpers for the Drosophila assembly workflow."""

import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml


ASSEMBLERS = ("canu", "hifiasm")
EXPECTED_BUILD_METHODS = {"dadec", "colormap", "proovread"}
EXPECTED_REUSE_METHODS = {
    "fmlrc",
    "ratatosk",
    "lordec",
    "f_hero",
    "r_hero",
    "l_hero",
}
QUAST_FIELDS = {
    "# contigs": "contigs",
    "Largest contig": "largest_contig",
    "Total length": "total_length",
    "N50": "n50",
    "# misassemblies": "misassemblies",
    "Genome fraction (%)": "genome_fraction_percent",
    "# mismatches per 100 kbp": "mismatches_per_100_kbp",
    "# indels per 100 kbp": "indels_per_100_kbp",
}
SUMMARY_FIELDS = [
    "method",
    "assembler",
    "mode",
    "assembly_path",
    "assembly_sha256",
    "source_path",
    "source_sha256",
    *QUAST_FIELDS.values(),
    "quast_report",
]


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def atomic_write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(text)
    os.replace(temporary, path)


def atomic_write_json(path, value):
    atomic_write_text(path, json.dumps(value, indent=2, sort_keys=True) + "\n")


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_path(value, project_root):
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = Path(project_root) / path
    return path.resolve()


def _require_mapping(value, label):
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a mapping")
    return value


def load_config(path):
    config_path = Path(path).resolve()
    raw = yaml.safe_load(config_path.read_text())
    config = _require_mapping(raw, "config")
    if config.get("schema_version") != 1:
        raise ValueError("schema_version must be 1")
    if not config.get("project_root"):
        raise ValueError("project_root is required")
    project_root = Path(config["project_root"]).resolve()
    config["config_path"] = config_path
    config["project_root"] = project_root
    config["output_root"] = resolve_path(config.get("output_root", ""), project_root)
    config["reference"] = resolve_path(config.get("reference", ""), project_root)
    tools = _require_mapping(config.get("tools"), "tools")
    config["tools"] = {
        name: resolve_path(tools.get(name, ""), project_root)
        for name in ("python", "time", "canu", "hifiasm", "quast")
    }
    methods = _require_mapping(config.get("methods"), "methods")
    normalized_methods = {}
    for method, entry in methods.items():
        entry = dict(_require_mapping(entry, f"methods.{method}"))
        mode = entry.get("mode")
        entry["mode"] = mode
        entry["skip_assemblers"] = list(entry.get("skip_assemblers", []))
        entry["skip_reasons"] = dict(entry.get("skip_reasons", {}))
        if mode == "build":
            entry["corrected_fasta"] = resolve_path(
                entry.get("corrected_fasta", ""), project_root
            )
        elif mode == "reuse":
            assemblies = _require_mapping(
                entry.get("assemblies"), f"methods.{method}.assemblies"
            )
            entry["assemblies"] = {
                assembler: resolve_path(assemblies.get(assembler, ""), project_root)
                for assembler in ASSEMBLERS
            }
        normalized_methods[str(method)] = entry
    config["methods"] = normalized_methods
    return config


def matrix(config):
    """Return enabled method/assembler cells."""
    rows = []
    for method, entry in config["methods"].items():
        for assembler in ASSEMBLERS:
            if assembler in entry.get("skip_assemblers", []):
                continue
            source = (
                entry["corrected_fasta"]
                if entry["mode"] == "build"
                else entry["assemblies"][assembler]
            )
            rows.append(
                {
                    "method": method,
                    "assembler": assembler,
                    "mode": entry["mode"],
                    "source": Path(source),
                }
            )
    return rows


def skipped_cells(config):
    rows = []
    for method, entry in config["methods"].items():
        reasons = entry.get("skip_reasons", {})
        for assembler in entry.get("skip_assemblers", []):
            rows.append(
                {
                    "method": method,
                    "assembler": assembler,
                    "reason": reasons.get(assembler, "disabled by configuration"),
                }
            )
    return rows


def validate_fasta(path, label="FASTA"):
    path = Path(path)
    if not path.is_file():
        raise ValueError(f"{label} does not exist: {path}")
    if path.stat().st_size == 0:
        raise ValueError(f"{label} is empty: {path}")
    with open(path, "rb") as handle:
        first = handle.read(1)
    if first != b">":
        raise ValueError(f"{label} does not start with '>': {path}")


def _nearest_existing(path):
    path = Path(path)
    while not path.exists():
        if path.parent == path:
            raise ValueError(f"No existing parent for {path}")
        path = path.parent
    return path


def _version(command):
    result = subprocess.run(
        [str(item) for item in command],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=True,
    )
    return result.stdout.strip()


def validate_config(config, check_disk=True, capture_versions=True):
    if config.get("dataset") != "drosophila":
        raise ValueError("dataset must be drosophila")
    if config.get("threads") != 64:
        raise ValueError("assembler threads must be exactly 64")
    quast_threads = config.get("quast_threads", config["threads"])
    if not isinstance(quast_threads, int) or quast_threads < 1:
        raise ValueError("quast_threads must be a positive integer")
    config["quast_threads"] = quast_threads
    if config.get("genome_size") != "137m":
        raise ValueError("genome_size must be 137m")
    if set(config["methods"]) != EXPECTED_BUILD_METHODS | EXPECTED_REUSE_METHODS:
        raise ValueError("methods must contain the expected nine-method matrix")
    actual_build = {
        name for name, entry in config["methods"].items() if entry["mode"] == "build"
    }
    actual_reuse = {
        name for name, entry in config["methods"].items() if entry["mode"] == "reuse"
    }
    if actual_build != EXPECTED_BUILD_METHODS:
        raise ValueError(f"invalid build methods: {sorted(actual_build)}")
    if actual_reuse != EXPECTED_REUSE_METHODS:
        raise ValueError(f"invalid reuse methods: {sorted(actual_reuse)}")
    for method, entry in config["methods"].items():
        invalid = set(entry["skip_assemblers"]) - set(ASSEMBLERS)
        if invalid:
            raise ValueError(f"invalid skipped assemblers for {method}: {sorted(invalid)}")
        if len(entry["skip_assemblers"]) != len(set(entry["skip_assemblers"])):
            raise ValueError(f"duplicate skipped assembler for {method}")
        if set(entry["skip_reasons"]) - set(entry["skip_assemblers"]):
            raise ValueError(f"skip_reasons must only name skipped assemblers for {method}")
    if not matrix(config):
        raise ValueError("at least one assembly cell must be enabled")

    root = config["project_root"]
    try:
        config["output_root"].relative_to(root)
    except ValueError as error:
        raise ValueError("output_root must be inside project_root") from error
    validate_fasta(config["reference"], "reference FASTA")
    for row in matrix(config):
        label = (
            f"{row['method']} corrected FASTA"
            if row["mode"] == "build"
            else f"{row['method']}/{row['assembler']} legacy assembly"
        )
        validate_fasta(row["source"], label)
    for name, path in config["tools"].items():
        if not path.is_file():
            raise ValueError(f"tool does not exist: {name}={path}")
        if name != "quast" and not os.access(path, os.X_OK):
            raise ValueError(f"tool is not executable: {name}={path}")

    free_gb = shutil.disk_usage(_nearest_existing(config["output_root"])).free / 10**9
    minimum = float(config.get("min_free_disk_gb", 0))
    if check_disk and free_gb < minimum:
        raise ValueError(
            f"insufficient free disk: {free_gb:.2f} GB available, {minimum:.2f} GB required"
        )
    versions = {}
    if capture_versions:
        versions = {
            "canu": _version([config["tools"]["canu"], "-version"]),
            "hifiasm": _version([config["tools"]["hifiasm"], "--version"]),
            "quast": _version(
                [
                    config["tools"]["python"],
                    config["tools"]["quast"],
                    "--version",
                ]
            ),
        }
    return {
        "status": "ok",
        "created_utc": utc_now(),
        "config": str(config["config_path"]),
        "dataset": config["dataset"],
        "threads": config["threads"],
        "quast_threads": config["quast_threads"],
        "genome_size": config["genome_size"],
        "matrix_size": len(matrix(config)),
        "skipped_cells": skipped_cells(config),
        "free_disk_gb": round(free_gb, 2),
        "versions": versions,
    }


def source_for(config, method, assembler):
    entry = config["methods"][method]
    if entry["mode"] == "build":
        return entry["corrected_fasta"]
    return entry["assemblies"][assembler]


def result_paths(config, method, assembler):
    root = config["output_root"] / method / assembler
    return {
        "root": root,
        "assembly": root / "assembly.fa",
        "provenance": root / "provenance.json",
        "quast": root / "quast",
        "report_tsv": root / "quast" / "report.tsv",
    }


def publish_fasta(
    source, output, provenance, method, assembler, mode, source_input=None
):
    source = Path(source).resolve()
    provenance_source = Path(source_input).resolve() if source_input else source
    output = Path(output)
    provenance = Path(provenance)
    validate_fasta(source, "source FASTA")
    validate_fasta(provenance_source, "provenance source FASTA")
    source_digest = sha256(provenance_source)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + ".tmp")
    if temporary.exists():
        temporary.unlink()
    command = [
        "cp",
        "--reflink=auto",
        "--preserve=mode",
        str(source),
        str(temporary),
    ]
    subprocess.run(command, check=True)
    validate_fasta(temporary, "materialized FASTA")
    output_digest = sha256(temporary)
    if provenance_source == source and source_digest != output_digest:
        temporary.unlink(missing_ok=True)
        raise ValueError(f"copy checksum mismatch: {source} -> {output}")
    os.replace(temporary, output)
    atomic_write_json(
        provenance,
        {
            "created_utc": utc_now(),
            "method": method,
            "assembler": assembler,
            "mode": mode,
            "source_path": str(provenance_source),
            "source_size": provenance_source.stat().st_size,
            "source_sha256": source_digest,
            "assembly_source_path": str(source),
            "assembly_path": str(output.resolve()),
            "assembly_size": output.stat().st_size,
            "assembly_sha256": output_digest,
        },
    )


def gfa_to_fasta(source, output, provenance, method, assembler, corrected_fasta):
    source = Path(source).resolve()
    output = Path(output)
    provenance = Path(provenance)
    corrected_fasta = Path(corrected_fasta).resolve()
    if not source.is_file() or source.stat().st_size == 0:
        raise ValueError(f"GFA does not exist or is empty: {source}")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + ".tmp")
    records = 0
    bases = 0
    with open(source) as input_handle, open(temporary, "w") as output_handle:
        for line_number, line in enumerate(input_handle, 1):
            if not line.startswith("S\t"):
                continue
            fields = line.rstrip("\n").split("\t")
            if len(fields) < 3 or fields[2] in {"", "*"}:
                raise ValueError(f"invalid GFA segment at {source}:{line_number}")
            output_handle.write(f">{fields[1]}\n{fields[2]}\n")
            records += 1
            bases += len(fields[2])
    if records == 0:
        temporary.unlink(missing_ok=True)
        raise ValueError(f"GFA contains no sequence-bearing S records: {source}")
    validate_fasta(temporary, "hifiasm FASTA")
    assembly_digest = sha256(temporary)
    os.replace(temporary, output)
    atomic_write_json(
        provenance,
        {
            "created_utc": utc_now(),
            "method": method,
            "assembler": assembler,
            "mode": "build",
            "source_path": str(corrected_fasta),
            "source_size": corrected_fasta.stat().st_size,
            "source_sha256": sha256(corrected_fasta),
            "gfa_path": str(source),
            "gfa_size": source.stat().st_size,
            "records": records,
            "bases": bases,
            "assembly_path": str(output.resolve()),
            "assembly_size": output.stat().st_size,
            "assembly_sha256": assembly_digest,
        },
    )


def parse_quast_report(path):
    found = {}
    with open(path, newline="") as handle:
        for row in csv.reader(handle, delimiter="\t"):
            if not row:
                continue
            label = row[0].strip()
            if label not in QUAST_FIELDS:
                continue
            values = [value.strip() for value in row[1:] if value.strip()]
            if len(values) != 1:
                raise ValueError(f"expected one QUAST value for {label!r} in {path}")
            found[label] = values[0]
    missing = [label for label in QUAST_FIELDS if label not in found]
    if missing:
        raise ValueError(f"missing QUAST rows in {path}: {', '.join(missing)}")
    return {QUAST_FIELDS[label]: found[label] for label in QUAST_FIELDS}


def summarize(config, output, manifest, preflight):
    rows = []
    entries = []
    for cell in matrix(config):
        paths = result_paths(config, cell["method"], cell["assembler"])
        validate_fasta(paths["assembly"], "result assembly")
        provenance = json.loads(paths["provenance"].read_text())
        metrics = parse_quast_report(paths["report_tsv"])
        row = {
            "method": cell["method"],
            "assembler": cell["assembler"],
            "mode": cell["mode"],
            "assembly_path": str(paths["assembly"]),
            "assembly_sha256": provenance["assembly_sha256"],
            "source_path": provenance["source_path"],
            "source_sha256": provenance["source_sha256"],
            **metrics,
            "quast_report": str(paths["report_tsv"]),
        }
        rows.append(row)
        entries.append({**row})
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + ".tmp")
    with open(temporary, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SUMMARY_FIELDS, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, output)
    preflight_value = json.loads(Path(preflight).read_text())
    atomic_write_json(
        manifest,
        {
            "status": "complete_with_skips" if skipped_cells(config) else "complete",
            "created_utc": utc_now(),
            "config": str(config["config_path"]),
            "preflight": preflight_value,
            "entries": entries,
            "skipped_cells": skipped_cells(config),
        },
    )


def verify(config):
    summary_path = config["output_root"] / "summary.tsv"
    manifest_path = config["output_root"] / "manifest.json"
    if not summary_path.is_file() or not manifest_path.is_file():
        raise ValueError("summary.tsv or manifest.json is missing")
    with open(summary_path, newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    expected_cells = matrix(config)
    if len(rows) != len(expected_cells):
        raise ValueError(f"summary must contain {len(expected_cells)} rows, found {len(rows)}")
    keys = {(row["method"], row["assembler"]) for row in rows}
    expected = {
        (cell["method"], cell["assembler"]) for cell in expected_cells
    }
    if keys != expected:
        raise ValueError("summary matrix does not match the configured matrix")
    manifest = json.loads(manifest_path.read_text())
    expected_status = "complete_with_skips" if skipped_cells(config) else "complete"
    if manifest.get("status") != expected_status or len(manifest.get("entries", [])) != len(expected_cells):
        raise ValueError("manifest is incomplete")
    if manifest.get("skipped_cells", []) != skipped_cells(config):
        raise ValueError("manifest skipped cells do not match configuration")
    for cell in expected_cells:
        paths = result_paths(config, cell["method"], cell["assembler"])
        validate_fasta(paths["assembly"], "result assembly")
        parse_quast_report(paths["report_tsv"])
        provenance = json.loads(paths["provenance"].read_text())
        if sha256(paths["assembly"]) != provenance["assembly_sha256"]:
            raise ValueError(f"assembly checksum mismatch: {paths['assembly']}")
        current_source = source_for(config, cell["method"], cell["assembler"])
        if sha256(current_source) != provenance["source_sha256"]:
            raise ValueError(f"source checksum changed: {current_source}")
    return {
        "status": expected_status,
        "matrix_size": len(expected_cells),
        "summary": str(summary_path),
        "manifest": str(manifest_path),
    }


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    preflight_parser = subparsers.add_parser("preflight")
    preflight_parser.add_argument("--config", required=True)
    preflight_parser.add_argument("--output", required=True)

    publish_parser = subparsers.add_parser("publish-fasta")
    publish_parser.add_argument("--input", required=True)
    publish_parser.add_argument("--output", required=True)
    publish_parser.add_argument("--provenance", required=True)
    publish_parser.add_argument("--method", required=True)
    publish_parser.add_argument("--assembler", choices=ASSEMBLERS, required=True)
    publish_parser.add_argument("--mode", choices=("build", "reuse"), required=True)
    publish_parser.add_argument("--source-input")

    gfa_parser = subparsers.add_parser("gfa-to-fasta")
    gfa_parser.add_argument("--input", required=True)
    gfa_parser.add_argument("--output", required=True)
    gfa_parser.add_argument("--provenance", required=True)
    gfa_parser.add_argument("--method", required=True)
    gfa_parser.add_argument("--assembler", choices=ASSEMBLERS, required=True)
    gfa_parser.add_argument("--corrected-fasta", required=True)

    summary_parser = subparsers.add_parser("summarize")
    summary_parser.add_argument("--config", required=True)
    summary_parser.add_argument("--output", required=True)
    summary_parser.add_argument("--manifest", required=True)
    summary_parser.add_argument("--preflight", required=True)

    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--config", required=True)

    args = parser.parse_args()
    if args.command == "preflight":
        config = load_config(args.config)
        atomic_write_json(args.output, validate_config(config))
    elif args.command == "publish-fasta":
        publish_fasta(
            args.input,
            args.output,
            args.provenance,
            args.method,
            args.assembler,
            args.mode,
            args.source_input,
        )
    elif args.command == "gfa-to-fasta":
        gfa_to_fasta(
            args.input,
            args.output,
            args.provenance,
            args.method,
            args.assembler,
            args.corrected_fasta,
        )
    elif args.command == "summarize":
        config = load_config(args.config)
        summarize(config, args.output, args.manifest, args.preflight)
    elif args.command == "verify":
        config = load_config(args.config)
        result = verify(config)
        print(json.dumps(result, indent=2))
    else:
        raise AssertionError(args.command)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(2)
