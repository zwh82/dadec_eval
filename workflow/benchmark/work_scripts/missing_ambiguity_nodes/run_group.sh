#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 RUN_GROUP [--dry-run] [runner options...]" >&2
  exit 2
fi

RUN_GROUP="$1"
shift
ROOT="/home/work/wenhai/dadec"
PYTHON="/home/wenhai/miniconda3/envs/dadec_eval/bin/python"
RUNNER="$ROOT/benchmark/work_scripts/run_missing_ambiguity_scores.py"
MODE="--execute"

if [[ "${1:-}" == "--dry-run" || "${1:-}" == "--execute" ]]; then
  MODE="$1"
  shift
fi

exec "$PYTHON" "$RUNNER" "$MODE" \
  --run-glob "${RUN_GROUP}*" \
  --keep-going \
  "$@"
