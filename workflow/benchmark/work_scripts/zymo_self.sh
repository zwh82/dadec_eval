#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$ROOT"

export DATASET_CONFIG="${DATASET_CONFIG:-$ROOT/benchmark/config/datasets/zymo.yaml}"
export CORES="${CORES:-64}"

coverages=(5pct 10pct 20pct 30pct 40pct)
# coverages=(20pct)
tools=(vechat dechat)

for coverage in "${coverages[@]}"; do
  for tool in "${tools[@]}"; do
    config="benchmark/config/runs/zymo/${coverage}_${tool}.yaml"

    echo "======================================"
    echo "Running Zymo fraction: ${coverage}"
    echo "Running tool: ${tool}"
    echo "Config: ${config}"
    echo "======================================"

    "$ROOT/benchmark/run_one.sh" \
      "$config" \
      --latency-wait "${LATENCY_WAIT:-60}" \
      "$@"
  done
done

python benchmark/scripts/collect_run_summaries.py \
  --runs-root benchmark/runs \
  --dataset zymo \
  --run-glob 'zymo_*pct_*' \
  --output-all benchmark/results/zymo_self_all_parameter_runs.tsv \
  --output-best benchmark/results/zymo_self_best_parameter_runs.tsv
