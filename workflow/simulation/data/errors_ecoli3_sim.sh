#!/usr/bin/env bash

# Reproduce the data/errors simulation with the three-sequence E. coli
# reference, while writing all new outputs under data/errors_ecoli3.
#
# Usage:
#   bash scripts/data/errors_ecoli3_sim.sh [all|short|long]
#
# Examples:
#   bash scripts/data/errors_ecoli3_sim.sh all
#   bash scripts/data/errors_ecoli3_sim.sh long  # resume after short reads
#
# Environment overrides:
#   GENOME, DATA_DIR, SHORT_COVERAGE, LONG_DEPTH, SHORT_CPUS, SEED, MODELS,
#   ISS, MINIMAP2, REFORMAT, PBSIM, PBSIM_MODEL

set -Eeuo pipefail

readonly SCRIPT_NAME="$(basename "$0")"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/../.." && pwd)"

GENOME="${GENOME:-/home/yczhang/zyc/final_result/ecoil/data/ref/ref.fa}"
DATA_DIR="${DATA_DIR:-$PROJECT_ROOT/data/errors_ecoli3}"

SHORT_COVERAGE="${SHORT_COVERAGE:-30}"
LONG_DEPTH="${LONG_DEPTH:-20}"
SHORT_CPUS="${SHORT_CPUS:-1}"
SEED="${SEED:-42}"
MODELS="${MODELS:-MiSeq HiSeq NextSeq NovaSeq}"

ISS="${ISS:-/home/wenhai/miniconda3/envs/dadec_eval/bin/iss}"
MINIMAP2="${MINIMAP2:-/home/wenhai/miniconda3/envs/hero/bin/minimap2}"
REFORMAT="${REFORMAT:-/home/work/wenhai/tools/bbmap/reformat.sh}"
PBSIM="${PBSIM:-/home/yczhang/zyc/tools/pbsim2/install/bin/pbsim}"
PBSIM_MODEL="${PBSIM_MODEL:-/home/yczhang/zyc/tools/pbsim2/data/P6C4.model}"

SHORT_SCRIPT="$SCRIPT_DIR/errors_data_sim.sh"
LONG_SCRIPT="$SCRIPT_DIR/errors_data_sim_long.sh"
STAGE="${1:-all}"

log() {
    printf '[%s] %s\n' "$(date '+%F %T')" "$*"
}

die() {
    printf '%s: ERROR: %s\n' "$SCRIPT_NAME" "$*" >&2
    exit 1
}

usage() {
    printf 'Usage: %s [all|short|long]\n' "$SCRIPT_NAME" >&2
}

case "$STAGE" in
    all|short|long) ;;
    -h|--help)
        usage
        exit 0
        ;;
    *)
        usage
        die "unknown stage: $STAGE"
        ;;
esac

[[ $# -le 1 ]] || {
    usage
    die "too many arguments"
}
[[ -r "$GENOME" ]] || die "genome FASTA is not readable: $GENOME"
[[ -r "$SHORT_SCRIPT" ]] || die "short-read simulation script is not readable: $SHORT_SCRIPT"
[[ -r "$LONG_SCRIPT" ]] || die "long-read simulation script is not readable: $LONG_SCRIPT"

sequence_count=$(awk '/^>/ { count++ } END { print count + 0 }' "$GENOME")
((sequence_count > 0)) || die "no FASTA headers were found in $GENOME"

# A complete all-stage run must start with an empty destination. This protects
# both the original data/errors directory and partial outputs from overwrites.
if [[ "$STAGE" == all && -d "$DATA_DIR" ]]; then
    first_entry=$(find "$DATA_DIR" -mindepth 1 -maxdepth 1 -print -quit)
    [[ -z "$first_entry" ]] || \
        die "DATA_DIR is not empty: $DATA_DIR (use the short or long stage explicitly to resume)"
fi

mkdir -p "$DATA_DIR"

log "Reference: $GENOME"
log "Reference sequences: $sequence_count"
log "Output directory: $DATA_DIR"
log "Stage: $STAGE"

if [[ "$STAGE" == all || "$STAGE" == short ]]; then
    log "Starting short-read simulation: ${SHORT_COVERAGE}x; models: $MODELS"
    GENOME="$GENOME" \
    DATA_DIR="$DATA_DIR" \
    ISS="$ISS" \
    MINIMAP2="$MINIMAP2" \
    REFORMAT="$REFORMAT" \
    COVERAGE="$SHORT_COVERAGE" \
    CPUS="$SHORT_CPUS" \
    SEED="$SEED" \
    MODELS="$MODELS" \
        bash "$SHORT_SCRIPT"
fi

long_prefix="sim_ecoli3_long_error_${LONG_DEPTH}x"
merged_long_fastq="$DATA_DIR/long/${long_prefix}.fastq"

if [[ "$STAGE" == all || "$STAGE" == long ]]; then
    log "Starting long-read simulation: ${LONG_DEPTH}x"
    GENOME="$GENOME" \
    DATA_DIR="$DATA_DIR/long" \
    PBSIM="$PBSIM" \
    MODEL="$PBSIM_MODEL" \
    DEPTH="$LONG_DEPTH" \
    SEED="$SEED" \
    PREFIX="$long_prefix" \
    MERGED_FASTQ="$merged_long_fastq" \
        bash "$LONG_SCRIPT"
fi

manifest="$DATA_DIR/simulation_manifest.tsv"
{
    printf 'key\tvalue\n'
    printf 'reference\t%s\n' "$GENOME"
    printf 'reference_sequences\t%s\n' "$sequence_count"
    printf 'short_coverage\t%s\n' "$SHORT_COVERAGE"
    printf 'short_models\t%s\n' "$MODELS"
    printf 'short_cpus\t%s\n' "$SHORT_CPUS"
    printf 'long_coverage\t%s\n' "$LONG_DEPTH"
    printf 'seed\t%s\n' "$SEED"
    printf 'merged_long_fastq\t%s\n' "$merged_long_fastq"
} > "$manifest"

log "Requested stage completed successfully"
log "Dataset manifest: $manifest"
if [[ "$STAGE" == all || "$STAGE" == long ]]; then
    log "Combined long-read FASTQ: $merged_long_fastq"
fi
