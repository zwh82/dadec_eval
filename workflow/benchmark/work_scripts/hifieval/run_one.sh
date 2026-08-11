#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
CONDA="${CONDA:-/home/wenhai/miniconda3/bin/conda}"
CONDA_ENV="${CONDA_ENV:-dadec_eval}"

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 CONFIG.yaml [--preflight] [--force] [--threads N]" >&2
    exit 2
fi

config="$1"
shift
if [[ "$config" != /* ]]; then
    config="$ROOT/$config"
fi

exec "$CONDA" run --no-capture-output -n "$CONDA_ENV" \
    python "$ROOT/benchmark/scripts/run_hifieval_eval.py" "$config" "$@"
