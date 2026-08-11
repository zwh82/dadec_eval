#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
exec python3 "$ROOT/benchmark/work_scripts/final_collect_res/drosophila_43x/collect_assembly_results.py"
