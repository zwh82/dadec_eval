#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$ROOT"

export DATASET_CONFIG="${DATASET_CONFIG:-$ROOT/benchmark/config/datasets/mhc_ont.yaml}"
export CORES="${CORES:-64}"

tools=(dadec lordec l_hero fmlrc f_hero ratatosk r_hero colormap proovread)
# tools=(fmlrc dadec)
for tool in "${tools[@]}"; do
  config="benchmark/config/runs/mhc_ont/50x_${tool}.yaml"

  echo "======================================"
  echo "Running tool: ${tool}"
  echo "Config: ${config}"
  echo "======================================"

  "$ROOT/benchmark/run_one.sh" \
    "$config" \
    --latency-wait "${LATENCY_WAIT:-60}" \
    "$@"
done
