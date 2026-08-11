# DADEC paper evaluation

This repository is the compact, auditable evaluation package for the DADEC manuscript. It links every paper-facing analysis to the workflow source, run configuration, collector, and final numerical evidence used in the manuscript.

> [!IMPORTANT]
> **Method parameters are directly accessible here—do not search through scripts to find them.** Start with [`config/common.yaml`](config/common.yaml) for shared executable paths, threads, and study-wide method settings; then open the exact [`dataset configs`](config/datasets/), [`run configs`](config/runs/), [`classification configs`](config/classification/), and [`overlay configs`](config/overlays/) used by each analysis. Assembly settings are in [`config/runs/drosophila/assembly/config.yaml`](config/runs/drosophila/assembly/config.yaml), and hifieval settings are in the dataset-specific `config/runs/*/hifieval/` directories. The exact config for every paper result is linked from [`docs/PAPER_EVALUATION_MAP.tsv`](docs/PAPER_EVALUATION_MAP.tsv). Preserve these parameter values when reproducing the manuscript.

## Contents

- `workflow/benchmark/`: snapshot of the Snakemake workflows, method runners, evaluation parsers, final collectors, tests, and operational documentation.
- `workflow/simulation/`: simulation and data-preparation code/configuration collected from the project `scripts/` tree; generated logs, cached bytecode, and result files are excluded.
- `config/`: all dataset, run, classification, overlay, and common YAML/TSV configurations. An identical copy is retained under `workflow/benchmark/config/` so the original launchers keep their expected layout.
- `results/`: compact final evidence from `benchmark/results`.
- `runs/`: run-level final reports and provenance that were not promoted to the aggregate result tree.
- `metadata/metagenome/`: genome/accession lists, strain names, abundance distributions, ANI summaries, CAMISIM/ART/PBSIM configurations, taxonomic profiles, mappings, manifests, and simulation logs for 30S-NU, 30S-BA, 100S-NU, and 100S-BA.
- `docs/PAPER_EVALUATION_MAP.tsv`: one row per paper analysis, with the exact code, representative configuration, final result, and reproduction command.
- `docs/SOURCE_CODE_MAP.tsv`: auditable inventory of current and historical analysis, benchmark, plotting, table, statistics, simulation, and evaluation code.
- `docs/RESULT_INVENTORY.tsv`: source path, size, and checksum for every bundled final result.
- `docs/DATASETS.tsv`: dataset source, accession/download or simulation route, configuration, and bundled-material boundary.
- `docs/ISSUES.md`: known provenance gaps or inconsistencies; discrepancies are recorded rather than silently corrected.
- `EXTERNAL_DATA.tsv`: absolute paths referenced by configurations, their current availability, and the configurations that use them.
- `MANIFEST.tsv`: byte size and SHA-256 digest of every bundled file.
- `build_bundle.py` and `validate_bundle.py`: deterministic export and integrity validation.

## Scope of “final results”

The bundle contains numerical summaries, selected-run tables, QUAST/MetaQUAST final reports, hifieval evaluation tables, classification metrics, assembly summaries, resource summaries, status files, and provenance. It intentionally excludes raw reads, references, corrected FASTA, assemblies, PAF/BED/SAM/BAM files, per-read assignments, QUAST alignment caches, HTML viewers, logs, and temporary work directories. See `docs/RESULT_POLICY.md`.

## Quick start

Validate the supplied snapshot:

```bash
python validate_bundle.py
```

Inspect the paper-to-evidence index:

```bash
column -s $'\t' -t docs/PAPER_EVALUATION_MAP.tsv | less -S
```

Run a single correction job after installing the required tools and replacing machine-specific paths in `workflow/benchmark/config/common.yaml` and the selected dataset YAML:

```bash
cd workflow
CORES=64 benchmark/run_one.sh benchmark/config/runs/ecoli3/20x_dadec.yaml
```

Run only the evaluation stage for an existing corrected FASTA by setting `evaluation_only: true` and `corrected_input` in a copied run YAML. Detailed commands for hifieval, coverage, classification, assembly, ablation, and result collection are indexed in `docs/PAPER_EVALUATION_MAP.tsv` and documented in `workflow/benchmark/README.md`.

## Regenerating paper figures, tables, and statistics

Use `docs/PAPER_EVALUATION_MAP.tsv` as the authoritative traceability index. For each paper item, it identifies the input source, exact method config, analysis runner, collector or plotting script, final numerical output, and reproduction command. Current production code lives under `workflow/benchmark/`; compact historical scripts from `/home/yczhang/zyc/final_result` are preserved separately under `workflow/legacy_final_result/` and must not be mistaken for rewritten parameter definitions.

After running an analysis, execute the mapped collector or plot command and compare its compact TSV/CSV/TEX result with `results/`. If a value differs, retain both files and add the comparison to `docs/ISSUES.md`; do not edit either result to force agreement.

## Rebuilding from the working project

`build_bundle.py` expects this repository at `<project>/dadec_eval`, the source benchmark at `<project>/benchmark`, and the historical near-uniform metadata roots listed in `metadata/metagenome/SOURCE_MANIFEST.tsv`:

```bash
python build_bundle.py --refresh
python validate_bundle.py
```

The rebuild preserves `.git`, `LICENSE`, `README.md`, `docs/`, and the two builder/validator scripts. It replaces only generated `workflow/`, `config/`, `results/`, `runs/`, `metadata/`, `MANIFEST.tsv`, and `EXTERNAL_DATA.tsv`.

## Reproducibility boundary

The configurations preserve the exact historical paths and parameters for provenance. They are not silently rewritten because doing so could change scientific inputs. On a new system, acquire the datasets listed in `docs/ENVIRONMENT.md`, replace paths in copied YAML files, confirm checksums where available, and then run the same configuration. Missing external paths are reported as inventory information, not as corruption of this compact result bundle.
