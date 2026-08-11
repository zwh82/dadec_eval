#!/usr/bin/env bash
set -euo pipefail

WORK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$WORK_DIR/../../.." && pwd)"

exec /home/wenhai/miniconda3/envs/dadec_eval/bin/python \
  "$ROOT/benchmark/scripts/assembly_pipeline.py" verify \
  --config "$ROOT/benchmark/config/runs/drosophila/assembly/config.yaml"
