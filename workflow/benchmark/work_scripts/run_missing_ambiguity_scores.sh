#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/work/wenhai/dadec"
PYTHON="/home/wenhai/miniconda3/envs/dadec_eval/bin/python"

case "${1:-}" in
  --dry-run|--execute|--help|-h)
    exec "$PYTHON" "$ROOT/benchmark/work_scripts/run_missing_ambiguity_scores.py" "$@"
    ;;
esac

exec "$PYTHON" "$ROOT/benchmark/work_scripts/run_missing_ambiguity_scores.py" --execute "$@"
