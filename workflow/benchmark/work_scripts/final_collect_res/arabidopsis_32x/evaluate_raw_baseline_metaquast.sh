#!/usr/bin/env bash
set -euo pipefail

# Run MetaQUAST directly on the existing long01.fa file.
# No BAM extraction is performed here.

THREADS=${THREADS:-64}
BASE_DIR=${BASE_DIR:-/home/work/wenhai/dadec/benchmark/work_scripts/final_collect_res/arabidopsis_32x}
RESULT_DIR=${RESULT_DIR:-/home/work/wenhai/dadec/benchmark/results/raw_long_reads/arabidopsis/metaquast_raw}
RAW_FA=${RAW_FA:-/home/yczhang/zyc/final_result/Arabidopsis/data/long/long_a01.fa}
REFERENCE=${REFERENCE:-/home/yczhang/zyc/final_result/Arabidopsis/data/Arabidopsis_assembly.fasta}
QUAST_HOME=${QUAST_HOME:-/home/yczhang/zyc/tools/quast}

mkdir -p "${RESULT_DIR}"

python3 "${QUAST_HOME}/metaquast.py" \
  -r "${REFERENCE}" \
  -t "${THREADS}" \
  "${RAW_FA}" \
  --ambiguity-usage all --ambiguity-score 0.9999 \
  -o "${RESULT_DIR}/metaquast"

