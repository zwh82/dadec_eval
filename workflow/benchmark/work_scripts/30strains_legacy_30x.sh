#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$ROOT"

export DATASET_CONFIG="${DATASET_CONFIG:-$ROOT/benchmark/config/datasets/30strains_legacy.yaml}"
export CORES="${CORES:-64}"

tools=(dadec)
tools=(dadec lordec fmlrc ratatosk l_hero f_hero r_hero colormap proovread)
cov=30
for tool in "${tools[@]}"; do
  config="benchmark/config/runs/30strains_legacy/${cov}x_${tool}.yaml"

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
  --run-glob "30strains_legacy_${cov}x*" \
  --output-all benchmark/results/30strains_legacy_${cov}x_all_parameter_runs.tsv \
  --output-best benchmark/results/30strains_legacy_${cov}x_best_parameter_runs.tsv

