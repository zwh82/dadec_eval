#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$ROOT"

export DATASET_CONFIG="${DATASET_CONFIG:-$ROOT/benchmark/config/datasets/ecoli_error_tech.yaml}"
export CORES="${CORES:-64}"

tools=(dadec lordec fmlrc ratatosk colormap proovread f_hero r_hero l_hero)
technologies=(miseq nextseq novaseq hiseq)

for technology in "${technologies[@]}"; do
  for tool in "${tools[@]}"; do
    config="benchmark/config/runs/ecoli_error/${technology}_${tool}.yaml"

    echo "======================================"
    echo "Running technology: ${technology}"
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
  --run-glob 'ecoli_error*' \
  --output-all benchmark/results/ecoli_error_all_parameter_runs.tsv \
  --output-best benchmark/results/ecoli_error_best_parameter_runs.tsv
