#!/usr/bin/env bash
# Collect one tagged development-DADEC series into its dataset result folder.
#
# Usage:
#   bash benchmark/work_scripts/collect_dadec_dev_results.sh <version-tag> <run-group>
#
# Example:
#   bash benchmark/work_scripts/collect_dadec_dev_results.sh 20260721_fix_a 30strains_10x
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 <version-tag> <run-group>" >&2
  exit 2
fi

TAG="$1"
RUN_GROUP="$2"
if [[ ! "$TAG" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]]; then
  echo "ERROR: invalid version tag: $TAG" >&2
  exit 2
fi
if [[ ! "$RUN_GROUP" =~ ^[a-z0-9][a-z0-9_-]*$ ]]; then
  echo "ERROR: invalid run group: $RUN_GROUP" >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
RESULT_DIR="$ROOT/benchmark/results/$RUN_GROUP"
LABEL="dadec_dev_${TAG}"

mkdir -p "$RESULT_DIR"
exec /home/wenhai/miniconda3/envs/dadec_eval/bin/python \
  "$ROOT/benchmark/scripts/collect_run_summaries.py" \
  --runs-root "$ROOT/benchmark/runs" \
  --run-glob "${RUN_GROUP}_dadec_dev_${TAG}*" \
  --method dadec \
  --output-all "$RESULT_DIR/${LABEL}_all_parameter_runs.tsv" \
  --output-best "$RESULT_DIR/${LABEL}_best_parameter_runs.tsv"
