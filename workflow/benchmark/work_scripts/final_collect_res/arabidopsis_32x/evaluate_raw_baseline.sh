#!/usr/bin/env bash
# Re-evaluate the Arabidopsis raw PacBio baseline with full (non-fast) QUAST.
# This does not modify benchmark/results/raw_long_reads/arabidopsis/full/.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
BAM="/home/yczhang/zyc/final_result/Arabidopsis/data/long/1_A01_customer/m54113_160913_184949.subreads.bam"
REFERENCE="/home/yczhang/zyc/final_result/Arabidopsis/data/Arabidopsis_assembly.fasta"
RESULT_DIR="$ROOT/benchmark/results/raw_long_reads/arabidopsis/quast_pac"
SAMTOOLS="${SAMTOOLS:-/home/work/wenhai/bin/samtools}"
QUAST="${QUAST:-/home/yczhang/zyc/tools/quast/quast.py}"
THREADS="${THREADS:-64}"

[[ -r "$BAM" ]] || { echo "ERROR: BAM is not readable: $BAM" >&2; exit 2; }
[[ -r "$REFERENCE" ]] || { echo "ERROR: reference is not readable: $REFERENCE" >&2; exit 2; }
[[ -x "$SAMTOOLS" ]] || { echo "ERROR: samtools is not executable: $SAMTOOLS" >&2; exit 2; }
[[ -x "$QUAST" ]] || { echo "ERROR: QUAST is not executable: $QUAST" >&2; exit 2; }
[[ "$THREADS" =~ ^[1-9][0-9]*$ ]] || { echo "ERROR: THREADS must be a positive integer" >&2; exit 2; }
[[ ! -e "$RESULT_DIR" ]] || { echo "ERROR: refusing to overwrite existing result directory: $RESULT_DIR" >&2; exit 2; }

mkdir -p "$(dirname "$RESULT_DIR")"
TMP_DIR="$(mktemp -d "$(dirname "$RESULT_DIR")/.revalidate_arabidopsis_raw.XXXXXX")"
LOG="${RESULT_DIR}.log"
cleanup() {
    status=$?
    if [[ $status -ne 0 ]]; then
        echo "ERROR: evaluation failed; command log retained at: $LOG" >&2
    fi
    rm -rf "$TMP_DIR"
    exit "$status"
}
trap cleanup EXIT
RAW_FASTA="$TMP_DIR/raw_long_reads.fa"
RAW_FASTQ="$TMP_DIR/raw_long_reads.fastq"
QUAST_DIR="$TMP_DIR/quast"

{
    "$SAMTOOLS" fasta "$BAM" > "$RAW_FASTA"
    "$SAMTOOLS" fastq "$BAM" > "$RAW_FASTQ"
    "$QUAST" -r "$REFERENCE" -t "$THREADS" "$RAW_FASTA" -o "$QUAST_DIR" \
        --pacbio "$RAW_FASTQ"
} > "$LOG" 2>&1

[[ -s "$QUAST_DIR/report.tsv" ]] || { echo "ERROR: QUAST completed without report.tsv" >&2; exit 2; }
mv "$TMP_DIR" "$RESULT_DIR"
trap - EXIT

echo "Revalidated raw baseline written to: $RESULT_DIR"
echo "Report: $RESULT_DIR/quast/report.tsv"
