#!/usr/bin/env bash

# Simulate paired-end Illumina reads with different InSilicoSeq error models.
# Configuration can be overridden with environment variables, for example:
#   COVERAGE=10 CPUS=1 bash scripts/data/errors_data_sim.sh
#   MODELS="MiSeq HiSeq" bash scripts/data/errors_data_sim.sh

set -Eeuo pipefail

readonly SCRIPT_NAME="$(basename "$0")"

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
GENOME="${GENOME:-/home/yczhang/zyc/final_result/ecoil/data/ref/ecoli1.fa}"
DATA_DIR="${DATA_DIR:-/home/work/wenhai/dadec/data/errors}"
ISS="${ISS:-/home/wenhai/miniconda3/envs/dadec_eval/bin/iss}"
MINIMAP2="${MINIMAP2:-/home/wenhai/miniconda3/envs/hero/bin/minimap2}"
REFORMAT="${REFORMAT:-/home/work/wenhai/tools/bbmap/reformat.sh}"

COVERAGE="${COVERAGE:-30}"
CPUS="${CPUS:-1}"
SEED="${SEED:-42}"

# Built-in ISS profiles. MODELS may be overridden with a space-separated list.
read -r -a MODELS_ARRAY <<< "${MODELS:-MiSeq HiSeq NextSeq NovaSeq}"

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
log() {
    printf '[%s] %s\n' "$(date '+%F %T')" "$*"
}

die() {
    printf '%s: ERROR: %s\n' "$SCRIPT_NAME" "$*" >&2
    exit 1
}

validate_positive_integer() {
    local name="$1"
    local value="$2"
    [[ "$value" =~ ^[1-9][0-9]*$ ]] || die "$name must be a positive integer (received: $value)"
}

model_slug() {
    printf '%s' "$1" | tr '[:upper:]' '[:lower:]'
}

# -----------------------------------------------------------------------------
# Validation and shared input
# -----------------------------------------------------------------------------
[[ -r "$GENOME" ]] || die "genome FASTA is not readable: $GENOME"
[[ -x "$ISS" ]] || die "InSilicoSeq executable is not available: $ISS"
[[ -x "$MINIMAP2" ]] || die "minimap2 executable is not available: $MINIMAP2"
[[ -x "$REFORMAT" ]] || die "BBMap reformat.sh is not available: $REFORMAT"
[[ "$COVERAGE" =~ ^[0-9]+([.][0-9]+)?$ ]] || die "COVERAGE must be a non-negative number"
validate_positive_integer "CPUS" "$CPUS"
validate_positive_integer "SEED" "$SEED"
((${#MODELS_ARRAY[@]} > 0)) || die "no sequencing models were selected"

mkdir -p "$DATA_DIR"

# InSilicoSeq matches coverage entries against the first token of each FASTA
# header. One entry is written for every sequence, so multi-contig references
# are also supported.
COVERAGE_FILE="$DATA_DIR/coverage_${COVERAGE}x.tsv"
: > "$COVERAGE_FILE"
while IFS= read -r header; do
    sequence_id="${header#>}"
    sequence_id="${sequence_id%%[[:space:]]*}"
    [[ -n "$sequence_id" ]] && printf '%s\t%s\n' "$sequence_id" "$COVERAGE" >> "$COVERAGE_FILE"
done < <(grep '^>' "$GENOME")

[[ -s "$COVERAGE_FILE" ]] || die "no FASTA headers were found in $GENOME"

# One row is appended after each model has been simulated and evaluated.
ERROR_RATE_FILE="$DATA_DIR/sequencing_error_rates.tsv"
printf 'model\tcoverage\taligned_reads\tmatching_bases\talignment_block_bases\terror_rate\n' \
    > "$ERROR_RATE_FILE"

# -----------------------------------------------------------------------------
# Simulation
# -----------------------------------------------------------------------------
log "Genome: $GENOME"
log "Coverage: ${COVERAGE}x; CPUs: $CPUS; seed: $SEED"
log "Models: ${MODELS_ARRAY[*]}"

for model in "${MODELS_ARRAY[@]}"; do
    case "${model,,}" in
        miseq|miseq-20|miseq-24|miseq-28|miseq-32|miseq-36|hiseq|nextseq|novaseq)
            ;;
        *)
            die "unsupported ISS model '$model'"
            ;;
    esac

    slug="$(model_slug "$model")"
    output_dir="$DATA_DIR/$slug"
    output_prefix="$output_dir/${slug}_reads"
    mkdir -p "$output_dir"

    # Refuse to silently mix a new run with incomplete files from an old run.
    if compgen -G "${output_prefix}*" > /dev/null; then
        die "output already exists for $model: ${output_prefix}*"
    fi

    log "Simulating $model reads -> $output_dir"
    "$ISS" generate \
        --genomes "$GENOME" \
        --coverage_file "$COVERAGE_FILE" \
        --mode kde \
        --model "$model" \
        --output "$output_prefix" \
        --cpus "$CPUS" \
        --seed "$SEED"

    [[ -s "${output_prefix}_R1.fastq" ]] || die "$model did not produce a non-empty R1 FASTQ"
    [[ -s "${output_prefix}_R2.fastq" ]] || die "$model did not produce a non-empty R2 FASTQ"

    # Keep the original R1/R2 files and additionally create one interleaved,
    # gzip-compressed paired-end FASTQ, as in the original workflow.
    interleaved_reads="${output_prefix}.fastq.gz"
    log "Interleaving $model R1/R2 reads -> $interleaved_reads"
    "$REFORMAT" \
        in1="${output_prefix}_R1.fastq" \
        in2="${output_prefix}_R2.fastq" \
        out="$interleaved_reads" \
        verifypaired=t
    [[ -s "$interleaved_reads" ]] || die "$model did not produce a non-empty interleaved FASTQ"

    # PAF columns 10 and 11 are matching bases and alignment block length.
    # Secondary alignments are disabled so the same read is not counted twice.
    log "Calculating the sequencing error rate for $model"
    alignment_log="$output_dir/${slug}_minimap2.log"
    stats="$({
        "$MINIMAP2" \
            -x sr \
            --secondary=no \
            -t "$CPUS" \
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

    printf '%s\t%s\t%s\n' "$model" "$COVERAGE" "$stats" >> "$ERROR_RATE_FILE"
    error_rate="${stats##*$'\t'}"
    log "Completed $model; sequencing error rate: $error_rate"
done

log "All simulations completed successfully"
log "Error-rate summary: $ERROR_RATE_FILE"
