#!/usr/bin/env bash
# Run the Zymo 10pct benchmark configurations other than DADEC, VeChat, and
# DeChat.  Those three methods are launched by their dedicated scripts.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$ROOT"

export DATASET_CONFIG="${DATASET_CONFIG:-$ROOT/benchmark/config/datasets/zymo.yaml}"
export CORES="${CORES:-64}"
# Do not schedule the default 0.99 MetaQUAST variant.  The supplied Zymo
# reports are also imported exclusively as the 0.9999 variant.
export AMBIGUITY_SCORES="0.9999"

coverage="10pct"
tools=(colormap f_hero fmlrc l_hero lordec proovread r_hero ratatosk)
tools=(colormap)
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

python benchmark/scripts/collect_run_summaries.py \
  --runs-root benchmark/runs \
  --dataset zymo \
  --long-coverage 10pct \
  --output-all benchmark/results/zymo_10pct_other_tools_all_parameter_runs.tsv \
  --output-best benchmark/results/zymo_10pct_other_tools_best_parameter_runs.tsv
