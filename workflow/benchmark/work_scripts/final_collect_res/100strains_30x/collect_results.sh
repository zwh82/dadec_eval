#!/usr/bin/env bash
# Collect the configuration-matched 100S-BA (broad-abundance), 30x comparison.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
RUNS_ROOT="$ROOT/benchmark/runs/100strains_30x"
RESULT_DIR="$ROOT/benchmark/results/100strains_30x"
CONFIG_ROOT="$ROOT/benchmark/config/runs/100strains"
RAW_REPORT="$ROOT/benchmark/results/raw_long_reads/100strains/full/combined_reference/report.tsv"
PYTHON="${PYTHON:-/home/wenhai/miniconda3/envs/dadec_eval/bin/python}"

RUN_IDS=(
    100strains_30x_dadec_dev_fix_a_k31_k31_s3_a2_a1
    100strains_30x_fmlrc_original_k21_k59
    100strains_30x_ratatosk_original_k31_k63
    100strains_30x_lordec_original_k31_ls5
    100strains_30x_colormap_original
    100strains_30x_proovread_original
)
METHODS=(DADEC FMLRC Ratatosk LoRDEC CoLoRMap Proovread)
CONFIG_FILES=(30x_dadec.yaml 30x_fmlrc.yaml 30x_ratatosk.yaml 30x_lordec.yaml 30x_colormap.yaml 30x_proovread.yaml)

[[ -x "$PYTHON" ]] || { echo "ERROR: Python interpreter is not executable: $PYTHON" >&2; exit 2; }
[[ -d "$RUNS_ROOT" ]] || { echo "ERROR: run directory not found: $RUNS_ROOT" >&2; exit 2; }
[[ -f "$RAW_REPORT" ]] || { echo "ERROR: raw-read report not found: $RAW_REPORT" >&2; exit 2; }

for i in "${!RUN_IDS[@]}"; do
    run_id="${RUN_IDS[$i]}"
    method_dir="$(printf '%s' "${METHODS[$i]}" | tr '[:upper:]' '[:lower:]')"
    report="$RUNS_ROOT/$run_id/output/short_30x/$method_dir/metaquast.ambiguity9999/combined_reference/report.tsv"
    [[ -f "$RUNS_ROOT/$run_id/benchmark/provenance.json" ]] || { echo "ERROR: missing provenance: $run_id" >&2; exit 2; }
    [[ -f "$CONFIG_ROOT/${CONFIG_FILES[$i]}" ]] || { echo "ERROR: missing config: ${CONFIG_FILES[$i]}" >&2; exit 2; }
    [[ -f "$RUNS_ROOT/$run_id/benchmark/short_30x/$method_dir/resources.time.txt" ]] || { echo "ERROR: missing resource log: $run_id" >&2; exit 2; }
    [[ -f "$report" ]] || { echo "ERROR: missing strict report: $run_id" >&2; exit 2; }
done

mkdir -p "$RESULT_DIR"
TMP_DIR="$(mktemp -d "$RESULT_DIR/.collect_100strains_30x.XXXXXX")"
trap 'rm -rf "$TMP_DIR"' EXIT

for run_id in "${RUN_IDS[@]}"; do
    "$PYTHON" "$ROOT/benchmark/scripts/collect_run_summaries.py" \
        --runs-root "$RUNS_ROOT" --run-glob "$run_id" \
        --output-all "$TMP_DIR/$run_id.tsv" --output-best "$TMP_DIR/$run_id.best.tsv"
done

{
    head -n 1 "$TMP_DIR/${RUN_IDS[0]}.tsv"
    for run_id in "${RUN_IDS[@]}"; do tail -n +2 "$TMP_DIR/$run_id.tsv"; done
} > "$TMP_DIR/comparative_selected_runs.tsv"

awk -F '\t' 'NR == 1 || $7 == "0.9999"' "$TMP_DIR/comparative_selected_runs.tsv" > "$TMP_DIR/comparative_ambiguity9999.tsv"

{
    printf 'method\tmismatches_per_100_kbp\tindels_per_100_kbp\thaplotype_coverage_percent\tlocal_misassemblies\tcontigs_number\tevaluation_scope\n'
    awk -F '\t' '
        $1 == "# mismatches per 100 kbp" {mm=$2}
        $1 == "# indels per 100 kbp" {indel=$2}
        $1 == "Genome fraction (%)" {coverage=$2}
        $1 == "# local misassemblies" {local=$2}
        $1 == "# contigs" {contigs=$2}
        END {if (mm == "" || indel == "" || coverage == "" || local == "" || contigs == "") exit 2; print "Raw\t" mm "\t" indel "\t" coverage "\t" local "\t" contigs "\traw_long_reads"}' "$RAW_REPORT"
    awk -F '\t' 'NR > 1 {sub(/\r$/, "", $15); print $6 "\t" $11 "\t" $12 "\t" $13 "\t" $14 "\t" $15 "\tambiguity_0.9999"}' "$TMP_DIR/comparative_ambiguity9999.tsv"
} > "$TMP_DIR/table_ambiguity9999.tsv"

{
    printf 'method\trun_id\trun_config\tprovenance\tresource_log\tmetaquast_report_ambiguity9999\n'
    for i in "${!RUN_IDS[@]}"; do
        run_id="${RUN_IDS[$i]}"; method="${METHODS[$i]}"; method_dir="$(printf '%s' "$method" | tr '[:upper:]' '[:lower:]')"
        printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$method" "$run_id" \
            "benchmark/config/runs/100strains/${CONFIG_FILES[$i]}" \
            "benchmark/runs/100strains_30x/$run_id/benchmark/provenance.json" \
            "benchmark/runs/100strains_30x/$run_id/benchmark/short_30x/$method_dir/resources.time.txt" \
            "benchmark/runs/100strains_30x/$run_id/output/short_30x/$method_dir/metaquast.ambiguity9999/combined_reference/report.tsv"
    done
} > "$TMP_DIR/run_manifest.tsv"

printf '%s\n' \
    '**Table note.** The 100S-BA panel includes the six methods that completed evaluation. F_HERO, R_HERO, and L_HERO were not included because their multi-round correction and evaluation runs were terminated after exceeding 24 h.' \
    > "$TMP_DIR/table_note.md"

for output in comparative_selected_runs.tsv comparative_ambiguity9999.tsv table_ambiguity9999.tsv run_manifest.tsv table_note.md; do
    mv "$TMP_DIR/$output" "$RESULT_DIR/$output"
done
echo "Collected 6 selected 100S-BA, 30x runs into: $RESULT_DIR"
