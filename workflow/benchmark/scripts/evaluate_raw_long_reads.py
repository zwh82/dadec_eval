#!/usr/bin/env python3
"""Evaluate the raw long-read input of every benchmark dataset config.

Results are intentionally outside ``benchmark/runs``: these are dataset input
baselines, not outputs of a correction-method run.
"""

import argparse
import csv
import gzip
import os
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from prepare_reference import prepare as prepare_reference


def resolve_path(value, root):
    path = Path(value)
    return path if path.is_absolute() else root / path


def open_text(path):
    return gzip.open(path, "rt") if str(path).endswith(".gz") else open(path, "rt")


def prepare_reads(source, destination):
    """Copy FASTA or stream-convert FASTQ to FASTA without touching the input."""
    with open_text(source) as handle:
        first = handle.read(1)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    if first == ">":
        with open_text(source) as inp, open(temporary, "w") as out:
            shutil.copyfileobj(inp, out)
    elif first == "@":
        with open_text(source) as inp, open(temporary, "w") as out:
            while True:
                header = inp.readline()
                if not header:
                    break
                sequence = inp.readline()
                plus = inp.readline()
                quality = inp.readline()
                if not sequence or not plus or not quality or not header.startswith("@") or not plus.startswith("+"):
                    raise ValueError(f"Malformed FASTQ: {source}")
                out.write(">" + header[1:])
                out.write(sequence)
    else:
        raise ValueError(f"Unrecognized or empty FASTA/FASTQ input: {source}")
    os.replace(temporary, destination)


def is_current(report, inputs):
    return report.is_file() and report.stat().st_size > 0 and all(
        report.stat().st_mtime >= path.stat().st_mtime for path in inputs
    )


def write_summary(path, rows):
    fields = [
        "config", "dataset", "long_read_label", "evaluation_tool", "long_reads", "genome_map",
        "output_dir", "report", "status", "message",
    ]
    temporary = path.with_suffix(path.suffix + ".tmp")
    with open(temporary, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)


def evaluate(config_path, config, long_read_label, long_read_path, root, output_root, threads, force):
    dataset = config["dataset"]["id"]
    tool = config["evaluation"]["tool"].lower()
    if tool not in {"metaquast", "quast"}:
        raise ValueError(f"{config_path}: unsupported evaluation.tool {tool!r}")

    source = resolve_path(long_read_path, root)
    genome_map = resolve_path(config["inputs"]["genome_map"], root)
    if not source.is_file():
        raise FileNotFoundError(source)
    if not genome_map.is_file():
        raise FileNotFoundError(genome_map)

    output_dir = output_root / config_path.stem / long_read_label
    reads = output_dir / "raw_long_reads.fa"
    reference = output_dir / "reference.fa"
    mapping = output_dir / "contig_to_genome.tsv"
    report = output_dir / ("combined_reference/report.tsv" if tool == "metaquast" else "report.tsv")
    row = {
        "config": config_path.name,
        "dataset": dataset,
        "long_read_label": long_read_label,
        "evaluation_tool": tool,
        "long_reads": str(source),
        "genome_map": str(genome_map),
        "output_dir": str(output_dir),
        "report": str(report),
        "status": "",
        "message": "",
    }

    if not force and is_current(report, [source, genome_map]):
        row.update(status="skipped", message="current report exists")
        return row

    output_dir.mkdir(parents=True, exist_ok=True)
    if force or not reads.is_file() or reads.stat().st_mtime < source.stat().st_mtime:
        prepare_reads(source, reads)
    if force or not reference.is_file() or reference.stat().st_mtime < genome_map.stat().st_mtime:
        prepare_reference(genome_map, int(config["dataset"]["expected_genomes"]), reference, mapping)

    temporary = output_dir.with_name(output_dir.name + ".tmp")
    if temporary.exists():
        shutil.rmtree(temporary)
    temporary.mkdir()
    common = yaml.safe_load((SCRIPT_DIR.parent / "config" / "common.yaml").read_text())
    executable = common["tools"][tool]
    command = [executable, "-r", str(reference), "-t", str(threads), "--min-contig", "500", "--fast"]
    if tool == "metaquast":
        command += ["--ambiguity-usage", "all", "--ambiguity-score", "0.9999"]
    command += ["-o", str(temporary), str(reads)]
    log = output_dir / f"{tool}.log"
    with open(log, "w") as handle:
        handle.write("$ " + " ".join(command) + "\n")
        subprocess.run(command, check=True, stdout=handle, stderr=subprocess.STDOUT)

    temporary_report = temporary / ("combined_reference/report.tsv" if tool == "metaquast" else "report.tsv")
    if not temporary_report.is_file() or temporary_report.stat().st_size == 0:
        raise RuntimeError(f"{tool} completed without report: {temporary_report}")
    keep = {reads.name, reference.name, mapping.name, log.name}
    for item in output_dir.iterdir():
        if item.name in keep:
            continue
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()
    for item in temporary.iterdir():
        shutil.move(str(item), str(output_dir / item.name))
    temporary.rmdir()
    row.update(status="completed", message="")
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config-dir", type=Path, default=SCRIPT_DIR.parent / "config" / "datasets")
    parser.add_argument("--output-root", type=Path, default=SCRIPT_DIR.parent / "results" / "raw_long_reads")
    parser.add_argument("--threads", type=int, default=int(os.environ.get("QUAST_THREADS", "64")))
    parser.add_argument("--force", action="store_true", help="Re-run reports even when they are current.")
    args = parser.parse_args()
    if args.threads < 1:
        parser.error("--threads must be positive")

    root = SCRIPT_DIR.parents[1]
    args.output_root.mkdir(parents=True, exist_ok=True)
    rows = []
    failures = []
    for config_path in sorted(args.config_dir.glob("*.yaml")):
        config = yaml.safe_load(config_path.read_text())
        inputs = config.get("inputs", {})
        # Zymo's full long-read set is only the source for its subsamples and
        # is not part of the requested raw-input baseline matrix.
        targets = [] if config_path.stem == "zymo" else [("full", inputs["long_reads"])]
        targets.extend((str(label), path) for label, path in (inputs.get("long_read_subsamples") or {}).items())
        for long_read_label, long_read_path in targets:
            try:
                row = evaluate(
                    config_path, config, long_read_label, long_read_path,
                    root, args.output_root, args.threads, args.force,
                )
                print(f"[{row['status']}] {config_path.name}:{long_read_label}", flush=True)
            except Exception as error:
                row = {
                    "config": config_path.name, "dataset": config.get("dataset", {}).get("id", ""),
                    "long_read_label": long_read_label,
                    "evaluation_tool": config.get("evaluation", {}).get("tool", ""),
                    "long_reads": long_read_path,
                    "genome_map": config.get("inputs", {}).get("genome_map", ""),
                    "output_dir": str(args.output_root / config_path.stem / long_read_label), "report": "",
                    "status": "failed", "message": str(error),
                }
                failures.append(f"{config_path.name}:{long_read_label}")
                print(f"[failed] {config_path.name}:{long_read_label}: {error}", file=sys.stderr, flush=True)
            rows.append(row)
            write_summary(args.output_root / "summary.tsv", rows)
    if failures:
        raise SystemExit("Failed dataset configs: " + ", ".join(failures))


if __name__ == "__main__":
    main()
