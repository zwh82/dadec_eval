#!/usr/bin/env bash
# Raw long-read baseline evaluation for every benchmark/config/datasets/*.yaml.
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
CONDA=/home/wenhai/miniconda3/bin/conda
THREADS=${QUAST_THREADS:-64}

cd "$ROOT"
exec "$CONDA" run --no-capture-output -n dadec_eval python \
  benchmark/scripts/evaluate_raw_long_reads.py --threads "$THREADS" "$@"
