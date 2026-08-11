#!/usr/bin/env bash
set -euo pipefail

# Run QUAST directly on the existing long01.fa file with a lower identity threshold.
# No BAM extraction is performed here.

THREADS=${THREADS:-64}
BASE_DIR=${BASE_DIR:-/home/work/wenhai/dadec/benchmark/work_scripts/final_collect_res/arabidopsis_32x}
RESULT_DIR=${RESULT_DIR:-/home/work/wenhai/dadec/benchmark/results/raw_long_reads/arabidopsis/quast_low_identity}
RAW_FA=${RAW_FA:-/home/yczhang/zyc/final_result/Arabidopsis/data/long/long_a01.fa}
REFERENCE=${REFERENCE:-/home/yczhang/zyc/final_result/Arabidopsis/data/Arabidopsis_assembly.fasta}
QUAST_HOME=${QUAST_HOME:-/home/yczhang/zyc/tools/quast}
MIN_IDENTITY=${MIN_IDENTITY:-80}

mkdir -p "${RESULT_DIR}"

python3 "${QUAST_HOME}/quast.py" \
  -r "${REFERENCE}" \
  -t "${THREADS}" \
  --min-identity "${MIN_IDENTITY}" \
  "${RAW_FA}" \
  -o "${RESULT_DIR}/quast_minid_${MIN_IDENTITY}"

