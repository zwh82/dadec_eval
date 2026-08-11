#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/work/wenhai/dadec"
PYTHON="/home/wenhai/miniconda3/envs/dadec_eval/bin/python"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

exec "$PYTHON" "$ROOT/benchmark/work_scripts/run_missing_ambiguity_scores.py" \
  --manifest "$DIR/current_missing.tsv" \
  "$@"
