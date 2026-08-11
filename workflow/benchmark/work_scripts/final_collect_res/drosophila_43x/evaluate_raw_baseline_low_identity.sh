#!/usr/bin/env bash
set -euo pipefail

# Re-evaluate the raw ONT reads with a lower QUAST alignment-identity threshold.
# No read extraction or correction is performed.

THREADS=${THREADS:-64}
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
RESULT_DIR=${RESULT_DIR:-/home/work/wenhai/dadec/benchmark/results/raw_long_reads/drosophila/quast_low_identity}
RAW_FA=${RAW_FA:-/home/yczhang/zyc/final_result/Drosophila/data/long_reads.fa}
GENOME_MAP=${GENOME_MAP:-$ROOT/benchmark/config/datasets/drosophila_genome_to_id.tsv}
QUAST_HOME=${QUAST_HOME:-/home/yczhang/zyc/tools/quast}
MIN_IDENTITY=${MIN_IDENTITY:-80}

mkdir -p "$RESULT_DIR"
REFERENCE=${REFERENCE:-$(awk -F '\t' '$1 == "drosophila" {print $2; exit}' "$GENOME_MAP")}
[[ -n "$REFERENCE" && -f "$REFERENCE" ]] || { echo "ERROR: reference not found from $GENOME_MAP: $REFERENCE" >&2; exit 2; }
python3 "$QUAST_HOME/quast.py" \
  -r "$REFERENCE" \
  -t "$THREADS" \
  --min-identity "$MIN_IDENTITY" \
  "$RAW_FA" \
  -o "$RESULT_DIR/quast_minid_${MIN_IDENTITY}"

echo "Raw Drosophila baseline written to: $RESULT_DIR/quast_minid_${MIN_IDENTITY}"
