#!/usr/bin/env bash
# Collect strict 10pct Zymo results, including the whitespace-delimited CoLoRMap report.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
RUNS_ROOT="$ROOT/benchmark/runs/zymo_10pct"
RESULT_DIR="$ROOT/benchmark/results/zymo_10pct"
CONFIG_ROOT="$ROOT/benchmark/config/runs/zymo"
RAW_REPORT="$ROOT/benchmark/results/raw_long_reads/zymo/10pct/combined_reference/report.tsv"

RUN_IDS=(
    zymo_10pct_dadec_original_dev_fix_a_k59_k59_s1_a2_a1
    zymo_10pct_fmlrc_original_k21_k59
    zymo_10pct_f_hero_original_k21_k59_hs30_hi1
    zymo_10pct_ratatosk_original_k31_k63
    zymo_10pct_r_hero_original_k31_k63_hs30_hi1
    zymo_10pct_lordec_original_k31_ls5
    zymo_10pct_l_hero_original_k31_ls5_hs30_hi1
    zymo_10pct_colormap_original
    zymo_10pct_proovread_original
)
METHODS=(DADEC FMLRC F_HERO Ratatosk R_HERO LoRDEC L_HERO CoLoRMap Proovread)
CONFIG_FILES=(10pct_dadec.yaml 10pct_fmlrc.yaml 10pct_f_hero.yaml 10pct_ratatosk.yaml 10pct_r_hero.yaml 10pct_lordec.yaml 10pct_l_hero.yaml 10pct_colormap.yaml 10pct_proovread.yaml)

metrics() {
    local report="$1"
    awk '
        $0 ~ /^# mismatches per 100 kbp[[:space:]]/ {mm=$NF}
        $0 ~ /^# indels per 100 kbp[[:space:]]/ {indel=$NF}
        $0 ~ /^Genome fraction \(%\)[[:space:]]/ {coverage=$NF}
        $0 ~ /^# local misassemblies[[:space:]]/ {local=$NF}
        $0 ~ /^# contigs[[:space:]]/ {contigs=$NF}
        END {
            if (mm == "" || indel == "" || coverage == "" || local == "" || contigs == "") exit 2
            printf "%s\t%s\t%s\t%s\t%s\n", mm, indel, coverage, local, contigs
        }
    ' "$report"
}

[[ -f "$RAW_REPORT" ]] || { echo "ERROR: raw report not found: $RAW_REPORT" >&2; exit 2; }
metrics "$RAW_REPORT" >/dev/null || { echo "ERROR: invalid raw report: $RAW_REPORT" >&2; exit 2; }

for i in "${!RUN_IDS[@]}"; do
    run_id="${RUN_IDS[$i]}"; method_dir="$(printf '%s' "${METHODS[$i]}" | tr '[:upper:]' '[:lower:]')"
    report="$RUNS_ROOT/$run_id/output/short_10pct/$method_dir/metaquast.ambiguity9999/combined_reference/report.tsv"
    [[ -f "$RUNS_ROOT/$run_id/benchmark/provenance.json" ]] || { echo "ERROR: missing provenance: $run_id" >&2; exit 2; }
    [[ -f "$CONFIG_ROOT/${CONFIG_FILES[$i]}" ]] || { echo "ERROR: missing config: ${CONFIG_FILES[$i]}" >&2; exit 2; }
    [[ -f "$report" ]] || { echo "ERROR: missing strict report: $run_id" >&2; exit 2; }
    metrics "$report" >/dev/null || { echo "ERROR: invalid strict report: $report" >&2; exit 2; }
done

mkdir -p "$RESULT_DIR"
TMP_DIR="$(mktemp -d "$RESULT_DIR/.collect_zymo_10pct.XXXXXX")"
trap 'rm -rf "$TMP_DIR"' EXIT

{
    printf 'run_id\tparameter_set\tdataset\tlong_coverage\tshort_coverage\tmethod\tambiguity_score\tmismatches_per_100_kbp\tindels_per_100_kbp\thaplotype_coverage_percent\tlocal_misassemblies\tcontigs_number\n'
    for i in "${!RUN_IDS[@]}"; do
        run_id="${RUN_IDS[$i]}"; method="${METHODS[$i]}"; method_dir="$(printf '%s' "$method" | tr '[:upper:]' '[:lower:]')"
        report="$RUNS_ROOT/$run_id/output/short_10pct/$method_dir/metaquast.ambiguity9999/combined_reference/report.tsv"
        printf '%s\toriginal\tzymo\t10pct\t10pct\t%s\t0.9999\t%s\n' "$run_id" "$method" "$(metrics "$report")"
    done
} > "$TMP_DIR/comparative_ambiguity9999_metrics_only.tsv"

{
    printf 'method\tmismatches_per_100_kbp\tindels_per_100_kbp\thaplotype_coverage_percent\tlocal_misassemblies\tcontigs_number\tevaluation_scope\n'
    printf 'Raw\t%s\traw_long_reads\n' "$(metrics "$RAW_REPORT")"
    awk -F '\t' 'NR > 1 {print $6 "\t" $8 "\t" $9 "\t" $10 "\t" $11 "\t" $12 "\tambiguity_0.9999"}' "$TMP_DIR/comparative_ambiguity9999_metrics_only.tsv"
} > "$TMP_DIR/table_ambiguity9999_metrics_only.tsv"

{
    printf 'method\trun_id\trun_config\tprovenance\tresource_log\tmetaquast_report_ambiguity9999\n'
    for i in "${!RUN_IDS[@]}"; do
        run_id="${RUN_IDS[$i]}"; method="${METHODS[$i]}"; method_dir="$(printf '%s' "$method" | tr '[:upper:]' '[:lower:]')"
        resource="$RUNS_ROOT/$run_id/benchmark/short_10pct/$method_dir/resources.time.txt"
        [[ -f "$resource" ]] || resource="MISSING"
        printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$method" "$run_id" \
            "benchmark/config/runs/zymo/${CONFIG_FILES[$i]}" \
            "benchmark/runs/zymo_10pct/$run_id/benchmark/provenance.json" "$resource" \
            "benchmark/runs/zymo_10pct/$run_id/output/short_10pct/$method_dir/metaquast.ambiguity9999/combined_reference/report.tsv"
    done
} > "$TMP_DIR/run_manifest.tsv"

for output in comparative_ambiguity9999_metrics_only.tsv table_ambiguity9999_metrics_only.tsv run_manifest.tsv; do
    mv "$TMP_DIR/$output" "$RESULT_DIR/$output"
done
echo "Collected 9 selected Zymo 10pct strict metric rows into: $RESULT_DIR"
