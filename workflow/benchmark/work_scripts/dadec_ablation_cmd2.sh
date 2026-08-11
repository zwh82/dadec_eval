#!/usr/bin/env bash
# Convenience launcher for the two supported datasets.
# Usage: bash dadec_ablation_cmd.sh {arabidopsis|30strains} [current|dev] [suffix]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VARIANT="${2:-current}"
SUFFIX="${3:-}"

case "${1:-}" in
  arabidopsis)
    # Real Arabidopsis reads; QUAST and the existing 32x baseline are used.
    export DATASET=arabidopsis COVERAGE=32x K1=39 K2=39 SPLIT=4
    export THRESHOLD=0.1 ABUND1=3 ABUND2=2
    export SHORT="${SHORT:-/home/work/wenhai/dadec/data/arabidopsis/arabidopsis_32x.fa}"
    export LONG="${LONG:-/home/work/wenhai/dadec/data/arabidopsis/arabidopsis_lr_10x.fa}"
    export STAGES_LIST="${STAGES_LIST:-1 2 3 1,2 1,3 2,3 1,2,3}"
    ;;
  30strains)
    # Simulated metagenome; METAQUAST is selected automatically by the driver.
    export DATASET=30strains COVERAGE="${COVERAGE:-30x}" K1="${K1:-31}" K2="${K2:-31}"
    export SPLIT="${SPLIT:-10}" THRESHOLD="${THRESHOLD:-0.2}"
    export ABUND1="${ABUND1:-5}" ABUND2="${ABUND2:-1}"
    export SHORT="${SHORT:-/home/work/wenhai/dadec/data/30strains/sim_30strains_short_30x.fq.gz}"
    export LONG="${LONG:-/home/work/wenhai/dadec/data/30strains/sim_30strains_long_10x.fq.gz}"
    # REF may be supplied by the caller; otherwise the driver uses the baseline
    # run's prepared combined reference.
    export STAGES_LIST="${STAGES_LIST:-1,3 1,2,3}"
    export REF=/home/work/wenhai/dadec/data/ref/30strains.fa
    # export Ambiguity=0.9999
    export QUAST_THREADS=64
    ;;
  30strains_legacy)
    # Simulated metagenome; METAQUAST is selected automatically by the driver.
    export DATASET=30strains_legacy COVERAGE="${COVERAGE:-30x}" K1="${K1:-31}" K2="${K2:-31}"
    export SPLIT="${SPLIT:-5}" THRESHOLD="${THRESHOLD:-0.08}"
    export ABUND1="${ABUND1:-2}" ABUND2="${ABUND2:-1}"
    export SHORT="${SHORT:-/home/yczhang/zyc/final_result/30strains/data/short/short_reads3.fa}"
    export LONG="${LONG:-/home/yczhang/zyc/final_result/30strains/data/long/long_reads.fa}"
    # REF may be supplied by the caller; otherwise the driver uses the baseline
    # run's prepared combined reference.
    export STAGES_LIST="${STAGES_LIST:-1,3 1,2,3}"
    export REF=/home/yczhang/zyc/final_result/30strains/data/ref/ref.fa
    export AMBIGUITY_SCORES="${AMBIGUITY_SCORES:-0.99,0.9999}"
    ;;
  *)
    echo "Usage: bash ${BASH_SOURCE[0]} {arabidopsis|30strains} [current|dev] [suffix]" >&2
    exit 2
    ;;
esac

exec bash "$SCRIPT_DIR/dadec_ablation.sh" "$VARIANT" "$SUFFIX"
