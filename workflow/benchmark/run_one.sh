#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 benchmark/config/<job>.yaml [snakemake args...]" >&2
  exit 2
fi

ROOT="/home/work/wenhai/dadec"
SNAKEMAKE="/home/work/wenhai/bin/snakemake"
DATASET_CONFIG="${DATASET_CONFIG:-$ROOT/benchmark/config/datasets/30strains.yaml}"
COMMON_CONFIG="${COMMON_CONFIG:-$ROOT/benchmark/config/common.yaml}"
COMMON_CONFIG_OVERLAY="${COMMON_CONFIG_OVERLAY:-}"
JOB_CONFIG="$1"
shift
if [[ "$JOB_CONFIG" != /* ]]; then
  JOB_CONFIG="$ROOT/$JOB_CONFIG"
fi
if [[ "$DATASET_CONFIG" != /* ]]; then
  DATASET_CONFIG="$ROOT/$DATASET_CONFIG"
fi
if [[ "$COMMON_CONFIG" != /* ]]; then
  COMMON_CONFIG="$ROOT/$COMMON_CONFIG"
fi
if [[ -n "$COMMON_CONFIG_OVERLAY" && "$COMMON_CONFIG_OVERLAY" != /* ]]; then
  COMMON_CONFIG_OVERLAY="$ROOT/$COMMON_CONFIG_OVERLAY"
fi
for config_path in "$COMMON_CONFIG" "$JOB_CONFIG" "$DATASET_CONFIG"; do
  if [[ ! -f "$config_path" ]]; then
    echo "Missing config file: $config_path" >&2
    exit 2
  fi
done
if [[ -n "$COMMON_CONFIG_OVERLAY" && ! -f "$COMMON_CONFIG_OVERLAY" ]]; then
  echo "Missing common-config overlay: $COMMON_CONFIG_OVERLAY" >&2
  exit 2
fi

mapfile -t RUN_LAYOUT < <(
  /home/wenhai/miniconda3/envs/dadec_eval/bin/python - "$ROOT" "$JOB_CONFIG" "$DATASET_CONFIG" <<'PY'
import re
import sys
import os
from pathlib import Path

root = Path(sys.argv[1])
path = Path(sys.argv[2])
dataset_path = Path(sys.argv[3])
if not path.is_absolute():
    path = root / path
if not dataset_path.is_absolute():
    dataset_path = root / dataset_path
run = {}
values = {}
in_run = False
dataset_id = "dataset"
in_dataset = False
for raw in dataset_path.read_text().splitlines():
    line = raw.split("#", 1)[0].rstrip()
    if not line.strip():
        continue
    if not raw.startswith((" ", "\t")):
        key = line.split(":", 1)[0].strip()
        in_dataset = key == "dataset"
        continue
    if in_dataset and ":" in line:
        key, value = line.split(":", 1)
        if key.strip() == "id" and value.strip():
            dataset_id = value.strip().strip("'\"")
            break
for raw in path.read_text().splitlines():
    line = raw.split("#", 1)[0].rstrip()
    if not line.strip():
        continue
    if not raw.startswith((" ", "\t")):
        key, _, value = line.partition(":")
        key = key.strip()
        in_run = key == "run"
        value = value.strip()
        if in_run and value.startswith("{") and value.endswith("}"):
            for part in value.strip("{}").split(","):
                item_key, _, item_value = part.partition(":")
                if item_key.strip():
                    run[item_key.strip()] = item_value.strip().strip("'\"")
        elif not in_run and value:
            values[key] = value.strip("'\"")
        continue
    if in_run and ":" in line:
        key, value = line.split(":", 1)
        run[key.strip()] = value.strip().strip("'\"")
    elif ":" in line:
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip().strip("'\"")
run_id = run.get("id")
if not run_id:
    coverage = run.get("coverage", "coverage")
    method = run.get("method", "method")
    parameter_set = run.get("parameter_set", "study")
    run_id = f"{dataset_id}_{coverage}_{method}_{parameter_set}"
run_id_suffix = os.environ.get("RUN_ID_SUFFIX", "").strip()
if run_id_suffix:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", run_id_suffix):
        raise SystemExit(f"Invalid RUN_ID_SUFFIX: {run_id_suffix!r}")
    run_id = f"{run_id}_{run_id_suffix}"
coverage = run.get("coverage", "coverage")
method = run.get("method", "method")
def compact(value):
    return str(value).replace(".", "p")

def has(*fields):
    return all(field in values and values[field] != "" for field in fields)

signature = ""
if method == "dadec" and has("dadec_k1", "dadec_k2", "dadec_split", "dadec_abundance1", "dadec_abundance2"):
    parts = [
        f"k{values['dadec_k1']}",
        f"k{values['dadec_k2']}",
        f"s{values['dadec_split']}",
        f"a{values['dadec_abundance1']}",
        f"a{values['dadec_abundance2']}",
    ]
    if values.get("dadec_threshold") not in (None, "", "0.08"):
        parts.append(f"t{compact(values['dadec_threshold'])}")
    signature = "_".join(parts)
elif method in {"fmlrc", "f_hero"} and has("fmlrc_k1", "fmlrc_k2"):
    parts = [f"k{values['fmlrc_k1']}", f"k{values['fmlrc_k2']}"]
    if method == "f_hero" and has("hero_split", "hero_iterations"):
        parts.extend([f"hs{values['hero_split']}", f"hi{values['hero_iterations']}"])
    signature = "_".join(parts)
elif method in {"ratatosk", "r_hero"} and has("ratatosk_k1", "ratatosk_k2"):
    parts = [f"k{values['ratatosk_k1']}", f"k{values['ratatosk_k2']}"]
    if method == "r_hero" and has("hero_split", "hero_iterations"):
        parts.extend([f"hs{values['hero_split']}", f"hi{values['hero_iterations']}"])
    signature = "_".join(parts)
elif method in {"lordec", "l_hero"} and has("lordec_k", "lordec_solid"):
    parts = [f"k{values['lordec_k']}", f"ls{values['lordec_solid']}"]
    if method == "l_hero" and has("hero_split", "hero_iterations"):
        parts.extend([f"hs{values['hero_split']}", f"hi{values['hero_iterations']}"])
    signature = "_".join(parts)
if signature:
    run_id = f"{run_id}_{signature}"
run_id = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(run_id)).strip("._-")
if not run_id:
    raise SystemExit("Empty run.id after sanitizing")
marker = f"_{method}"
match = re.search(rf"{re.escape(marker)}(?:_|$)", run_id)
if not match:
    raise SystemExit(f"Cannot derive data group from run id {run_id!r} and method {method!r}")
run_group = run_id[:match.start()]
if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", run_group):
    raise SystemExit(f"Invalid run group: {run_group!r}")
print(run_group)
print(run_id)
PY
)
if [[ ${#RUN_LAYOUT[@]} -ne 2 ]]; then
  echo "Failed to resolve run group and run id" >&2
  exit 2
fi
RUN_GROUP="${RUN_LAYOUT[0]}"
RUN_ID="${RUN_LAYOUT[1]}"

# Zymo run configs may optionally import an external MetaQUAST report.  Keep
# existing outputs stable when the workflow/config implementation changes;
# input and mtime changes still trigger the explicitly requested report copy.
DATASET_ID="$(
  awk '
    /^dataset:[[:space:]]*$/ { in_dataset=1; next }
    /^[^[:space:]]/ { in_dataset=0 }
    in_dataset && $1 == "id:" { print $2; exit }
  ' "$DATASET_CONFIG" | tr -d "\"'"
)"
RERUN_TRIGGER_ARGS=()
HAS_RERUN_TRIGGER=0
for argument in "$@"; do
  if [[ "$argument" == "--rerun-triggers" || "$argument" == --rerun-triggers=* ]]; then
    HAS_RERUN_TRIGGER=1
    break
  fi
done
if [[ "$DATASET_ID" == "zymo" && "$HAS_RERUN_TRIGGER" == "0" ]]; then
  RERUN_TRIGGER_ARGS+=(--rerun-triggers input mtime)
fi

RUN_DIR="$ROOT/benchmark/runs/$RUN_GROUP/$RUN_ID"
mkdir -p "$RUN_DIR"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-$ROOT/.snakemake-cache}"
mkdir -p "$XDG_CACHE_HOME"

cd "$RUN_DIR"
EXTRA_CONFIG=()
if [[ -n "${AMBIGUITY_SCORES:-}" ]]; then
  EXTRA_CONFIG+=(--config "ambiguity_scores=$AMBIGUITY_SCORES")
fi
if [[ -n "${RUN_ID_SUFFIX:-}" ]]; then
  EXTRA_CONFIG+=(--config "run_id_suffix=$RUN_ID_SUFFIX")
fi
CONFIG_FILES=("$COMMON_CONFIG")
if [[ -n "$COMMON_CONFIG_OVERLAY" ]]; then
  CONFIG_FILES+=("$COMMON_CONFIG_OVERLAY")
fi
exec "$SNAKEMAKE" \
  --snakefile "$ROOT/benchmark/Snakefile" \
  --directory "$RUN_DIR" \
  --configfile "${CONFIG_FILES[@]}" \
  "$DATASET_CONFIG" \
  "$JOB_CONFIG" \
  --nolock \
  --cores "${CORES:-64}" \
  "${EXTRA_CONFIG[@]}" \
  "${RERUN_TRIGGER_ARGS[@]}" \
  "$@"
