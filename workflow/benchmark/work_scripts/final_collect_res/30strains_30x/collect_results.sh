#!/usr/bin/env bash
# Collect the configuration-matched 30-strain, 30x comparison runs.
#
# Usage (from the repository root):
#   bash benchmark/work_scripts/final_collect_res/30strains_30x/collect_results.sh
#
# All comparator run IDs follow benchmark/config/runs/30strains/30x_*.yaml.
# DADEC uses the dev_fix_a executable with the parameter values in
# 30x_dadec.yaml. Raw run directories are never modified.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
RUNS_ROOT="$ROOT/benchmark/runs/30strains_30x"
RESULT_DIR="$ROOT/benchmark/results/30strains_30x"
CONFIG_ROOT="$ROOT/benchmark/config/runs/30strains"
PYTHON="${PYTHON:-/home/wenhai/miniconda3/envs/dadec_eval/bin/python}"

if [[ ! -x "$PYTHON" ]]; then
    echo "ERROR: Python interpreter is not executable: $PYTHON" >&2
    exit 2
fi
if [[ ! -d "$RUNS_ROOT" ]]; then
    echo "ERROR: run directory not found: $RUNS_ROOT" >&2
    exit 2
fi

# Order is retained in the output tables and is the intended comparison panel.
RUN_IDS=(
    30strains_30x_dadec_dev_fix_a_k31_k31_s1_a2_a1
    30strains_30x_fmlrc_original_k21_k59
    30strains_30x_f_hero_original_k21_k59_hs10_hi1
    30strains_30x_ratatosk_original_k21_k31
    30strains_30x_r_hero_original_k21_k31_hs10_hi1
    30strains_30x_lordec_original_k31_ls5
    30strains_30x_l_hero_original_k31_ls5_hs10_hi1
    30strains_30x_colormap_original
    30strains_30x_proovread_original
)
METHODS=(DADEC FMLRC F_HERO Ratatosk R_HERO LoRDEC L_HERO CoLoRMap Proovread)
CONFIG_FILES=(
    30x_dadec.yaml
    30x_fmlrc.yaml
    30x_f_hero.yaml
    30x_ratatosk.yaml
    30x_r_hero.yaml
    30x_lordec.yaml
    30x_l_hero.yaml
    30x_colormap.yaml
    30x_proovread.yaml
)

for i in "${!RUN_IDS[@]}"; do
    run_id="${RUN_IDS[$i]}"
    config="$CONFIG_ROOT/${CONFIG_FILES[$i]}"
    if [[ ! -f "$RUNS_ROOT/$run_id/benchmark/provenance.json" ]]; then
        echo "ERROR: missing provenance for selected run: $run_id" >&2
        exit 2
    fi
    if [[ ! -f "$config" ]]; then
        echo "ERROR: missing configuration file: $config" >&2
        exit 2
    fi
done

mkdir -p "$RESULT_DIR"
TMP_DIR="$(mktemp -d "$RESULT_DIR/.collect_30strains_30x.XXXXXX")"
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
    printf 'method\trun_id\trun_config\tprovenance\tresource_log\tmetaquast_report_ambiguity9999\n'
    for i in "${!RUN_IDS[@]}"; do
        run_id="${RUN_IDS[$i]}"
        method="${METHODS[$i]}"
        method_dir="$(printf '%s' "$method" | tr '[:upper:]' '[:lower:]')"
        case "$method_dir" in
            colormap) method_dir=colormap ;;
            proovread) method_dir=proovread ;;
        esac
        printf '%s\t%s\t%s\t%s\t%s\t%s\n' \
            "$method" \
            "$run_id" \
            "benchmark/config/runs/30strains/${CONFIG_FILES[$i]}" \
            "benchmark/runs/30strains_30x/$run_id/benchmark/provenance.json" \
            "benchmark/runs/30strains_30x/$run_id/benchmark/short_30x/$method_dir/resources.time.txt" \
            "benchmark/runs/30strains_30x/$run_id/output/short_30x/$method_dir/metaquast.ambiguity9999/combined_reference/report.tsv"
    done
} > "$TMP_DIR/run_manifest.tsv"

mv "$TMP_DIR/comparative_selected_runs.tsv" "$RESULT_DIR/comparative_selected_runs.tsv"
mv "$TMP_DIR/comparative_ambiguity9999.tsv" "$RESULT_DIR/comparative_ambiguity9999.tsv"
mv "$TMP_DIR/run_manifest.tsv" "$RESULT_DIR/run_manifest.tsv"

echo "Collected 9 selected 30-strain, 30x runs into: $RESULT_DIR"
