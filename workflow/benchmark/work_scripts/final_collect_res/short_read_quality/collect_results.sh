#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PYTHON:-/home/wenhai/miniconda3/envs/dadec_eval/bin/python}"

[[ -x "$PYTHON" ]] || { echo "ERROR: Python interpreter is not executable: $PYTHON" >&2; exit 2; }
exec "$PYTHON" "$SCRIPT_DIR/collect_results.py" "$@"
