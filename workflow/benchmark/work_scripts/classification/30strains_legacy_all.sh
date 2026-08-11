#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

cd "$ROOT"

export CORES="${CORES:-1}"
export LATENCY_WAIT="${LATENCY_WAIT:-60}"
export CLASSIFICATION_PYTHON="${CLASSIFICATION_PYTHON:-/home/wenhai/miniconda3/envs/dadec_eval/bin/python}"

/home/work/wenhai/bin/snakemake \
  -s benchmark/scripts/classification/Snakefile \
  --configfile benchmark/config/classification/30strains_legacy.yaml \
  --config coverage=all classification_python="$CLASSIFICATION_PYTHON" \
  --cores "$CORES" \
  --latency-wait "$LATENCY_WAIT" \
  "$@"
