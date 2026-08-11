#!/usr/bin/env python3
"""Build the compact, auditable DADEC paper-evaluation bundle."""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
import re
import shutil
import subprocess
from pathlib import Path


BUNDLE = Path(__file__).resolve().parent
PROJECT = BUNDLE.parent
BENCHMARK = PROJECT / "benchmark"
SIMULATION_SCRIPTS = PROJECT / "scripts"
LEGACY_RESULTS = Path("/home/yczhang/zyc/final_result")

SOURCE_SUFFIXES = {".py", ".sh", ".smk", ".md", ".yaml", ".yml", ".tsv", ".json"}
SOURCE_EXACT = {"Snakefile", "Snakefile.ecoli3", "Makefile"}
SIMULATION_SUFFIXES = {".py", ".sh", ".ini"}
SKIP_PARTS = {".git", ".snakemake", "__pycache__", "logs", "tmp", "work", "dev_runs"}
RESULT_EXACT = {
    "report.tsv", "transposed_report.tsv", "report.txt", "report.tex",
    "summary.tsv", "run_manifest.tsv", "manifest.json", "provenance.json",
    "metrics.json", "metrics.txt", "status.json", "benchmark.txt",
}
RESULT_MARKERS = (
    "comparative", "selected_results", "best_parameter_runs", "all_parameter_runs",
    "coverage_method_status", "technology_method_status", "quality_sensitivity",
    "subsampling_metrics", "assembly_results", "classification", "ablation",
    "benchmark_tables", "default_parameter", "resource", "runtime", "memory", "table_",
)
RESULT_SUFFIXES = {".tsv", ".csv", ".json", ".tex", ".txt"}
MAX_RESULT_BYTES = 20 * 1024 * 1024
MAX_METADATA_BYTES = 10 * 1024 * 1024
EXCLUDED_RESULT_PARTS = {
    "logs", "paf", "work", ".state", "icarus_viewers", "contigs_reports",
    "minimap_output", "quast_corrected_input", "reads_stats",
}
EXCLUDED_RESULT_ROOTS = {"old_before_20260728"}
# These compact run groups support the Zymo long-read-subsampling table, whose
# imported summary rows do not carry report paths that can be discovered from
# the aggregate TSV itself.
ADDITIONAL_PAPER_RUN_GROUPS = {
    "zymo_5pct", "zymo_10pct", "zymo_20pct", "zymo_30pct", "zymo_40pct",
    "ecoli3_error_readcount_hiseq", "ecoli3_error_readcount_miseq",
    "ecoli3_error_readcount_nextseq", "ecoli3_error_readcount_novaseq",
}
EXCLUDED_PAPER_RUN_GROUPS = {"arabidopsis_15x", "arabidopsis_25x"}
ABSOLUTE_PATH_RE = re.compile(r"(?<![A-Za-z0-9_.-])(/(?:home|data|mnt|scratch|work)/[^\s'\"\],}]+)")
METADATA_SOURCES = {
    "30S-BA": PROJECT / "data" / "30strains",
    "30S-NU": Path("/home/yczhang/zyc/final_result/30strains/data"),
    "100S-BA": PROJECT / "data" / "100strains",
    "100S-NU": Path("/home/yczhang/zyc/final_result/100strains/data"),
}
METADATA_SUFFIXES = {".tsv", ".csv", ".txt", ".ini", ".md", ".sh", ".py", ".log"}
METADATA_PRUNED = {
    "bam", "source_genomes", "long_reads_quast", "quast", "metaquast",
    "__pycache__", ".snakemake", "corrected", "30_cor", "classification",
}
LEGACY_CODE_SUFFIXES = {".py", ".r", ".sh", ".yaml", ".yml", ".ini"}
PAPER_LEGACY_ROOTS = {
    "30strains", "100strains", "Arabidopsis", "Drosophila", "ecoil", "mhc", "zymo",
}
TRACE_COLLECTORS = {
    "Raw-read baselines": "workflow/benchmark/scripts/collect_summaries.py",
    "Short-read coverage sensitivity": "workflow/benchmark/work_scripts/final_collect_res/coverage_depths/collect_results.py; workflow/benchmark/work_scripts/final_collect_res/plot_coverage_depths.py",
    "Short-read quality sensitivity": "workflow/benchmark/work_scripts/final_collect_res/short_read_quality/collect_results.py",
    "Under/over-correction: E. coli": "workflow/benchmark/scripts/collect_hifieval_results.py; workflow/benchmark/work_scripts/hifieval/plot_oc_composition.py",
    "Under/over-correction: Arabidopsis": "workflow/benchmark/scripts/collect_hifieval_results.py; workflow/benchmark/work_scripts/hifieval/plot_oc_composition.py",
    "DADEC ablation": "workflow/benchmark/work_scripts/collect_ablation.py",
    "Strain classification": "workflow/benchmark/work_scripts/final_collect_res/collect_classification_30strains_legacy.py; workflow/benchmark/work_scripts/final_collect_res/plot_classification_macro.py",
    "Drosophila assembly": "workflow/benchmark/work_scripts/final_collect_res/drosophila_43x/collect_assembly_results.py",
    "Runtime and memory": "workflow/benchmark/scripts/combine_resources.py",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def clean_generated() -> None:
    for name in ("workflow", "config", "results", "runs", "metadata"):
        path = BUNDLE / name
        if path.exists():
            shutil.rmtree(path)
    for name in ("MANIFEST.tsv", "EXTERNAL_DATA.tsv"):
        path = BUNDLE / name
        if path.exists():
            path.unlink()


def copy_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def walk_files(root: Path, pruned_names: set[str]) -> list[Path]:
    files: list[Path] = []
    for current, directories, names in os.walk(root):
        directories[:] = sorted(
            name for name in directories
            if name not in pruned_names and not (Path(current) / name).is_symlink()
        )
        for name in sorted(names):
            path = Path(current) / name
            if path.is_file() and not path.is_symlink():
                files.append(path)
    return files


def source_files() -> list[Path]:
    selected: list[Path] = []
    source_pruned = SKIP_PARTS | {"results", "runs", "logs"}
    for path in walk_files(BENCHMARK, source_pruned):
        relative = path.relative_to(BENCHMARK)
        if path.name in SOURCE_EXACT or path.suffix.lower() in SOURCE_SUFFIXES:
            selected.append(path)
    return sorted(selected)


def simulation_files() -> list[Path]:
    """Return simulation/data-preparation code, excluding outputs and caches."""
    if not SIMULATION_SCRIPTS.is_dir():
        return []
    selected = []
    for path in walk_files(SIMULATION_SCRIPTS, {"__pycache__", "results"}):
        if path.suffix.lower() in SIMULATION_SUFFIXES:
            selected.append(path)
    return sorted(selected)


def config_files() -> list[Path]:
    return walk_files(BENCHMARK / "config", set())


def is_final_result(path: Path, root: Path) -> bool:
    relative = path.relative_to(root)
    if any(part in EXCLUDED_RESULT_PARTS for part in relative.parts):
        # QUAST's final report files can sit above these directories, but no internal file is needed.
        return False
    if path.stat().st_size > MAX_RESULT_BYTES:
        return False
    name = path.name.lower()
    if name in RESULT_EXACT:
        return True
    if path.suffix.lower() not in RESULT_SUFFIXES:
        return False
    if name.endswith((".base.eval.tsv", ".read.eval.tsv", ".metric.eval.tsv", ".rdlvl.eval.tsv", ".errorrate.tsv")):
        return True
    if any(marker in name for marker in RESULT_MARKERS):
        return True
    # Top-level result tables are curated collector outputs.
    return root == BENCHMARK / "results" and len(relative.parts) == 1


def add_result(selected: dict[str, Path], source: Path) -> None:
    """Add a policy-compliant result or selected-run artifact."""
    for root, label in ((BENCHMARK / "results", "results"), (BENCHMARK / "runs", "runs")):
        try:
            relative = source.relative_to(root)
        except ValueError:
            continue
        if source.is_file() and is_final_result(source, root):
            selected[f"{label}/{relative.as_posix()}"] = source
        return


def referenced_artifacts(table: Path) -> list[Path]:
    """Extract selected benchmark result/run paths recorded in a TSV manifest."""
    found: list[Path] = []
    try:
        rows = csv.reader(table.open(), delimiter="\t")
        for row in rows:
            for value in row:
                value = value.strip()
                if value.startswith("benchmark/results/") or value.startswith("benchmark/runs/"):
                    found.append(PROJECT / value)
    except (OSError, UnicodeDecodeError, csv.Error):
        pass
    return found


def add_selected_run(selected: dict[str, Path], run_dir: Path) -> None:
    """Keep provenance, resources, and the preferred final report for one run."""
    if not run_dir.is_dir():
        return
    files = walk_files(run_dir, EXCLUDED_RESULT_PARTS | {"tmp", ".snakemake", "logs"})
    for path in files:
        relative = path.relative_to(run_dir).as_posix()
        if path.name == "provenance.json" or path.name == "resources.time.txt":
            add_result(selected, path)
        elif path.name == "report.tsv" and "/combined_reference/" in f"/{relative}":
            if "ambiguity9999" in relative:
                add_result(selected, path)
    if not any(
        source.is_relative_to(run_dir) and source.name == "report.tsv"
        for source in selected.values()
    ):
        for path in files:
            if path.name == "report.tsv" and path.parent.name in {"quast", "metaquast"}:
                add_result(selected, path)


def result_files() -> list[tuple[Path, str]]:
    """Collect current aggregates and only the runs that support them."""
    selected: dict[str, Path] = {}
    results_root = BENCHMARK / "results"
    result_pruned = (
        EXCLUDED_RESULT_PARTS | EXCLUDED_RESULT_ROOTS |
        {"tmp", ".snakemake", "logs"}
    )
    for path in walk_files(results_root, result_pruned):
        if is_final_result(path, results_root):
            key = f"results/{path.relative_to(results_root).as_posix()}"
            selected[key] = path

    # Aggregate tables and manifests record the exact selected benchmark/run
    # paths.  Preserve compact evidence only for those referenced runs.
    referenced_runs: set[Path] = set()
    for source in list(selected.values()):
        if source.suffix.lower() != ".tsv":
            continue
        for artifact in referenced_artifacts(source):
            try:
                relative = artifact.relative_to(BENCHMARK / "runs")
            except ValueError:
                continue
            if len(relative.parts) >= 2 and relative.parts[0] not in EXCLUDED_PAPER_RUN_GROUPS:
                referenced_runs.add(BENCHMARK / "runs" / relative.parts[0] / relative.parts[1])
    for run_dir in sorted(referenced_runs):
        add_selected_run(selected, run_dir)

    # The Zymo depth summary contains imported provenance labels rather than
    # paths, so retain its compact run evidence by paper-scoped run group.
    for group in sorted(ADDITIONAL_PAPER_RUN_GROUPS):
        root = BENCHMARK / "runs" / group
        if root.is_dir():
            for run_dir in sorted(path for path in root.iterdir() if path.is_dir()):
                add_selected_run(selected, run_dir)
    return [(selected[key], key) for key in sorted(selected)]


def code_role(path: Path) -> str:
    value = path.as_posix().lower()
    if "plot" in value:
        return "plotting"
    if any(token in value for token in ("collect", "table", "atiqu", "evalue")):
        return "table_or_statistics"
    if any(token in value for token in ("config", "sim", "data.sh", "download")):
        return "data_or_simulation"
    if any(token in value for token in ("quast", "hifi", "assembly", "assambly", "class")):
        return "evaluation"
    return "benchmark_or_method"


def legacy_code_files() -> tuple[list[Path], list[Path]]:
    included: list[Path] = []
    excluded: list[Path] = []
    if not LEGACY_RESULTS.is_dir():
        return included, excluded
    completed = subprocess.run(
        ["find", str(LEGACY_RESULTS), "-type", "f", "-size", f"-{MAX_METADATA_BYTES}c", "-print0"],
        check=True, capture_output=True,
    )
    for value in completed.stdout.split(b"\0"):
        if not value:
            continue
        path = Path(os.fsdecode(value))
        if path.suffix.lower() not in LEGACY_CODE_SUFFIXES:
            continue
        relative = path.relative_to(LEGACY_RESULTS)
        if relative.parts and relative.parts[0] in PAPER_LEGACY_ROOTS:
            included.append(path)
        else:
            excluded.append(path)
    return sorted(included), sorted(excluded)


def write_source_code_map(
    sources: list[Path], simulation: list[Path], configs: list[Path],
    legacy_included: list[Path], legacy_excluded: list[Path]
) -> None:
    output = BUNDLE / "docs" / "SOURCE_CODE_MAP.tsv"
    with output.open("w", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(["bundle_path", "source_path", "sha256", "role", "status", "reason"])
        for source in sources:
            relative = source.relative_to(BENCHMARK)
            writer.writerow([
                f"workflow/benchmark/{relative.as_posix()}", str(source), sha256(source),
                code_role(relative), "included", "current reproducible benchmark source",
            ])
        for source in simulation:
            relative = source.relative_to(SIMULATION_SCRIPTS)
            writer.writerow([
                f"workflow/simulation/{relative.as_posix()}", str(source), sha256(source),
                "data_or_simulation", "included", "simulation or data-preparation source",
            ])
        for source in configs:
            relative = source.relative_to(BENCHMARK / "config")
            writer.writerow([
                f"config/{relative.as_posix()}", str(source), sha256(source),
                "configuration", "included", "exact current configuration snapshot",
            ])
        for source in legacy_included:
            relative = source.relative_to(LEGACY_RESULTS)
            writer.writerow([
                f"workflow/legacy_final_result/{relative.as_posix()}", str(source), sha256(source),
                code_role(relative), "included", "compact historical script for a manuscript dataset",
            ])
        for source in legacy_excluded:
            relative = source.relative_to(LEGACY_RESULTS)
            writer.writerow([
                "", str(source), sha256(source), code_role(relative), "excluded",
                "outside the manuscript dataset scope; retained at source and inventoried only",
            ])


def write_result_inventory(results: list[tuple[Path, str]]) -> None:
    output = BUNDLE / "docs" / "RESULT_INVENTORY.tsv"
    with output.open("w", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(["bundle_path", "source_path", "bytes", "sha256", "status", "reason"])
        for source, relative in results:
            writer.writerow([
                relative, str(source), source.stat().st_size, sha256(source),
                "included", "compact final report, aggregate, metric, status, or provenance",
            ])


def expand_paper_map() -> None:
    path = BUNDLE / "docs" / "PAPER_EVALUATION_MAP.tsv"
    rows = list(csv.DictReader(path.open(), delimiter="\t"))
    fields = list(rows[0]) if rows else []
    for field in ("input_source", "collector_or_plot"):
        if field not in fields:
            fields.append(field)
    for row in rows:
        row["input_source"] = (
            f"paths declared by {row['config']}; acquisition/generation route in docs/DATASETS.tsv"
        )
        row["collector_or_plot"] = TRACE_COLLECTORS.get(
            row["analysis"], "workflow/benchmark/scripts/collect_run_summaries.py"
        )
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def metadata_files() -> list[tuple[str, Path, Path]]:
    selected: list[tuple[str, Path, Path]] = []
    for dataset, root in METADATA_SOURCES.items():
        if not root.is_dir():
            continue
        for path in walk_files(root, METADATA_PRUNED):
            if path.suffix.lower() not in METADATA_SUFFIXES:
                continue
            if path.stat().st_size > MAX_METADATA_BYTES:
                continue
            selected.append((dataset, root, path))
    return sorted(selected, key=lambda item: (item[0], item[2].relative_to(item[1]).as_posix()))


def write_metadata_sources(metadata: list[tuple[str, Path, Path]]) -> None:
    counts: dict[str, int] = {}
    for dataset, _, _ in metadata:
        counts[dataset] = counts.get(dataset, 0) + 1
    output = BUNDLE / "metadata" / "metagenome" / "SOURCE_MANIFEST.tsv"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(["dataset", "community", "source_root", "files"])
        labels = {
            "30S-BA": "30-strain broad-abundance mixture",
            "30S-NU": "30-strain near-uniform legacy mixture",
            "100S-BA": "100-strain broad-abundance mixture",
            "100S-NU": "100-strain near-uniform legacy mixture",
        }
        for dataset in sorted(METADATA_SOURCES):
            writer.writerow([dataset, labels[dataset], METADATA_SOURCES[dataset], counts.get(dataset, 0)])


def write_external_data(configs: list[Path]) -> None:
    occurrences: dict[str, set[str]] = {}
    for config in configs:
        try:
            text = config.read_text(errors="replace")
        except OSError:
            continue
        for match in ABSOLUTE_PATH_RE.findall(text):
            normalized = match.rstrip(".:;)")
            occurrences.setdefault(normalized, set()).add(config.relative_to(BENCHMARK / "config").as_posix())
    output = BUNDLE / "EXTERNAL_DATA.tsv"
    with output.open("w", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(["absolute_path", "exists", "kind", "referenced_by"])
        for value in sorted(occurrences):
            path = Path(value)
            kind = "directory" if path.is_dir() else "file" if path.is_file() else "missing"
            writer.writerow([value, str(path.exists()).lower(), kind, ";".join(sorted(occurrences[value]))])


def write_manifest() -> None:
    excluded = {"MANIFEST.tsv", "validation_report.txt"}
    files = sorted(
        path for path in BUNDLE.rglob("*")
        if path.is_file() and ".git" not in path.parts and path.relative_to(BUNDLE).as_posix() not in excluded
    )
    with (BUNDLE / "MANIFEST.tsv").open("w", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(["path", "bytes", "sha256"])
        for path in files:
            writer.writerow([path.relative_to(BUNDLE).as_posix(), path.stat().st_size, sha256(path)])


def build(refresh: bool) -> None:
    if refresh:
        clean_generated()
    sources = source_files()
    simulation = simulation_files()
    configs = config_files()
    results = result_files()
    metadata = metadata_files()
    legacy_included, legacy_excluded = legacy_code_files()

    for source in sources:
        relative = source.relative_to(BENCHMARK)
        copy_file(source, BUNDLE / "workflow" / "benchmark" / relative)
    for source in simulation:
        relative = source.relative_to(SIMULATION_SCRIPTS)
        copy_file(source, BUNDLE / "workflow" / "simulation" / relative)
    for source in configs:
        relative = source.relative_to(BENCHMARK / "config")
        copy_file(source, BUNDLE / "config" / relative)
        # Preserve the original runnable relative layout as well.
        copy_file(source, BUNDLE / "workflow" / "benchmark" / "config" / relative)
    for source, relative in results:
        copy_file(source, BUNDLE / relative)
    for source in legacy_included:
        copy_file(source, BUNDLE / "workflow" / "legacy_final_result" / source.relative_to(LEGACY_RESULTS))
    for dataset, root, source in metadata:
        copy_file(source, BUNDLE / "metadata" / "metagenome" / dataset / source.relative_to(root))
    write_metadata_sources(metadata)
    write_source_code_map(sources, simulation, configs, legacy_included, legacy_excluded)
    write_result_inventory(results)
    expand_paper_map()

    write_external_data(configs)
    write_manifest()
    total = sum(path.stat().st_size for path in BUNDLE.rglob("*") if path.is_file() and ".git" not in path.parts)
    print(
        f"Bundle built: {len(sources)} benchmark source files, {len(simulation)} simulation files, "
        f"{len(configs)} configs, "
        f"{len(results)} result files, {len(metadata)} metadata files, "
        f"{len(legacy_included)} historical scripts, {total / 1048576:.2f} MiB"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="replace generated workflow/config/results trees")
    args = parser.parse_args()
    if not BENCHMARK.is_dir():
        parser.error(f"benchmark source not found: {BENCHMARK}")
    build(args.refresh)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
