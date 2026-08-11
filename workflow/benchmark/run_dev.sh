#!/usr/bin/env bash
# Run one existing DADEC job configuration with the development executable.
#
# Usage:
#   bash benchmark/run_dev.sh <version-tag> <job-config> [snakemake args...]
#
# Example:
#   bash benchmark/run_dev.sh 20260721_fix_a benchmark/config/runs/30strains/10x_dadec.yaml
#
# The tag is included in the run ID as ``dev_<tag>``. Consequently this never
# reuses or overwrites the corresponding production DADEC run.
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <version-tag> <job-config> [snakemake args...]" >&2
  exit 2
fi

TAG="$1"
JOB_CONFIG="$2"
shift 2
if [[ ! "$TAG" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]]; then
  echo "ERROR: invalid version tag: $TAG" >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export RUN_ID_SUFFIX="dev_${TAG}"
export COMMON_CONFIG_OVERLAY="$SCRIPT_DIR/config/overlays/dadec_dev.yaml"

exec "$SCRIPT_DIR/run_one.sh" "$JOB_CONFIG" "$@"
