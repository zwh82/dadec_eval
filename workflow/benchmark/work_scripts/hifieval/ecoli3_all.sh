#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
CONDA="${CONDA:-/home/wenhai/miniconda3/bin/conda}"
CONDA_ENV="${CONDA_ENV:-dadec_eval}"
all_methods=(dadec fmlrc f_hero ratatosk r_hero lordec l_hero colormap proovread)

selection="${METHODS:-${all_methods[*]}}"
selection="${selection//,/ }"
read -r -a methods <<< "$selection"
if [[ ${#methods[@]} -eq 0 ]]; then
    echo "METHODS selected no methods" >&2
    exit 2
fi

for method in "${methods[@]}"; do
    valid=0
    for candidate in "${all_methods[@]}"; do
        if [[ "$method" == "$candidate" ]]; then
            valid=1
            break
        fi
    done
    if [[ "$valid" -ne 1 ]]; then
        echo "Unknown ecoli3 Hifieval method: $method" >&2
        exit 2
    fi
done

args=("$@")
if [[ -n "${THREADS:-}" ]]; then
    args+=(--threads "$THREADS")
fi

preflight=0
for arg in "${args[@]}"; do
    if [[ "$arg" == "--preflight" ]]; then
        preflight=1
    fi
done

for method in "${methods[@]}"; do
    config="benchmark/config/runs/ecoli3/hifieval/20x_${method}_hifieval.yaml"
    echo "Running ecoli3 Hifieval: $method"
    "$SCRIPT_DIR/run_one.sh" "$config" "${args[@]}"
done

if [[ "$preflight" -eq 1 ]]; then
    exit 0
fi
if [[ ${#methods[@]} -ne ${#all_methods[@]} ]]; then
    echo "Subset complete; summary.tsv is collected only after all nine methods."
    exit 0
fi

"$CONDA" run --no-capture-output -n "$CONDA_ENV" \
    python "$ROOT/benchmark/scripts/collect_hifieval_results.py" \
    --config-dir "$ROOT/benchmark/config/runs/ecoli3/hifieval" \
    --config-pattern '20x_{method}_hifieval.yaml' \
    --output "$ROOT/benchmark/results/hifieval/ecoli3_20x/summary.tsv"
