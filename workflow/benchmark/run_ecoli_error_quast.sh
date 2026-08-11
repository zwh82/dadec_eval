#!/usr/bin/env bash

# Run all ecoli_error short-read correction jobs with single-reference QUAST.
# Jobs are intentionally run one after another so this script is safe to start
# manually on one node. Use CORES to control the threads for each job.
#
# Usage:
#   CORES=64 benchmark/run_ecoli_error_quast.sh
#   CORES=64 benchmark/run_ecoli_error_quast.sh -n --quiet  # dry-run all jobs

set -euo pipefail

ROOT="/home/work/wenhai/dadec"
RUN_ONE="$ROOT/benchmark/run_one.sh"
DATASET_CONFIG="${DATASET_CONFIG:-$ROOT/benchmark/config/datasets/ecoli_error_tech.yaml}"
RUN_CONFIG_DIR="$ROOT/benchmark/config/runs/ecoli_error"

if [[ ! -x "$RUN_ONE" ]]; then
    printf 'ERROR: missing executable: %s\n' "$RUN_ONE" >&2
    exit 1
fi
if [[ ! -f "$DATASET_CONFIG" ]]; then
    printf 'ERROR: missing dataset config: %s\n' "$DATASET_CONFIG" >&2
    exit 1
fi
if [[ ! -d "$RUN_CONFIG_DIR" ]]; then
    printf 'ERROR: missing run config directory: %s\n' "$RUN_CONFIG_DIR" >&2
    exit 1
fi

mapfile -t run_configs < <(find "$RUN_CONFIG_DIR" -maxdepth 1 -type f -name '*.yaml' -print | sort)
if (( ${#run_configs[@]} == 0 )); then
    printf 'ERROR: no run configs found in: %s\n' "$RUN_CONFIG_DIR" >&2
    exit 1
fi

for job_config in "${run_configs[@]}"; do
    printf '\n===== %s =====\n' "$(basename "$job_config")" >&2
    DATASET_CONFIG="$DATASET_CONFIG" \
        CORES="${CORES:-64}" \
        "$RUN_ONE" "$job_config" "$@"
done

printf '\nAll %d QUAST jobs completed.\n' "${#run_configs[@]}" >&2
