#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$ROOT"

export DATASET_CONFIG="${DATASET_CONFIG:-$ROOT/benchmark/config/datasets/100strains_legacy.yaml}"
export CORES="${CORES:-64}"

tools=(dadec lordec l_hero fmlrc f_hero ratatosk r_hero colormap proovread)
tools=(colormap proovread)

# The historical CoLoRMap FASTA contains 496 NUL bytes.  MetaQUAST rejects
# those bytes before evaluation, so use an auditable copy with only those
# unknown bytes represented as N.  The original file is never modified.
COLORMAP_SOURCE="/home/yczhang/zyc/final_result/100strains/100_cor/colormap_sp.fa"
COLORMAP_NORMALIZED="$ROOT/benchmark/runs/100strains_legacy_30x/100strains_legacy_30x_colormap_original/tmp/colormap_sp.nul_to_N.fa"

prepare_colormap_config() {
  local original_config="$1"
  local normalized_config
  if [[ ! -s "$COLORMAP_SOURCE" ]]; then
    echo "Missing CoLoRMap FASTA: $COLORMAP_SOURCE" >&2
    return 1
  fi
  if [[ ! -s "$COLORMAP_NORMALIZED" || "$COLORMAP_SOURCE" -nt "$COLORMAP_NORMALIZED" ]]; then
    mkdir -p "$(dirname "$COLORMAP_NORMALIZED")"
    echo "Creating normalized CoLoRMap FASTA: $COLORMAP_NORMALIZED" >&2
    LC_ALL=C tr '\000' 'N' < "$COLORMAP_SOURCE" > "$COLORMAP_NORMALIZED"
  fi
  normalized_config="$(mktemp "$ROOT/benchmark/work_scripts/100strains_legacy_colormap.XXXXXX.yaml")"
  sed "s|$COLORMAP_SOURCE|$COLORMAP_NORMALIZED|g" "$original_config" > "$normalized_config"
  printf '%s\n' "$normalized_config"
}

for tool in "${tools[@]}"; do
  config="benchmark/config/runs/100strains_legacy/30x_${tool}.yaml"
  temporary_config=""
  if [[ "$tool" == "colormap" ]]; then
    temporary_config="$(prepare_colormap_config "$config")"
    config="$temporary_config"
  fi

  echo "======================================"
  echo "Running tool: ${tool}"
  echo "Config: ${config}"
  echo "======================================"

  "$ROOT/benchmark/run_one.sh" \
    "$config" \
    --latency-wait "${LATENCY_WAIT:-60}" \
    --rerun-triggers mtime \
    --consider-ancient metaquast_corrected=reads,reference \
    "$@"

  if [[ -n "$temporary_config" ]]; then
    rm -f "$temporary_config"
  fi
done
