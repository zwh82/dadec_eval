# DADEC Manual Benchmark Workflow

The main Snakemake workflow is now designed for manual node scheduling. Log in
to a node, run one `coverage + method + parameter_set` job there, and keep each
job in its own run directory.

## Layout

```text
benchmark/config/common.yaml
benchmark/config/datasets/<dataset>.yaml
benchmark/config/runs/<dataset>/<coverage>_<method>.yaml
benchmark/runs/<data_group>/<run_id>/.snakemake/
benchmark/runs/<data_group>/<run_id>/tmp/
benchmark/runs/<data_group>/<run_id>/output/
benchmark/runs/<data_group>/<run_id>/logs/
benchmark/runs/<data_group>/<run_id>/benchmark/
benchmark/results/all_parameter_runs.tsv
benchmark/results/best_parameter_runs.tsv
```

Dataset YAML files only describe dataset metadata, inputs, and whether to use
`metaquast` or `quast`. Per-run parameters live in job configs under
`benchmark/config/runs/<dataset>/`.

## Raw long-read input baselines

Evaluate each configured raw long-read input independently of correction runs:

```bash
QUAST_THREADS=64 bash benchmark/work_scripts/evaluate_raw_long_reads.sh
```

The launcher uses the `dadec_eval` environment. Dataset configs marked
`metaquast` are evaluated with `--ambiguity-usage all --ambiguity-score 0.9999`;
those marked `quast` use QUAST. FASTQ inputs are converted to a local FASTA
copy, leaving the source read files unchanged. The primary input is labelled
`full`; every `inputs.long_read_subsamples` entry is evaluated as a separate
baseline using its own label. Zymo runs only its requested `5pct`–`40pct`
subsamples, not its full source set. Reports, logs, and prepared inputs are written to
`benchmark/results/raw_long_reads/<config>/<long-read-label>/`; the cross-dataset
index is `benchmark/results/raw_long_reads/summary.tsv`.
The config filename is retained as the result key so configurations that share
a dataset id remain distinguishable. Re-running skips reports newer than their
raw long-read and genome-map inputs; add `--force` to rerun them.

`30strains`, `30strains_legacy`, `100strains`, and `ecoli3` use `metaquast`.
`arabidopsis` is a placeholder for a single-reference workflow and uses `quast`.

## Run One Job

Dry-run one original 50x DADEC job:

```bash
benchmark/run_one.sh benchmark/config/runs/30strains/50x_dadec.yaml -n --quiet
```

Run it for real:

```bash
CORES=64 benchmark/run_one.sh benchmark/config/runs/30strains/50x_dadec.yaml
```

Run another dataset by setting `DATASET_CONFIG`:

```bash
DATASET_CONFIG=/home/work/wenhai/dadec/benchmark/config/datasets/100strains.yaml \
  CORES=64 benchmark/run_one.sh benchmark/config/runs/100strains/30x_dadec.yaml
```

Examples for manual multi-node scheduling:

```bash
# node001
CORES=64 benchmark/run_one.sh benchmark/config/runs/30strains/50x_dadec.yaml

# node002
CORES=64 benchmark/run_one.sh benchmark/config/runs/30strains/50x_fmlrc.yaml

# node003
CORES=64 benchmark/run_one.sh benchmark/config/runs/30strains/50x_ratatosk.yaml
```

The final run directory appends a method-specific parameter signature to
`run.id`. For example, changing DADEC k/split/threshold/abundance changes the
directory name even if the visible `run.id` prefix is unchanged. The signature
uses compact codes such as `k31_k31_s1_a2_a1`, `k31_ls5`, and
`k31_ls5_hs10_hi1`.

## Experiment-default FMLRC, Ratatosk, and LoRDEC queue

The restart-safe default-parameter audit and per-tool runners live in
`benchmark/work_scripts/default_parameters/`. They compare parameters from
provenance rather than trusting `original`/`tool_default` labels, skip validated
completed work, and resume missing evaluation reports without rerunning
correction. See `benchmark/work_scripts/default_parameters/README.md` for the
audit, dry-run, sharding, comparator-backfill, and final comparison commands.

The experiment defines FMLRC `21/59`, Ratatosk `31/63`, and LoRDEC `19/5`.
LoRDEC's `19/5` values are experiment defaults; LoRDEC 0.9 itself requires both
options and does not supply program defaults.

## 30strains Legacy Centrifuge Classification

The 30strains legacy classification workflow lives in
`benchmark/scripts/classification/`, with manual launchers in
`benchmark/work_scripts/classification/`. It reuses the historical Centrifuge
index, starts with `coverage=10x`, validates current FMLRC classification against
the historical report, falls back to the historical `30_cor/<coverage>/fmlrc1.fa`
when needed, and writes outputs under `benchmark/results/classification/`.

Dry-run the first 10x pass:

```bash
benchmark/work_scripts/classification/30strains_legacy_10x.sh -n
```

Each tool's `metrics.json` and `metrics.txt` contains both evaluation
conventions. `precision`, `recall`, and `F1` (also named `macro_*`) preserve
the historical 30-group macro average. `micro_precision`, `micro_recall`, and
`micro_F1` first sum the per-group confusion counts and then calculate the
global value. `accuracy`/`micro_accuracy` is the correctly classified read
count divided by all assignment rows.

## Hifieval Evaluation

The standalone Hifieval workflow evaluates corrected FASTAs without rerunning
correction. ecoli3 has configs for DADEC, FMLRC, F_HERO, Ratatosk, R_HERO,
LoRDEC, L_HERO, CoLoRMap, and Proovread under:

```text
benchmark/config/runs/ecoli3/hifieval/20x_<method>_hifieval.yaml
```

The DADEC entry deliberately evaluates
`ecoli3_20x_dadec_dev_fix_a_k31_k31_s1_a2_a1`; it does not use the older
standard or ablation DADEC outputs.

Preflight all nine methods without starting alignment or evaluation:

```bash
benchmark/work_scripts/hifieval/ecoli3_all.sh --preflight
```

Run all methods sequentially and collect the final comparison:

```bash
benchmark/work_scripts/hifieval/ecoli3_all.sh
```

Run or resume a subset with comma- or space-separated method names:

```bash
METHODS=dadec,fmlrc benchmark/work_scripts/hifieval/ecoli3_all.sh
```

Simulated Arabidopsis has the same nine-method interface:

```bash
benchmark/work_scripts/hifieval/arabidopsis_sim_all.sh --preflight
benchmark/work_scripts/hifieval/arabidopsis_sim_all.sh
METHODS=dadec,fmlrc benchmark/work_scripts/hifieval/arabidopsis_sim_all.sh
```

Its configs are `benchmark/config/runs/arabidopsis_sim/hifieval/32x_<method>_hifieval.yaml`
and its summary is
`benchmark/results/hifieval/arabidopsis_sim_32x/summary.tsv`. DADEC uses the
completed dev-fix-a output, while Proovread uses its completed non-empty
benchmark output.

The compatibility launchers `ecoli3_fmlrc.sh` and
`arabidopsis_sim_fmlrc.sh` remain available. Set `THREADS=N` or pass
`--threads N` to override minimap2 threads. Completed stages are reused when
their commands and input metadata are unchanged; `--force` reruns every stage.

Per-method results are written below
`benchmark/results/hifieval/ecoli3_20x/<method>/`. The unfiltered and filtered
directories use `<method>.*` prefixes. The filtered base metrics exclude
read-level over-corrections. Logs, corrected PAF, stage state, checksums, and
`provenance.json` are retained. After all nine methods complete,
`benchmark/results/hifieval/ecoli3_20x/summary.tsv` contains two rows per
method and the columns:

```text
method filter_state raw_errors corrected_errors read_oc read_uc read_cc
base_oc base_uc base_cc FDR FNR TPR read_mapping_mode corrected_fasta
```

The ecoli3 reproduction configs use `legacy_endpoint` to reproduce the
published read-level classification, including its endpoint/order-dependent
treatment of supplementary PAF alignments. `truth_interval` remains available
for reference-aware, any-compatible alignment classification, but the two
definitions must not be combined in one comparison. Arabidopsis FASTA
identifiers are normalized by streaming to `work/corrected.cleaned.fa`; source
MAF and raw PAF files are never copied.

## Drosophila Canu and hifiasm assembly

The Drosophila assembly matrix is configured in
`benchmark/config/runs/drosophila/assembly/config.yaml` and writes only below
`benchmark/runs/drosophila_43x/assembly/`. It contains nine methods and two
assemblers. DADEC, Colormap, and Proovread are newly assembled by both Canu and
hifiasm; FMLRC, Ratatosk, LoRDEC, F-HERO, R-HERO, and L-HERO import their
existing non-empty assembly FASTAs. All 18 assemblies are reevaluated with
QUAST against the same GCF reference.

The launcher gives Snakemake 64 cores and strictly runs Canu and hifiasm with
64 threads. Canu follows the reference command as `-p canu ... -pacbio INPUT`
without adding `-corrected`, using fresh `work_pacbio/` state. Hifiasm uses
fresh `work_corrected/` state. QUAST uses the independent `quast_threads`
setting (currently 64). Inspect
the full DAG before starting the long-running jobs:

```bash
cd benchmark/work_scripts/assembly
./run.sh -n --printshellcmds
```

Run or resume the workflow:

```bash
cd benchmark/work_scripts/assembly
./run.sh --printshellcmds
```

For a persistent background run from the same directory, use `./start.sh` and
follow `workflow.log`.

Canu stores remain under each Canu result's `work_pacbio/`; hifiasm GFA files
remain under each hifiasm result's `work_corrected/`
directory. Each cell also contains `assembly.fa`, `provenance.json`, logs,
resource measurements, and `quast/`. Imported assemblies are copied with
reflink support when available; the legacy source tree is never modified.
Failed jobs publish neither the final assembly nor the final QUAST directory,
and a normal rerun resumes only missing outputs.

After completion, `summary.tsv` and `manifest.json` must each describe the
complete 18-cell matrix. Verify FASTA/report presence and source/output
checksums with:

```bash
cd benchmark/work_scripts/assembly
./verify.sh
```

## Add A Parameter Set

Create a new job config instead of editing an old one. For example, to compare
DADEC 50x with `k=21`, copy `50x_dadec.yaml` to a new file and change:

```yaml
run: {id: 30strains_50x_dadec_k21, coverage: 50x, method: dadec, parameter_set: k21}
dadec_k1: 21
dadec_k2: 21
```

If a parameter key is present but blank, the workflow stops and asks you to fill
it or remove the key.

Runs are grouped by the data prefix before the method name. For example, all
`30strains_10x_*` runs live under `benchmark/runs/30strains_10x/`, while their
original run IDs remain unchanged.

The actual result directory will include the parameter signature, for example:

```text
benchmark/runs/30strains_50x/30strains_50x_dadec_k21_k21_k21_s1_a2_a1/
```

## Choose QUAST Or MetaQUAST

Set this in the dataset config or run config:

```yaml
evaluation:
  tool: metaquast
```

or:

```yaml
evaluation:
  tool: quast
```

`metaquast` outputs:

```text
output/short_<coverage>/<method>/metaquast/combined_reference/report.tsv
output/short_<coverage>/<method>/metaquast.ambiguity9999/combined_reference/report.tsv
```

The first path is `ambiguity_score=0.99`; the second is `0.9999`. Both are
selected by default. Select one or both without changing a run ID:

```bash
AMBIGUITY_SCORES=0.99 benchmark/run_one.sh benchmark/config/runs/30strains/10x_colormap.yaml
AMBIGUITY_SCORES=0.99,0.9999 benchmark/run_one.sh benchmark/config/runs/30strains/10x_colormap.yaml
```

Existing reports at either path are reused. Changing this selection only adds
missing MetaQUAST jobs; it does not rerun read correction.

`quast` uses the configured command equivalent to:

```bash
/home/yczhang/zyc/tools/quast/quast.py -r REF -t THREADS FASTA -o OUTDIR
```

and outputs:

```text
output/short_<coverage>/<method>/quast/report.tsv
```

### Evaluate an existing corrected FASTA

To skip read correction and run only QUAST/MetaQUAST plus provenance, add
`corrected_fasta` to the run config:

```yaml
evaluation:
  tool: metaquast
  corrected_fasta: /home/yczhang/zyc/final_result/100strains/100_cor/fmlrc1.fa
```

This is already configured for
`config/runs/100strains_legacy/30x_fmlrc.yaml`. The normal command is unchanged:

```bash
DATASET_CONFIG=benchmark/config/datasets/100strains_legacy.yaml \
  benchmark/run_one.sh benchmark/config/runs/100strains_legacy/30x_fmlrc.yaml
```

When `corrected_fasta` is absent or blank, the original correction-and-evaluation
pipeline is used unchanged. When it is set, the default targets exclude the
internally generated `corrected.fa` and correction resource file; the external
FASTA is passed directly to QUAST/MetaQUAST and recorded in `provenance.json`.
The option requires a run config selecting exactly one coverage and one method.
Relative paths are resolved from `project_root`.

### Reevaluate a run's own corrected FASTA

To change only the reference and evaluate the existing internal
`output/short_<coverage>/<method>/corrected.fa`, keep the original command and
add the opt-in override:

```bash
benchmark/run_one.sh benchmark/config/runs/<dataset>/<coverage>_<method>.yaml \
  --config evaluation_only=true -n
```

Remove `-n` only after inspecting the DAG. In this mode the workflow does not
load correction rules or resource targets, so a missing internal
`corrected.fa` is a hard error instead of a request to recreate it. The run
config must select exactly one coverage and one method. `evaluation_only=true`
cannot be combined with `evaluation.corrected_fasta` or `evaluation.report`.

Reference-map changes are tracked directly by `prepare_reference`; the shared
correction preflight no longer depends on the reference map. Consequently,
changing a reference rebuilds the prepared reference and QUAST/MetaQUAST
report without invalidating read preparation or correction. Existing commands
and FASTA, FASTQ/GZ, multi-coverage, long-read-subsample, self-correction,
external-FASTA, and report-import inputs remain unchanged when
`evaluation_only` is false (the default).

## Add 5x Later

It is fine to leave a future depth empty in the dataset config:

```yaml
inputs:
  short_reads:
    5x:
    10x: data/30strains/sim_30strains_short_10x.fq.gz
```

An empty depth is ignored. It will not trigger 10x-50x reruns. Add a real input
path and a new `benchmark/config/runs/30strains/5x_<method>.yaml` only when you
are ready to run 5x.

## Collect Results

Run final aggregation only after individual jobs are finished:

```bash
/home/wenhai/miniconda3/bin/conda run -n dadec_eval \
  python benchmark/scripts/collect_run_summaries.py \
  --runs-root benchmark/runs \
  --output-all benchmark/results/all_parameter_runs.tsv \
  --output-best benchmark/results/best_parameter_runs.tsv
```

Collect only one dataset/depth, for example the finished `ecoli3` 20x runs:

```bash
/home/wenhai/miniconda3/bin/conda run -n dadec_eval \
  python benchmark/scripts/collect_run_summaries.py \
  --runs-root benchmark/runs \
  --dataset ecoli3 \
  --short-coverage 20x \
  --output-all benchmark/results/ecoli3_20x_all_parameter_runs.tsv \
  --output-best benchmark/results/ecoli3_20x_best_parameter_runs.tsv
```

You can also filter by run directory name:

```bash
/home/wenhai/miniconda3/bin/conda run -n dadec_eval \
  python benchmark/scripts/collect_run_summaries.py \
  --runs-root benchmark/runs \
  --run-glob 'ecoli3_20x*' \
  --output-all benchmark/results/ecoli3_20x_all_parameter_runs.tsv \
  --output-best benchmark/results/ecoli3_20x_best_parameter_runs.tsv
```

Individual jobs never write global summary files.

## Run-layout migration and QUAST cleanup

Inspect the one-time flat-to-grouped migration before applying it:

```bash
python benchmark/scripts/migrate_run_layout.py --root /home/work/wenhai/dadec --dry-run
python benchmark/scripts/migrate_run_layout.py --root /home/work/wenhai/dadec --apply
```

The migration moves each complete run directory on the same filesystem and
writes `benchmark/run_layout_migration.json`. It refuses destination collisions.

QUAST and MetaQUAST output is compacted after the primary report is validated.
By default, only regular files at least 100 MiB inside the evaluation directory
are deleted; the primary `report.tsv` is always preserved. The threshold is
configured by `quast_cleanup.threshold_mib`. Existing results can be inspected
and compacted with:

```bash
python benchmark/scripts/compact_quast.py --runs-root benchmark/runs --threshold-mib 100 --dry-run
python benchmark/scripts/compact_quast.py --runs-root benchmark/runs --threshold-mib 100 --apply \
  --skip-missing-report --manifest benchmark/quast_cleanup_manifest.json
```

The cleanup manifest records every deleted path and size. Deleted QUAST
intermediates are not recoverable from the benchmark directory; rerunning QUAST
is required if one is later needed.

Run-level `tmp` directories contain prepared FASTA inputs and method working
files. These are reproducible staging data: Snakemake declares the prepared
inputs and reference as temporary outputs, while corrected reads, resource
logs, evaluation reports, preflight data, and provenance remain permanent.
Preview and remove `tmp` only for runs with a non-empty primary evaluation
report using:

```bash
python benchmark/scripts/cleanup_run_tmp.py --runs-root benchmark/runs --dry-run \
  --manifest /tmp/run_tmp_preview.json
python benchmark/scripts/cleanup_run_tmp.py --runs-root benchmark/runs --apply \
  --manifest benchmark/run_tmp_cleanup_manifest.json
```

The default preserves incomplete runs so their method work can be resumed.
After reviewing the manifest, pass `--include-incomplete` only when restarting
those runs from their recorded inputs is acceptable. Re-running the original
`benchmark/run_one.sh` command reconstructs missing staging files; completed
evaluation reports remain Snakemake targets and are not recomputed.

## Resume missing ambiguity-score reports

List completed non-ablation runs that are still missing either MetaQUAST score:

```bash
python benchmark/work_scripts/run_missing_ambiguity_scores.py
```

Validate every missing job with Snakemake, then execute them sequentially:

```bash
bash benchmark/work_scripts/run_missing_ambiguity_scores.sh --dry-run
nohup bash benchmark/work_scripts/run_missing_ambiguity_scores.sh \
  > benchmark/work_scripts/logs/missing_ambiguity_scores.log 2>&1 &
```

The scanner ignores QUAST-only datasets, ablation directories, and runs without
an existing `corrected.fa`. It reconstructs historical parameter configs from
each run's provenance, requests only missing scores, and is safe to restart.
Use `--dataset 30strains_legacy` or `--run-glob 'ecoli_error_miseq*'` to run a
subset.

## Metrics And Tests

Reported fields are runtime/resources plus these QUAST/MetaQUAST metrics:
`# mismatches per 100 kbp`, `# indels per 100 kbp`, `Genome fraction (%)`,
`# local misassemblies`, and exact `# contigs`.

```bash
python -m unittest discover -s benchmark/tests -v
```

## DADEC Stage Ablation Study

DADEC's correction algorithm is built from three modules (stages), selectable
via the binary's `--stages` option:

- **Stage 1** — High-Confidence Error Elimination (DBG, `-k`/`-a`)
- **Stage 2** — Haplotype-Specific Refinement (MSA, `-r`)
- **Stage 3** — Low-Abundance Information Recovery (DBG, `-K`/`-A`)

Valid subsets are `1`, `2`, `3`, `1,2`, `1,3`, `2,3`, `1,2,3` (stages always run
in their original order).

The main Snakemake pipeline never passes `--stages` (it always runs the default
`1,2,3`) and there is no config field to inject it. The ablation therefore uses a
standalone driver, `benchmark/work_scripts/dadec_ablation.sh`, which calls the
DADEC binary and QUAST directly, reusing the prepared inputs and reference left
behind by a completed full run. It does not modify any pipeline code, config, or
the DADEC source.

Each stage combination runs under `conda run -n DADEC`; QUAST runs under
`conda run -n dadec_eval`. All DADEC parameters, coverage, the stage list, conda
env names, and input paths are overridable environment variables (defaults match
`benchmark/config/runs/arabidopsis/32x_dadec.yaml`: `k=39 K=39 S=4 r=0.1 a=3 A=2`).
For combinations that start directly at stage 2 (`2` and `2,3`), the long-read
input is normalized to a per-run, single-line FASTA before it is passed to the
MSA module, matching the format normally emitted by stage 1. FASTQ input (plain
or gzip-compressed) uses `seqkit fq2fa -w 0`; existing FASTA uses
`seqkit seq -w 0` so wrapped sequences are not truncated by the stage-2 reader.
Outputs go to
`benchmark/runs/<dataset>_<coverage>/<dataset>_<coverage>_dadec_ablation_<param-signature>/stage_<tag>/`
and the summary table to
`benchmark/results/<dataset>_<coverage>_dadec_ablation_<param-signature>.tsv`,
so multiple parameter sweeps never overwrite each other. The already-completed
full `1,2,3` run is reused as the `1,2,3` column.

```bash
# Default: arabidopsis 32x, k=39/K=39/S=4/r=0.1/a=3/A=2, all 6 subsets
bash benchmark/work_scripts/dadec_ablation.sh

# Sweep a different parameter set / coverage (point SHORT at that coverage's
# prepared short reads; LONG and REF are coverage-independent and reused)
COVERAGE=20x K1=31 K2=31 SPLIT=1 THRESHOLD=0.08 ABUND1=2 ABUND2=1 \
  SHORT=/path/to/short_20x.fa bash benchmark/work_scripts/dadec_ablation.sh

COVERAGE=32x K1=39 K2=39 SPLIT=4 THRESHOLD=0.1 ABUND1=3 ABUND2=2 \
  SHORT=/home/work/wenhai/dadec/data/arabidopsis/arabidopsis_32x.fa \
  bash benchmark/work_scripts/dadec_ablation.sh current

nohup env \
COVERAGE=32x \
K1=39 \
K2=39 \
SPLIT=4 \
THRESHOLD=0.1 \
ABUND1=3 \
ABUND2=2 \
SHORT=/home/work/wenhai/dadec/data/arabidopsis/arabidopsis_32x.fa \
bash dadec_ablation.sh current \
> logs/dadec_ablation_32x.log 2>&1 &

nohup env \
COVERAGE=32x \
K1=39 \
K2=39 \
SPLIT=4 \
THRESHOLD=0.1 \
ABUND1=3 \
ABUND2=2 \
SHORT=/home/work/wenhai/dadec/data/arabidopsis/arabidopsis_32x.fa \
bash dadec_ablation.sh dev \
> logs/dadec_ablation_32x_dev.log 2>&1 &

# Smoke test a single combination
STAGES_LIST="2" bash benchmark/work_scripts/dadec_ablation.sh
```

The summary table has one row per metric (`Genome fraction (%)`,
`# mismatches per 100 kbp`, `# indels per 100 kbp`, `# misassemblies`, `N50`,
`NGA50`, `Total aligned length`, `Largest alignment`, plus `wall_seconds` and
`max_rss_kb`) and one column per stage combination.
