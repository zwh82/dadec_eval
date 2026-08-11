#!/usr/bin/env bash
set -euo pipefail

WORK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$WORK_DIR/../../.." && pwd)"
SNAKEMAKE="/home/work/wenhai/bin/snakemake"
CONFIG="$ROOT/benchmark/config/runs/drosophila/assembly/config.yaml"
SNAKEFILE="$ROOT/benchmark/assembly/Snakefile"
OUTPUT_ROOT="$ROOT/benchmark/runs/drosophila_43x/assembly"

for path in "$SNAKEMAKE" "$CONFIG" "$SNAKEFILE"; do
  if [[ ! -e "$path" ]]; then
    echo "Missing required path: $path" >&2
    exit 2
  fi
done

mkdir -p "$OUTPUT_ROOT"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-$ROOT/.snakemake-cache}"
mkdir -p "$XDG_CACHE_HOME"

exec "$SNAKEMAKE" \
  --snakefile "$SNAKEFILE" \
  --directory "$WORK_DIR" \
  --configfile "$CONFIG" \
  --config "config_path=$CONFIG" \
  --cores 64 \
  --nolock \
  --rerun-triggers mtime \
  "$@"
