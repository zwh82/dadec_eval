#!/usr/bin/env bash

# Simulate the three-sequence E. coli dataset using per-sequence ISS
# readcount files. This avoids the ISS coverage_file chunking issue that can
# truncate later FASTA records when the default --n_reads value is too small.
#
# Usage:
#   bash scripts/data/errors_ecoli3_readcount_sim.sh [all|short|long|readcounts]
#
# Examples:
#   bash scripts/data/errors_ecoli3_readcount_sim.sh readcounts
#   bash scripts/data/errors_ecoli3_readcount_sim.sh all
#
# Environment overrides:
#   GENOME, DATA_DIR, SHORT_COVERAGE, LONG_DEPTH, SHORT_CPUS, SEED, MODELS,
#   ISS, MINIMAP2, REFORMAT, PBSIM, PBSIM_MODEL, ACCURACY_MEAN, LENGTH_MIN,
#   LENGTH_MEAN

set -Eeuo pipefail

readonly SCRIPT_NAME="$(basename "$0")"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/../.." && pwd)"

GENOME="${GENOME:-/home/yczhang/zyc/final_result/ecoil/data/ref/ref.fa}"
DATA_DIR="${DATA_DIR:-$PROJECT_ROOT/data/errors_ecoli3_readcount}"

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

ACCURACY_MEAN="${ACCURACY_MEAN:-0.9}"
LENGTH_MIN="${LENGTH_MIN:-3000}"
LENGTH_MEAN="${LENGTH_MEAN:-10000}"

read -r -a MODELS_ARRAY <<< "$MODELS"
STAGE="${1:-all}"

log() {
    printf '[%s] %s\n' "$(date '+%F %T')" "$*"
}

die() {
    printf '%s: ERROR: %s\n' "$SCRIPT_NAME" "$*" >&2
    exit 1
}

usage() {
    printf 'Usage: %s [all|short|long|readcounts]\n' "$SCRIPT_NAME" >&2
}

validate_positive_integer() {
    local name="$1"
    local value="$2"
    [[ "$value" =~ ^[1-9][0-9]*$ ]] || die "$name must be a positive integer (received: $value)"
}

model_slug() {
    printf '%s' "$1" | tr '[:upper:]' '[:lower:]'
}

model_read_length() {
    case "${1,,}" in
        miseq|nextseq)
            printf '301\n'
            ;;
        hiseq)
            printf '126\n'
            ;;
        novaseq)
            printf '151\n'
            ;;
        *)
            die "unsupported ISS model '$1'"
            ;;
    esac
}

case "$STAGE" in
    all|short|long|readcounts) ;;
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
[[ "$SHORT_COVERAGE" =~ ^[0-9]+([.][0-9]+)?$ ]] || die "SHORT_COVERAGE must be a non-negative number"
[[ "$LONG_DEPTH" =~ ^[0-9]+([.][0-9]+)?$ ]] || die "LONG_DEPTH must be a non-negative number"
validate_positive_integer "SHORT_CPUS" "$SHORT_CPUS"
validate_positive_integer "SEED" "$SEED"
((${#MODELS_ARRAY[@]} > 0)) || die "no sequencing models were selected"

if [[ "$STAGE" == all || "$STAGE" == short ]]; then
    [[ -x "$ISS" ]] || die "InSilicoSeq executable is not available: $ISS"
    [[ -x "$MINIMAP2" ]] || die "minimap2 executable is not available: $MINIMAP2"
    [[ -x "$REFORMAT" ]] || die "BBMap reformat.sh is not available: $REFORMAT"
fi

if [[ "$STAGE" == all || "$STAGE" == long ]]; then
    [[ -x "$PBSIM" ]] || die "PBSIM executable is not available: $PBSIM"
    [[ -r "$PBSIM_MODEL" ]] || die "PBSIM HMM model is not readable: $PBSIM_MODEL"
    [[ "$LENGTH_MIN" =~ ^[1-9][0-9]*$ ]] || die "LENGTH_MIN must be a positive integer"
    [[ "$LENGTH_MEAN" =~ ^[1-9][0-9]*([.][0-9]+)?$ ]] || die "LENGTH_MEAN must be positive"
    [[ "$ACCURACY_MEAN" =~ ^(0([.][0-9]+)?|1([.]0+)?)$ ]] || \
        die "ACCURACY_MEAN must be between 0 and 1"
fi

sequence_count=$(awk '/^>/ { count++ } END { print count + 0 }' "$GENOME")
((sequence_count > 0)) || die "no FASTA headers were found in $GENOME"

mkdir -p "$DATA_DIR"

make_readcount_file() {
    local model="$1"
    local slug="$2"
    local read_len="$3"
    local output_dir="$4"
    local readcount_file="$output_dir/${slug}_readcount_${SHORT_COVERAGE}x.tsv"
    local summary_file="$output_dir/${slug}_readcount_${SHORT_COVERAGE}x.summary.tsv"

    awk -v cov="$SHORT_COVERAGE" -v read_len="$read_len" '
        function flush_record() {
            if (id == "") {
                return
            }
            # ISS generates paired-end reads, so keep per-record readcounts even.
            reads = 2 * int(((cov * len / read_len) / 2) + 0.5)
            if (reads < 1 && cov > 0 && len > 0) {
                reads = 2
            }
            printf "%s\t%d\n", id, reads > readcount
            printf "%s\t%d\t%s\t%.6f\t%d\n", id, len, read_len, cov, reads > summary
            total_reads += reads
            total_bases += len
        }
        BEGIN {
            readcount = ARGV[2]
            summary = ARGV[3]
            ARGV[2] = ""
            ARGV[3] = ""
            printf "sequence_id\tsequence_length\tread_length\ttarget_coverage\treadcount\n" > summary
        }
        /^>/ {
            flush_record()
            id = substr($0, 2)
            sub(/[[:space:]].*/, "", id)
            len = 0
            next
        }
        {
            len += length($0)
        }
        END {
            flush_record()
            printf "TOTAL\t%d\t%s\t%.6f\t%d\n", total_bases, read_len, cov, total_reads > summary
        }
    ' "$GENOME" "$readcount_file" "$summary_file"

    [[ -s "$readcount_file" ]] || die "$model readcount file is empty: $readcount_file"
    [[ -s "$summary_file" ]] || die "$model readcount summary is empty: $summary_file"
}

make_all_readcount_files() {
    for model in "${MODELS_ARRAY[@]}"; do
        slug="$(model_slug "$model")"
        read_len="$(model_read_length "$model")"
        output_dir="$DATA_DIR/$slug"
        mkdir -p "$output_dir"
        make_readcount_file "$model" "$slug" "$read_len" "$output_dir"
    done
}

log "Reference: $GENOME"
log "Reference sequences: $sequence_count"
log "Output directory: $DATA_DIR"
log "Stage: $STAGE"
log "Short-read target coverage: ${SHORT_COVERAGE}x"
log "Models: ${MODELS_ARRAY[*]}"

make_all_readcount_files

if [[ "$STAGE" == readcounts ]]; then
    log "Readcount files created successfully"
    exit 0
fi

if [[ "$STAGE" == all || "$STAGE" == short ]]; then
    error_rate_file="$DATA_DIR/sequencing_error_rates.tsv"
    printf 'model\tcoverage\tread_length\trequested_reads\taligned_reads\tmatching_bases\talignment_block_bases\terror_rate\n' \
        > "$error_rate_file"

    for model in "${MODELS_ARRAY[@]}"; do
        slug="$(model_slug "$model")"
        read_len="$(model_read_length "$model")"
        output_dir="$DATA_DIR/$slug"
        output_prefix="$output_dir/${slug}_reads"
        readcount_file="$output_dir/${slug}_readcount_${SHORT_COVERAGE}x.tsv"
        summary_file="$output_dir/${slug}_readcount_${SHORT_COVERAGE}x.summary.tsv"
        requested_reads=$(awk -F '\t' '{ total += $2 } END { print total + 0 }' "$readcount_file")

        if compgen -G "${output_prefix}*" > /dev/null; then
            die "output already exists for $model: ${output_prefix}*"
        fi

        log "Simulating $model reads -> $output_dir"
        log "Read length: $read_len; requested reads: $requested_reads"
        "$ISS" generate \
            --genomes "$GENOME" \
            --readcount_file "$readcount_file" \
            --mode kde \
            --model "$model" \
            --output "$output_prefix" \
            --cpus "$SHORT_CPUS" \
            --seed "$SEED"

        [[ -s "${output_prefix}_R1.fastq" ]] || die "$model did not produce a non-empty R1 FASTQ"
        [[ -s "${output_prefix}_R2.fastq" ]] || die "$model did not produce a non-empty R2 FASTQ"

        interleaved_reads="${output_prefix}.fastq.gz"
        log "Interleaving $model R1/R2 reads -> $interleaved_reads"
        "$REFORMAT" \
            in1="${output_prefix}_R1.fastq" \
            in2="${output_prefix}_R2.fastq" \
            out="$interleaved_reads" \
            verifypaired=t
        [[ -s "$interleaved_reads" ]] || die "$model did not produce a non-empty interleaved FASTQ"

        log "Calculating sequencing error rate for $model"
        alignment_log="$output_dir/${slug}_minimap2.log"
        stats="$({
            "$MINIMAP2" \
                -x sr \
                --secondary=no \
                -t "$SHORT_CPUS" \
                "$GENOME" \
                "$interleaved_reads"
        } 2> "$alignment_log" | awk '
            BEGIN { records = 0; matches = 0; blocks = 0 }
            {
                records += 1
                matches += $10
                blocks += $11
            }
            END {
                if (blocks == 0) {
                    exit 2
                }
                printf "%d\t%d\t%d\t%.10f", records, matches, blocks, 1 - matches / blocks
            }
        ')" || die "failed to calculate the error rate for $model (see $alignment_log)"

        printf '%s\t%s\t%s\t%s\t%s\n' \
            "$model" "$SHORT_COVERAGE" "$read_len" "$requested_reads" "$stats" >> "$error_rate_file"
        log "Completed $model; readcount summary: $summary_file"
    done

    log "Short-read simulation completed successfully"
    log "Error-rate summary: $error_rate_file"
fi

long_prefix="sim_ecoli3_long_error_${LONG_DEPTH}x"
merged_long_fastq="$DATA_DIR/long/${long_prefix}.fastq"

if [[ "$STAGE" == all || "$STAGE" == long ]]; then
    long_script="$SCRIPT_DIR/errors_data_sim_long.sh"
    [[ -r "$long_script" ]] || die "long-read simulation script is not readable: $long_script"

    log "Starting long-read simulation: ${LONG_DEPTH}x"
    GENOME="$GENOME" \
    DATA_DIR="$DATA_DIR/long" \
    PBSIM="$PBSIM" \
    MODEL="$PBSIM_MODEL" \
    DEPTH="$LONG_DEPTH" \
    SEED="$SEED" \
    PREFIX="$long_prefix" \
    ACCURACY_MEAN="$ACCURACY_MEAN" \
    LENGTH_MIN="$LENGTH_MIN" \
    LENGTH_MEAN="$LENGTH_MEAN" \
    MERGED_FASTQ="$merged_long_fastq" \
        bash "$long_script"
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
    printf 'long_accuracy_mean\t%s\n' "$ACCURACY_MEAN"
    printf 'long_length_min\t%s\n' "$LENGTH_MIN"
    printf 'long_length_mean\t%s\n' "$LENGTH_MEAN"
    printf 'seed\t%s\n' "$SEED"
    for model in "${MODELS_ARRAY[@]}"; do
        slug="$(model_slug "$model")"
        read_len="$(model_read_length "$model")"
        printf 'short_readcount_file_%s\t%s\n' "$slug" "$DATA_DIR/$slug/${slug}_readcount_${SHORT_COVERAGE}x.tsv"
        printf 'short_read_length_%s\t%s\n' "$slug" "$read_len"
    done
    printf 'merged_long_fastq\t%s\n' "$merged_long_fastq"
} > "$manifest"

log "Requested stage completed successfully"
log "Dataset manifest: $manifest"
