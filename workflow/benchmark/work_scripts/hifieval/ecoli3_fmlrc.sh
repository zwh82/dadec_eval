#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
config="benchmark/config/runs/ecoli3/hifieval/20x_fmlrc_hifieval.yaml"
args=("$@")
if [[ -n "${THREADS:-}" ]]; then
    args+=(--threads "$THREADS")
fi
exec "$SCRIPT_DIR/run_one.sh" "$config" "${args[@]}"
