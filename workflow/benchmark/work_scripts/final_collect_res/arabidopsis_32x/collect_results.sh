#!/usr/bin/env bash
# Collect configuration-matched Arabidopsis 32x corrected-read results.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
RUNS_ROOT="$ROOT/benchmark/runs/arabidopsis_32x"
RESULT_DIR="$ROOT/benchmark/results/arabidopsis_32x"
CONFIG_ROOT="$ROOT/benchmark/config/runs/arabidopsis"
PYTHON="${PYTHON:-/home/wenhai/miniconda3/envs/dadec_eval/bin/python}"

RUN_IDS=(
    arabidopsis_32x_dadec_dev_fix_a_k39_k39_s4_a3_a2_t0p1
    arabidopsis_32x_fmlrc_original_k21_k59
    arabidopsis_32x_f_hero_original_k21_k59_hs10_hi1
    arabidopsis_32x_ratatosk_original_k21_k31
    arabidopsis_32x_r_hero_original_k21_k31_hs10_hi1
    arabidopsis_32x_lordec_original_k39_ls5
    arabidopsis_32x_l_hero_original_k39_ls5_hs10_hi1
    arabidopsis_32x_colormap_original
    arabidopsis_32x_proovread_original
)
METHODS=(DADEC FMLRC F_HERO Ratatosk R_HERO LoRDEC L_HERO CoLoRMap Proovread)
CONFIG_FILES=(32x_dadec.yaml 32x_fmlrc.yaml 32x_f_hero.yaml 32x_ratatosk.yaml 32x_r_hero.yaml 32x_lordec.yaml 32x_l_hero.yaml 32x_colormap.yaml 32x_proovread.yaml)

[[ -x "$PYTHON" ]] || { echo "ERROR: Python interpreter is not executable: $PYTHON" >&2; exit 2; }
[[ -d "$RUNS_ROOT" ]] || { echo "ERROR: run directory not found: $RUNS_ROOT" >&2; exit 2; }

for i in "${!RUN_IDS[@]}"; do
    run_id="${RUN_IDS[$i]}"; method_dir="$(printf '%s' "${METHODS[$i]}" | tr '[:upper:]' '[:lower:]')"
    [[ -f "$RUNS_ROOT/$run_id/benchmark/provenance.json" ]] || { echo "ERROR: missing provenance: $run_id" >&2; exit 2; }
    [[ -f "$CONFIG_ROOT/${CONFIG_FILES[$i]}" ]] || { echo "ERROR: missing config: ${CONFIG_FILES[$i]}" >&2; exit 2; }
    [[ -f "$RUNS_ROOT/$run_id/benchmark/short_32x/$method_dir/resources.time.txt" ]] || { echo "ERROR: missing resource log: $run_id" >&2; exit 2; }
    [[ -f "$RUNS_ROOT/$run_id/output/short_32x/$method_dir/quast/report.tsv" ]] || { echo "ERROR: missing QUAST report: $run_id" >&2; exit 2; }
done

mkdir -p "$RESULT_DIR"
TMP_DIR="$(mktemp -d "$RESULT_DIR/.collect_arabidopsis_32x.XXXXXX")"
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

{
    printf 'method\tmismatches_per_100_kbp\tindels_per_100_kbp\thaplotype_coverage_percent\tlocal_misassemblies\tcontigs_number\n'
    awk -F '\t' 'NR > 1 {sub(/\r$/, "", $15); print $6 "\t" $11 "\t" $12 "\t" $13 "\t" $14 "\t" $15}' "$TMP_DIR/comparative_selected_runs.tsv"
} > "$TMP_DIR/table_corrected_only.tsv"

{
    printf 'method\trun_id\trun_config\tprovenance\tresource_log\tquast_report\n'
    for i in "${!RUN_IDS[@]}"; do
        run_id="${RUN_IDS[$i]}"; method="${METHODS[$i]}"; method_dir="$(printf '%s' "$method" | tr '[:upper:]' '[:lower:]')"
        printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$method" "$run_id" \
            "benchmark/config/runs/arabidopsis/${CONFIG_FILES[$i]}" \
            "benchmark/runs/arabidopsis_32x/$run_id/benchmark/provenance.json" \
            "benchmark/runs/arabidopsis_32x/$run_id/benchmark/short_32x/$method_dir/resources.time.txt" \
            "benchmark/runs/arabidopsis_32x/$run_id/output/short_32x/$method_dir/quast/report.tsv"
    done
} > "$TMP_DIR/run_manifest.tsv"

printf '%s\n' \
    'Raw-long-read baseline is maintained separately from the corrected-read collection. For manuscript Table 3, use benchmark/results/raw_long_reads/arabidopsis/quast_low_identity/quast_minid_80/report.tsv (QUAST --min-identity 80), which reports 99.990% genome fraction, 4,403.47 mismatches, 7,135.62 indels, 73,242 local misassemblies, and 545,902 contigs. Other raw evaluations are documented in benchmark/work_scripts/final_collect_res/arabidopsis_32x/README.md.' \
    > "$TMP_DIR/raw_baseline_status.md"

for output in comparative_selected_runs.tsv table_corrected_only.tsv run_manifest.tsv raw_baseline_status.md; do
    mv "$TMP_DIR/$output" "$RESULT_DIR/$output"
done
echo "Collected 9 selected Arabidopsis 32x corrected-read runs into: $RESULT_DIR"
