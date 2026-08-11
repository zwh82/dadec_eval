#!/usr/bin/env bash
# Collect the preselected 3-strain E. coli comparison runs for the manuscript.
#
# Usage (from the repository root):
#   bash benchmark/work_scripts/final_collect_res/ecoli3_20x/collect_results.sh
#
# The run IDs are explicit on purpose.  The runs directory also contains an
# older DADEC executable and a LoRDEC tool-default run; neither is part of the
# manuscript comparison panel.  Raw run directories are never modified.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
RUNS_ROOT="$ROOT/benchmark/runs/ecoli3_20x"
RESULT_DIR="$ROOT/benchmark/results/ecoli3_20x"
HIFIEVAL_SUMMARY="$ROOT/benchmark/results/hifieval/ecoli3_20x/summary.tsv"
PYTHON="${PYTHON:-/home/wenhai/miniconda3/envs/dadec_eval/bin/python}"

if [[ ! -x "$PYTHON" ]]; then
    echo "ERROR: Python interpreter is not executable: $PYTHON" >&2
    exit 2
fi
if [[ ! -d "$RUNS_ROOT" ]]; then
    echo "ERROR: run directory not found: $RUNS_ROOT" >&2
    exit 2
fi
if [[ ! -f "$HIFIEVAL_SUMMARY" ]]; then
    echo "ERROR: HiFiEval summary not found: $HIFIEVAL_SUMMARY" >&2
    exit 2
fi

# Order is retained in the output tables and is the intended comparison panel.
RUN_IDS=(
    ecoli3_20x_dadec_dev_fix_a_k31_k31_s1_a2_a1
    ecoli3_20x_fmlrc_original_k21_k59
    ecoli3_20x_f_hero_original_k21_k59_hs30_hi3
    ecoli3_20x_ratatosk_original_k31_k63
    ecoli3_20x_r_hero_original_k31_k63_hs30_hi3
    ecoli3_20x_lordec_original_k31_ls5
    ecoli3_20x_l_hero_original_k31_ls5_hs30_hi3
    ecoli3_20x_colormap_original
    ecoli3_20x_proovread_original
)
METHODS=(DADEC FMLRC F_HERO Ratatosk R_HERO LoRDEC L_HERO CoLoRMap Proovread)

for run_id in "${RUN_IDS[@]}"; do
    if [[ ! -f "$RUNS_ROOT/$run_id/benchmark/provenance.json" ]]; then
        echo "ERROR: missing provenance for selected run: $run_id" >&2
        exit 2
    fi
done

mkdir -p "$RESULT_DIR"
TMP_DIR="$(mktemp -d "$RESULT_DIR/.collect_ecoli3_20x.XXXXXX")"
trap 'rm -rf "$TMP_DIR"' EXIT

for run_id in "${RUN_IDS[@]}"; do
    "$PYTHON" "$ROOT/benchmark/scripts/collect_run_summaries.py" \
        --runs-root "$RUNS_ROOT" \
        --run-glob "$run_id" \
        --output-all "$TMP_DIR/$run_id.tsv" \
        --output-best "$TMP_DIR/$run_id.best.tsv"
done

{
    head -n 1 "$TMP_DIR/${RUN_IDS[0]}.tsv"
    for run_id in "${RUN_IDS[@]}"; do
        tail -n +2 "$TMP_DIR/$run_id.tsv"
    done
} > "$TMP_DIR/comparative_selected_runs.tsv"

awk -F '\t' 'NR == 1 || $7 == "0.9999"' \
    "$TMP_DIR/comparative_selected_runs.tsv" \
    > "$TMP_DIR/comparative_ambiguity9999.tsv"

{
    printf 'method\trun_id\tprovenance\tresource_log\tmetaquast_report_ambiguity9999\n'
    for i in "${!RUN_IDS[@]}"; do
        run_id="${RUN_IDS[$i]}"
        method="${METHODS[$i]}"
        method_dir="$(printf '%s' "$method" | tr '[:upper:]' '[:lower:]')"
        case "$method_dir" in
            colormap) method_dir=colormap ;;
            proovread) method_dir=proovread ;;
        esac
        printf '%s\t%s\t%s\t%s\t%s\n' \
            "$method" \
            "$run_id" \
            "benchmark/runs/ecoli3_20x/$run_id/benchmark/provenance.json" \
            "benchmark/runs/ecoli3_20x/$run_id/benchmark/short_20x/$method_dir/resources.time.txt" \
            "benchmark/runs/ecoli3_20x/$run_id/output/short_20x/$method_dir/metaquast.ambiguity9999/combined_reference/report.tsv"
    done
} > "$TMP_DIR/run_manifest.tsv"

cp -p "$HIFIEVAL_SUMMARY" "$TMP_DIR/hifieval_summary.tsv"

mv "$TMP_DIR/comparative_selected_runs.tsv" "$RESULT_DIR/comparative_selected_runs.tsv"
mv "$TMP_DIR/comparative_ambiguity9999.tsv" "$RESULT_DIR/comparative_ambiguity9999.tsv"
mv "$TMP_DIR/run_manifest.tsv" "$RESULT_DIR/run_manifest.tsv"
mv "$TMP_DIR/hifieval_summary.tsv" "$RESULT_DIR/hifieval_summary.tsv"

echo "Collected 9 selected E. coli 3-strain runs into: $RESULT_DIR"
