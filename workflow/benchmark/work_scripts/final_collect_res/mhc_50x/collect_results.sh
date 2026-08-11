#!/usr/bin/env bash
# Collect strict metric-only results for simulated MHC PacBio and ONT datasets.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
RESULT_ROOT="$ROOT/benchmark/results"
PYTHON="${PYTHON:-/home/wenhai/miniconda3/envs/dadec_eval/bin/python}"

METHODS=(DADEC FMLRC F_HERO Ratatosk R_HERO LoRDEC L_HERO CoLoRMap Proovread)
CONFIG_FILES=(50x_dadec.yaml 50x_fmlrc.yaml 50x_f_hero.yaml 50x_ratatosk.yaml 50x_r_hero.yaml 50x_lordec.yaml 50x_l_hero.yaml 50x_colormap.yaml 50x_proovread.yaml)
PAC_RUN_IDS=(
    mhc_pac_50x_dadec_dev_fix_a_k63_k63_s1_a2_a1
    mhc_pac_50x_fmlrc_original_k21_k59
    mhc_pac_50x_f_hero_original_k21_k59_hs3_hi1
    mhc_pac_50x_ratatosk_original_k31_k63
    mhc_pac_50x_r_hero_original_k31_k63_hs10_hi1
    mhc_pac_50x_lordec_original_k59_ls5
    mhc_pac_50x_l_hero_original_k59_ls5_hs10_hi1
    mhc_pac_50x_colormap_original
    mhc_pac_50x_proovread_original
)
ONT_RUN_IDS=(
    mhc_ont_50x_dadec_dev_fix_a_k63_k63_s1_a2_a1
    mhc_ont_50x_fmlrc_original_k21_k59
    mhc_ont_50x_f_hero_original_k21_k59_hs5_hi1
    mhc_ont_50x_ratatosk_original_k31_k63
    mhc_ont_50x_r_hero_original_k31_k63_hs10_hi1
    mhc_ont_50x_lordec_original_k31_ls5
    mhc_ont_50x_l_hero_original_k31_ls5_hs10_hi1
    mhc_ont_50x_colormap_original
    mhc_ont_50x_proovread_original
)

[[ -x "$PYTHON" ]] || { echo "ERROR: Python interpreter is not executable: $PYTHON" >&2; exit 2; }

collect_dataset() {
    local dataset="$1" runs_root="$2" config_root="$3" raw_report="$4"
    shift 4
    local -a run_ids=("$@")
    local result_dir="$RESULT_ROOT/${dataset}_50x"
    local tmp_dir
    [[ -f "$raw_report" ]] || { echo "ERROR: raw report not found: $raw_report" >&2; exit 2; }
    mkdir -p "$result_dir"
    tmp_dir="$(mktemp -d "$result_dir/.collect_${dataset}_50x.XXXXXX")"

    for i in "${!run_ids[@]}"; do
        local run_id="${run_ids[$i]}" method="${METHODS[$i]}" method_dir report
        method_dir="$(printf '%s' "$method" | tr '[:upper:]' '[:lower:]')"
        report="$runs_root/$run_id/output/short_50x/$method_dir/metaquast.ambiguity9999/combined_reference/report.tsv"
        [[ -f "$runs_root/$run_id/benchmark/provenance.json" ]] || { echo "ERROR: missing provenance: $run_id" >&2; rm -rf "$tmp_dir"; exit 2; }
        [[ -f "$config_root/${CONFIG_FILES[$i]}" ]] || { echo "ERROR: missing config: ${CONFIG_FILES[$i]}" >&2; rm -rf "$tmp_dir"; exit 2; }
        [[ -f "$report" ]] || { echo "ERROR: missing strict report: $run_id" >&2; rm -rf "$tmp_dir"; exit 2; }
        "$PYTHON" "$ROOT/benchmark/scripts/parse_metaquast.py" \
            --dataset "$dataset" --long-coverage 10x --run-id "$run_id" --parameter-set original \
            --coverages 50x --methods "$method" --ambiguity-scores 0.9999 --reports "$report" --output "$tmp_dir/$i.tsv"
    done

    {
        head -n 1 "$tmp_dir/0.tsv"
        for i in "${!run_ids[@]}"; do tail -n +2 "$tmp_dir/$i.tsv"; done
    } > "$tmp_dir/comparative_ambiguity9999_metrics_only.tsv"
    {
        printf 'method\tmismatches_per_100_kbp\tindels_per_100_kbp\thaplotype_coverage_percent\tlocal_misassemblies\tcontigs_number\tevaluation_scope\n'
        awk -F '\t' '$1 == "# mismatches per 100 kbp" {mm=$2}; $1 == "# indels per 100 kbp" {indel=$2}; $1 == "Genome fraction (%)" {coverage=$2}; $1 == "# local misassemblies" {local=$2}; $1 == "# contigs" {contigs=$2} END {if (mm == "" || indel == "" || coverage == "" || local == "" || contigs == "") exit 2; print "Raw\t" mm "\t" indel "\t" coverage "\t" local "\t" contigs "\traw_long_reads"}' "$raw_report"
        awk -F '\t' 'NR > 1 {sub(/\r$/, "", $12); print $6 "\t" $8 "\t" $9 "\t" $10 "\t" $11 "\t" $12 "\tambiguity_0.9999"}' "$tmp_dir/comparative_ambiguity9999_metrics_only.tsv"
    } > "$tmp_dir/table_ambiguity9999_metrics_only.tsv"
    {
        printf 'method\trun_id\trun_config\tprovenance\tresource_log\tmetaquast_report_ambiguity9999\n'
        for i in "${!run_ids[@]}"; do
            local run_id="${run_ids[$i]}" method="${METHODS[$i]}" method_dir resource
            method_dir="$(printf '%s' "$method" | tr '[:upper:]' '[:lower:]')"
            resource="$runs_root/$run_id/benchmark/short_50x/$method_dir/resources.time.txt"
            [[ -f "$resource" ]] || resource="MISSING"
            printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$method" "$run_id" \
                "benchmark/config/runs/$dataset/${CONFIG_FILES[$i]}" \
                "benchmark/runs/${dataset}_50x/$run_id/benchmark/provenance.json" "$resource" \
                "benchmark/runs/${dataset}_50x/$run_id/output/short_50x/$method_dir/metaquast.ambiguity9999/combined_reference/report.tsv"
        done
    } > "$tmp_dir/run_manifest.tsv"
    for output in comparative_ambiguity9999_metrics_only.tsv table_ambiguity9999_metrics_only.tsv run_manifest.tsv; do mv "$tmp_dir/$output" "$result_dir/$output"; done
    rm -rf "$tmp_dir"
    echo "Collected 9 selected $dataset, 50x metric-only runs into: $result_dir"
}

collect_dataset mhc_pac "$ROOT/benchmark/runs/mhc_pac_50x" "$ROOT/benchmark/config/runs/mhc_pac" "$ROOT/benchmark/results/raw_long_reads/mhc_pac/full/combined_reference/report.tsv" "${PAC_RUN_IDS[@]}"
collect_dataset mhc_ont "$ROOT/benchmark/runs/mhc_ont_50x" "$ROOT/benchmark/config/runs/mhc_ont" "$ROOT/benchmark/results/raw_long_reads/mhc_ont/full/combined_reference/report.tsv" "${ONT_RUN_IDS[@]}"
