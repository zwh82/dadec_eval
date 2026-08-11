#!/usr/bin/env bash

# Simulate PacBio-like long reads with PBSIM2.
#
# All settings can be overridden with environment variables. For example:
#   GENOME=/path/to/ref.fa \
#   DATA_DIR=/path/to/output/long \
#   PREFIX=sim_long_error_20x \
#   bash scripts/data/errors_data_sim_long.sh
#
# A multi-sequence FASTA produces one PBSIM shard per input sequence. The
# shards are retained and also concatenated into one FASTQ for downstream
# tools that accept a single long-read input.

set -Eeuo pipefail

readonly SCRIPT_NAME="$(basename "$0")"

GENOME="${GENOME:-/home/yczhang/zyc/final_result/ecoil/data/ref/ecoli1.fa}"
DATA_DIR="${DATA_DIR:-/home/work/wenhai/dadec/data/errors/long}"
PBSIM="${PBSIM:-/home/yczhang/zyc/tools/pbsim2/install/bin/pbsim}"
MODEL="${MODEL:-/home/yczhang/zyc/tools/pbsim2/data/P6C4.model}"

DEPTH="${DEPTH:-20}"
SEED="${SEED:-42}"
PREFIX="${PREFIX:-sim_ecoli_long_error_20x}"
ACCURACY_MEAN="${ACCURACY_MEAN:-0.9}"
LENGTH_MIN="${LENGTH_MIN:-3000}"
LENGTH_MEAN="${LENGTH_MEAN:-10000}"
MERGED_FASTQ="${MERGED_FASTQ:-$DATA_DIR/${PREFIX}.fastq}"

log() {
    printf '[%s] %s\n' "$(date '+%F %T')" "$*"
}

die() {
    printf '%s: ERROR: %s\n' "$SCRIPT_NAME" "$*" >&2
    exit 1
}

[[ -r "$GENOME" ]] || die "genome FASTA is not readable: $GENOME"
[[ -x "$PBSIM" ]] || die "PBSIM executable is not available: $PBSIM"
[[ -r "$MODEL" ]] || die "PBSIM HMM model is not readable: $MODEL"
[[ "$DEPTH" =~ ^[0-9]+([.][0-9]+)?$ ]] || die "DEPTH must be a non-negative number"
[[ "$SEED" =~ ^[0-9]+$ ]] || die "SEED must be a non-negative integer"
[[ "$LENGTH_MIN" =~ ^[1-9][0-9]*$ ]] || die "LENGTH_MIN must be a positive integer"
[[ "$LENGTH_MEAN" =~ ^[1-9][0-9]*([.][0-9]+)?$ ]] || die "LENGTH_MEAN must be positive"
[[ "$ACCURACY_MEAN" =~ ^(0([.][0-9]+)?|1([.]0+)?)$ ]] || \
    die "ACCURACY_MEAN must be between 0 and 1"
[[ -n "$PREFIX" && "$PREFIX" != */* ]] || die "PREFIX must be a non-empty file-name prefix"

sequence_count=$(awk '/^>/ { count++ } END { print count + 0 }' "$GENOME")
((sequence_count > 0)) || die "no FASTA headers were found in $GENOME"

mkdir -p "$DATA_DIR"

shopt -s nullglob
existing=("$DATA_DIR/$PREFIX"_*.fastq "$DATA_DIR/$PREFIX"_*.maf "$DATA_DIR/$PREFIX"_*.ref)
shopt -u nullglob
if ((${#existing[@]} > 0)) || [[ -e "$MERGED_FASTQ" ]]; then
    die "output already exists for prefix '$PREFIX' in $DATA_DIR"
fi

pbsim_log="$DATA_DIR/${PREFIX}.pbsim.log"

log "Genome: $GENOME ($sequence_count sequences)"
log "Depth: ${DEPTH}x; seed: $SEED; accuracy mean: $ACCURACY_MEAN"
log "Read length: minimum $LENGTH_MIN; mean $LENGTH_MEAN"
log "Simulating PBSIM reads -> $DATA_DIR"

"$PBSIM" \
    --prefix "$DATA_DIR/$PREFIX" \
    --depth "$DEPTH" \
    --seed "$SEED" \
    --hmm_model "$MODEL" \
    --accuracy-mean "$ACCURACY_MEAN" \
    --length-min "$LENGTH_MIN" \
    --length-mean "$LENGTH_MEAN" \
    "$GENOME" \
    2>&1 | tee "$pbsim_log"

shopt -s nullglob
fastq_shards=("$DATA_DIR/$PREFIX"_*.fastq)
shopt -u nullglob

((${#fastq_shards[@]} > 0)) || die "PBSIM did not produce any FASTQ shards (see $pbsim_log)"
((${#fastq_shards[@]} == sequence_count)) || \
    die "expected $sequence_count FASTQ shards, found ${#fastq_shards[@]} (see $pbsim_log)"

for shard in "${fastq_shards[@]}"; do
    [[ -s "$shard" ]] || die "PBSIM produced an empty FASTQ shard: $shard"
done

log "Concatenating ${#fastq_shards[@]} FASTQ shards -> $MERGED_FASTQ"
cat "${fastq_shards[@]}" > "$MERGED_FASTQ"
[[ -s "$MERGED_FASTQ" ]] || die "merged FASTQ is empty: $MERGED_FASTQ"

manifest="$DATA_DIR/${PREFIX}.manifest.tsv"
{
    printf 'key\tvalue\n'
    printf 'genome\t%s\n' "$GENOME"
    printf 'sequence_count\t%s\n' "$sequence_count"
    printf 'depth\t%s\n' "$DEPTH"
    printf 'seed\t%s\n' "$SEED"
    printf 'hmm_model\t%s\n' "$MODEL"
    printf 'accuracy_mean\t%s\n' "$ACCURACY_MEAN"
    printf 'length_min\t%s\n' "$LENGTH_MIN"
    printf 'length_mean\t%s\n' "$LENGTH_MEAN"
    printf 'merged_fastq\t%s\n' "$MERGED_FASTQ"
    for shard in "${fastq_shards[@]}"; do
        printf 'fastq_shard\t%s\n' "$shard"
    done
} > "$manifest"

log "Long-read simulation completed successfully"
log "Merged long reads: $MERGED_FASTQ"
log "Manifest: $manifest"
