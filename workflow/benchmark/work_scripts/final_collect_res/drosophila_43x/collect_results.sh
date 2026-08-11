#!/usr/bin/env bash
set -euo pipefail

# Collect the report-derived Drosophila 43x corrected-read metrics.
# Comparator runs are legacy/imported runs and may not have resource logs.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
RUNS_ROOT="$ROOT/benchmark/runs/drosophila_43x"
RESULT_DIR="$ROOT/benchmark/results/drosophila_43x"
mkdir -p "$RESULT_DIR"

declare -a METHODS=(DADEC FMLRC F_HERO Ratatosk R_HERO LoRDEC L_HERO CoLoRMap Proovread)
declare -a RUN_IDS=(
  drosophila_43x_dadec_dev_fix_a_k39_k39_s3_a3_a2
  drosophila_43x_fmlrc_k21_k59
  drosophila_43x_f_hero_k21_k59_hs10_hi1
  drosophila_43x_ratatosk_k31_k63
  drosophila_43x_r_hero_k31_k63_hs10_hi1
  drosophila_43x_lordec_k21_ls5
  drosophila_43x_l_hero_k21_ls5_hs10_hi1
  drosophila_43x_colormap
  drosophila_43x_proovread
)
declare -a METHOD_DIRS=(dadec fmlrc f_hero ratatosk r_hero lordec l_hero colormap proovread)

metric() {
  local report="$1" key="$2"
  awk -F '\t' -v k="$key" '$1 == k {print $2; exit}' "$report"
}

printf 'method\tmismatches_per_100_kbp\tindels_per_100_kbp\thaplotype_coverage_percent\tlocal_misassemblies\tcontigs_number\tquast_report\tresource_log_status\n' > "$RESULT_DIR/table_corrected_only.tsv"
printf 'method\trun_id\tquast_report\tresource_log\tresource_log_status\n' > "$RESULT_DIR/run_manifest.tsv"

for i in "${!METHODS[@]}"; do
  method="${METHODS[$i]}"; run_id="${RUN_IDS[$i]}"; method_dir="${METHOD_DIRS[$i]}"
  report="$RUNS_ROOT/$run_id/output/short_43x/$method_dir/quast/report.tsv"
  resource="$RUNS_ROOT/$run_id/benchmark/short_43x/$method_dir/resources.time.txt"
  [[ -f "$report" ]] || { echo "ERROR: missing QUAST report: $report" >&2; exit 2; }
  status=missing
  [[ -f "$resource" ]] && status=present
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$method" "$(metric "$report" '# mismatches per 100 kbp')" \
    "$(metric "$report" '# indels per 100 kbp')" "$(metric "$report" 'Genome fraction (%)')" \
    "$(metric "$report" '# local misassemblies')" "$(metric "$report" '# contigs')" \
    "${report#$ROOT/}" "$status" >> "$RESULT_DIR/table_corrected_only.tsv"
  printf '%s\t%s\t%s\t%s\t%s\n' "$method" "$run_id" "${report#$ROOT/}" "${resource#$ROOT/}" "$status" >> "$RESULT_DIR/run_manifest.tsv"
done

printf '%s\n' 'Raw baseline is maintained separately. Use benchmark/results/raw_long_reads/drosophila/quast_low_identity/quast_minid_80/report.tsv after running evaluate_raw_baseline_low_identity.sh; the existing full report remains available for comparison.' > "$RESULT_DIR/raw_baseline_status.md"
echo "Collected ${#METHODS[@]} Drosophila 43x corrected-read reports into: $RESULT_DIR"
