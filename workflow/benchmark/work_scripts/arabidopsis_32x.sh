#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$ROOT"

export DATASET_CONFIG="${DATASET_CONFIG:-$ROOT/benchmark/config/datasets/arabidopsis.yaml}"
export CORES="${CORES:-64}"

tools=(dadec)
tools=(dadec lordec l_hero fmlrc f_hero ratatosk r_hero colormap proovread)
for tool in "${tools[@]}"; do
  config="benchmark/config/runs/arabidopsis/32x_${tool}.yaml"

  echo "======================================"
  echo "Running tool: ${tool}"
  echo "Config: ${config}"
  echo "======================================"

  "$ROOT/benchmark/run_one.sh" \
    "$config" \
    --latency-wait "${LATENCY_WAIT:-60}" \
    "$@"
done

python benchmark/scripts/collect_run_summaries.py \
  --runs-root benchmark/runs \
  --run-glob 'arabidopsis_32x*' \
  --output-all benchmark/results/arabidopsis_32x_all_parameter_runs.tsv \
  --output-best benchmark/results/arabidopsis_32x_best_parameter_runs.tsv