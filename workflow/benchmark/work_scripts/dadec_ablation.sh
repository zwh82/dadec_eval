#!/usr/bin/env bash
# Driver for the DADEC three-module (stage 1/2/3) ablation study.
#
# Calls the DADEC binary with --stages to run a given subset of stages, then
# evaluates the result with QUAST, reusing the prepared inputs/reference left
# behind by a completed baseline run. All parameters, coverage, stage list,
# conda envs and input paths can be overridden via environment variables so
# that multiple parameter combinations can be swept. The output directory and
# summary-table names encode the dataset, coverage, parameter signature and
# stage combination, so different runs never overwrite each other.
#
# Examples:
#   bash benchmark/work_scripts/dadec_ablation.sh current          # current version
#   bash benchmark/work_scripts/dadec_ablation.sh dev              # development version
#   bash benchmark/work_scripts/dadec_ablation.sh dev fix1         # dev, separate suffixed output
#   STAGES_LIST="2" bash benchmark/work_scripts/dadec_ablation.sh current # smoke test
#   AMBIGUITY_SCORES="0.99,0.9999" bash benchmark/work_scripts/dadec_ablation.sh current
#   COVERAGE=20x K1=31 K2=31 SPLIT=1 THRESHOLD=0.08 ABUND1=2 ABUND2=1 \
#     SHORT=/path/to/short_20x.fa bash benchmark/work_scripts/dadec_ablation.sh
set -euo pipefail

VARIANT="${1:-}"
if [[ "$VARIANT" != "current" && "$VARIANT" != "dev" ]]; then
  echo "Usage: bash ${BASH_SOURCE[0]} {current|dev} [output-suffix]" >&2
  exit 2
fi
RUN_SUFFIX="${2:-}"
if [[ -n "$RUN_SUFFIX" ]]; then
  if [[ ! "$RUN_SUFFIX" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]]; then
    echo "ERROR: invalid output suffix" >&2
    exit 2
  fi
  RUN_SUFFIX="_${RUN_SUFFIX}"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$ROOT"

# ---- Overridable parameters ----
: "${DATASET:=arabidopsis}"
: "${COVERAGE:=32x}"
: "${K1:=39}"
: "${K2:=39}"
: "${SPLIT:=4}"
: "${THRESHOLD:=0.1}"
: "${ABUND1:=3}"
: "${ABUND2:=2}"
: "${THREADS:=64}"
: "${QUAST_THREADS:=32}"
: "${FORCE_RERUN:=0}"
: "${STAGES_LIST:=1 2 3 1,2 1,3 2,3}"
: "${DEV_STAGES_LIST:=${STAGES_LIST} 1,2,3}"
: "${DADEC_ENV:=DADEC}"
: "${QUAST_ENV:=dadec_eval}"
# Ambiguity is kept as a backwards-compatible single-score alias.  For
# MetaQUAST, AMBIGUITY_SCORES accepts a comma- or space-separated list.
: "${Ambiguity:=0.99}"
: "${AMBIGUITY_SCORES:=${Ambiguity}}"
: "${QUAST_CLEANUP_MIB:=100}"
: "${RUN_GROUP:=${DATASET}_${COVERAGE}}"

# ---- Baseline run: reuse its prepared inputs and reference ----
if [[ "$DATASET" == "arabidopsis" ]]; then
  : "${BASELINE_RUN:=$ROOT/benchmark/runs/$RUN_GROUP/arabidopsis_32x_dadec_k39_k39_s4_a3_a2_t0p1}"
  : "${EVAL_TOOL:=quast}"
else
  : "${BASELINE_RUN:=$ROOT/benchmark/runs/$RUN_GROUP/${DATASET}_${COVERAGE}_dadec_k${K1}_k${K2}_s${SPLIT}_a${ABUND1}_a${ABUND2}_t${THRESHOLD//./p}}"
  : "${EVAL_TOOL:=metaquast}"
fi
: "${SHORT:=$BASELINE_RUN/tmp/inputs/short_${COVERAGE}.fa}"
: "${LONG:=$BASELINE_RUN/tmp/inputs/long_44x.fa}"
: "${REF:=$BASELINE_RUN/tmp/reference/${DATASET}.fa}"
# Full 1,2,3 baseline QUAST report and resource file (used as the "1,2,3" column)
# Leave BASELINE_REPORT empty by default so it can be resolved per ambiguity
# score below.  An explicit value still overrides that resolution.
: "${BASELINE_REPORT:=}"
: "${BASELINE_RESOURCES:=$BASELINE_RUN/benchmark/short_${COVERAGE}/dadec/resources.time.txt}"

# ---- Tool paths (match benchmark/config/common.yaml) ----
: "${CONDA:=/home/wenhai/miniconda3/bin/conda}"
: "${DADEC_CURRENT:=/home/work/wenhai/wh-github/DADEC/DADEC}"
: "${DADEC_DEV:=/home/work/wenhai/wh-github/DADEC/DADEC_DEV/DADEC_dev}"
: "${QUAST:=/home/yczhang/zyc/tools/quast/quast.py}"
: "${METAQUAST:=/home/yczhang/zyc/tools/quast/metaquast.py}"
: "${TIME_BIN:=/usr/bin/time}"
: "${SEQKIT:=/home/work/wenhai/bin/seqkit}"

# ---- Parameter signature and output directory (encode params + coverage) ----
SIG="k${K1}_k${K2}_s${SPLIT}_a${ABUND1}_a${ABUND2}_t${THRESHOLD//./p}"
# Keep all stage-ablation runs beneath a dedicated per-dataset directory.
OUT_PREFIX="$ROOT/benchmark/runs/$RUN_GROUP/dadec_ablation/${DATASET}_${COVERAGE}_dadec_ablation_${SIG}"
SUMMARY_ROOT="$ROOT/benchmark/results/$RUN_GROUP"

evaluation_dir_for_score() {
  local score="$1"
  if [[ "$EVAL_TOOL" == "quast" || "$score" == "0.99" ]]; then
    printf 'quast\n'
  elif [[ "$score" == "0.9999" ]]; then
    printf 'quast.ambiguity9999\n'
  else
    local score_tag="${score#0.}"
    score_tag="${score_tag//./}"
    printf 'quast.ambiguity%s\n' "$score_tag"
  fi
}

summary_suffix_for_score() {
  local score="$1"
  if [[ "$EVAL_TOOL" == "quast" || "$score" == "0.99" ]]; then
    return
  fi
  local score_tag="${score#0.}"
  score_tag="${score_tag//./}"
  printf '_ambiguity%s' "$score_tag"
}

baseline_report_for_score() {
  local score="$1"
  if [[ -n "$BASELINE_REPORT" ]]; then
    printf '%s\n' "$BASELINE_REPORT"
    return
  fi
  if [[ "$EVAL_TOOL" == "quast" ]]; then
    printf '%s\n' "$BASELINE_RUN/output/short_${COVERAGE}/dadec/quast/report.tsv"
    return
  fi
  local eval_dir="metaquast"
  [[ "$score" == "0.9999" ]] && eval_dir="metaquast.ambiguity9999"
  printf '%s\n' "$BASELINE_RUN/output/short_${COVERAGE}/dadec/$eval_dir/combined_reference/report.tsv"
}

is_fastq_path() {
  local path="${1,,}"
  [[ "$path" == *.fastq || "$path" == *.fq || \
     "$path" == *.fastq.gz || "$path" == *.fq.gz ]]
}

long_input_for_stages() {
  local stages="$1"
  local work="$2"

  # Stage 1 normally emits unwrapped FASTA for stage 2.  When an ablation
  # starts at stage 2, reproduce that format: the stage-2 reader otherwise
  # treats each physical FASTA line as a complete read.
  if [[ "$stages" != "2" && "$stages" != "2,3" ]]; then
    printf '%s\n' "$LONG"
    return
  fi

  if [[ ! -x "$SEQKIT" ]]; then
    echo "ERROR: seqkit missing or not executable: $SEQKIT" >&2
    return 1
  fi

  local converted="$work/long_input.fa"
  local temporary="$converted.tmp.$$"
  if is_fastq_path "$LONG"; then
    echo "Converting stage-${stages} FASTQ input to single-line FASTA: $converted" >&2
    "$SEQKIT" fq2fa -w 0 "$LONG" -o "$temporary" >&2
  else
    echo "Normalizing stage-${stages} FASTA input to one line per read: $converted" >&2
    "$SEQKIT" seq -w 0 "$LONG" -o "$temporary" >&2
  fi
  if [[ ! -s "$temporary" ]]; then
    echo "ERROR: seqkit produced no stage-${stages} input: $temporary" >&2
    return 1
  fi
  mv "$temporary" "$converted"
  printf '%s\n' "$converted"
}

write_or_check_run_metadata() {
  local out_root="$1"
  local variant="$2"
  local binary="$3"
  local stages_list="$4"
  local metadata="$out_root/run_metadata.txt"
  local binary_sha256 existing_sha256 temporary
  binary_sha256="$(sha256sum "$binary" | awk '{print $1}')"

  if [[ -f "$metadata" ]]; then
    existing_sha256="$(sed -n 's/^binary_sha256=//p' "$metadata" | head -n 1)"
    if [[ -n "$existing_sha256" && "$existing_sha256" != "$binary_sha256" ]]; then
      echo "ERROR: $out_root was started with a different DADEC binary." >&2
      echo "       Use a new output suffix instead of mixing binaries in one run." >&2
      exit 1
    fi
    return
  fi

  # Do not assign a new binary identity to a pre-existing legacy run whose
  # corrected outputs were made before metadata capture was introduced.
  if compgen -G "$out_root/stage_*/corrected.fa" > /dev/null; then
    echo "WARNING: legacy output has no run_metadata.txt: $out_root" >&2
    echo "         Use a new suffix for a reproducible development-binary run." >&2
    return
  fi

  temporary="$metadata.tmp"
  {
    printf 'variant=%s\n' "$variant"
    printf 'binary=%s\n' "$binary"
    printf 'binary_sha256=%s\n' "$binary_sha256"
    printf 'dataset=%s\n' "$DATASET"
    printf 'coverage=%s\n' "$COVERAGE"
    printf 'run_group=%s\n' "$RUN_GROUP"
    printf 'parameter_signature=%s\n' "$SIG"
    printf 'stages=%s\n' "$stages_list"
    printf 'ambiguity_scores=%s\n' "${AMBIGUITY_VALUES[*]}"
    printf 'short=%s\n' "$SHORT"
    printf 'long=%s\n' "$LONG"
    printf 'reference=%s\n' "$REF"
    printf 'created_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  } > "$temporary"
  mv "$temporary" "$metadata"
}

if [[ "$EVAL_TOOL" == "metaquast" ]]; then
  read -r -a AMBIGUITY_VALUES <<< "${AMBIGUITY_SCORES//,/ }"
  if [[ "${#AMBIGUITY_VALUES[@]}" -eq 0 ]]; then
    echo "ERROR: AMBIGUITY_SCORES must contain at least one score" >&2
    exit 2
  fi
else
  AMBIGUITY_VALUES=("0.99")
fi

echo "======================================"
echo "DADEC ablation study (${VARIANT})"
echo "  dataset=${DATASET}  coverage=${COVERAGE}"
echo "  params : k=${K1} K=${K2} S=${SPLIT} r=${THRESHOLD} a=${ABUND1} A=${ABUND2}  (sig=${SIG})"
[[ "$EVAL_TOOL" == "metaquast" ]] && echo "  ambiguity scores: ${AMBIGUITY_VALUES[*]}"
if [[ "$VARIANT" == "current" ]]; then
  echo "  binary : ${DADEC_CURRENT}"
  echo "  stages : ${STAGES_LIST} (full run from baseline)"
  echo "  out    : ${OUT_PREFIX}${RUN_SUFFIX}"
else
  echo "  binary : ${DADEC_DEV}"
  echo "  stages : ${DEV_STAGES_LIST}"
  echo "  out    : ${OUT_PREFIX}_dev${RUN_SUFFIX}"
fi
echo "  short  : ${SHORT}"
echo "  long   : ${LONG}"
echo "  ref    : ${REF}"
echo "======================================"

for src in "$SHORT" "$LONG" "$REF"; do
  if [[ ! -s "$src" ]]; then
    echo "ERROR: input file missing or empty: $src" >&2
    exit 1
  fi
done

if [[ "$VARIANT" == "current" ]]; then
  SELECTED_BINARY="$DADEC_CURRENT"
  SELECTED_STAGES="$STAGES_LIST"
else
  SELECTED_BINARY="$DADEC_DEV"
  SELECTED_STAGES="$DEV_STAGES_LIST"
fi
if [[ ! -x "$SELECTED_BINARY" ]]; then
  echo "ERROR: DADEC binary missing or not executable: $SELECTED_BINARY" >&2
  exit 1
fi

run_variant() {
  local variant="$1"
  local binary="$2"
  local stages_list="$3"
  local out_root="${OUT_PREFIX}${RUN_SUFFIX}"
  local summary_stem="${DATASET}_${COVERAGE}_dadec_ablation_${SIG}${RUN_SUFFIX}"
  if [[ "$variant" == "dev" ]]; then
    out_root="${OUT_PREFIX}_dev${RUN_SUFFIX}"
    summary_stem="${DATASET}_${COVERAGE}_dadec_ablation_${SIG}_dev${RUN_SUFFIX}"
  fi

  mkdir -p "$out_root"
  write_or_check_run_metadata "$out_root" "$variant" "$binary" "$stages_list"
  echo ""
  echo "======================================"
  echo "Running DADEC variant: ${variant}"
  echo "  binary: ${binary}"
  echo "  out   : ${out_root}"
  echo "======================================"

  local STAGES tag work stage_long_input
  for STAGES in $stages_list; do
    tag="${STAGES//,/_}"
    work="$out_root/stage_${tag}"
    mkdir -p "$work"

    echo ""
    echo "--------------------------------------"
    echo "Running stages: ${STAGES}  ->  ${work}"
    echo "--------------------------------------"

    if [[ "$FORCE_RERUN" == "1" || ! -s "$work/corrected.fa" ]]; then
      stage_long_input="$(long_input_for_stages "$STAGES" "$work")"
      # DADEC creates a temporary tmp/ in the current working directory, so cd into
      # each per-stage work dir to keep concurrent-safe, isolated scratch space.
      (
        cd "$work"
        "$CONDA" run --no-capture-output -n "$DADEC_ENV" \
          "$TIME_BIN" -v -o "$work/resources.time.txt" \
          "$binary" -s "$SHORT" -l "$stage_long_input" -o "$work/corrected.fa" \
          -t "$THREADS" -S "$SPLIT" -r "$THRESHOLD" -a "$ABUND1" -A "$ABUND2" \
          -k "$K1" -K "$K2" --stages "$STAGES"
      )
    else
      echo "Skipping DADEC stages=${STAGES}: existing $work/corrected.fa"
    fi

    if [[ ! -s "$work/corrected.fa" ]]; then
      echo "ERROR: stages=${STAGES} produced no corrected.fa" >&2
      exit 1
    fi

    local score eval_dir report
    for score in "${AMBIGUITY_VALUES[@]}"; do
      eval_dir="$(evaluation_dir_for_score "$score")"
      report="$work/$eval_dir/report.tsv"
      [[ "$EVAL_TOOL" == "metaquast" ]] && report="$work/$eval_dir/combined_reference/report.tsv"
      if [[ "$FORCE_RERUN" == "1" || ! -s "$report" ]]; then
        echo "${EVAL_TOOL}: evaluating stages=${STAGES} ambiguity=${score} -> ${eval_dir}"
        if [[ "$EVAL_TOOL" == "metaquast" ]]; then
          "$CONDA" run --no-capture-output -n "$QUAST_ENV" \
            "$METAQUAST" -r "$REF" -t "$QUAST_THREADS" --min-contig 500 --ambiguity-score "$score" \
            --no-html --no-icarus "$work/corrected.fa" -o "$work/$eval_dir"
        else
          "$CONDA" run --no-capture-output -n "$QUAST_ENV" \
            "$QUAST" -r "$REF" -t "$QUAST_THREADS" --min-contig 500 \
            --no-html --no-icarus "$work/corrected.fa" -o "$work/$eval_dir"
        fi
      else
        echo "Skipping ${EVAL_TOOL} stages=${STAGES} ambiguity=${score}: existing $report"
      fi
      if [[ ! -s "$report" ]]; then
        echo "ERROR: ${EVAL_TOOL} stages=${STAGES} produced no report: $report" >&2
        exit 1
      fi
      "$CONDA" run --no-capture-output -n "$QUAST_ENV" python \
        "$ROOT/benchmark/scripts/compact_quast.py" \
        --root "$work/$eval_dir" --threshold-mib "$QUAST_CLEANUP_MIB" --apply \
        --manifest "$work/$eval_dir/cleanup.json"
    done
  done

  local score eval_dir summary summary_suffix baseline_report
  for score in "${AMBIGUITY_VALUES[@]}"; do
    eval_dir="$(evaluation_dir_for_score "$score")"
    summary_suffix="$(summary_suffix_for_score "$score")"
    summary="$SUMMARY_ROOT/${summary_stem}${summary_suffix}.tsv"
    echo ""
    echo "Collecting ${variant} results (ambiguity=${score})"
    if [[ "$variant" == "current" ]]; then
      baseline_report="$(baseline_report_for_score "$score")"
      "$CONDA" run --no-capture-output -n "$QUAST_ENV" python "$SCRIPT_DIR/collect_ablation.py" \
        --out-root "$out_root" --evaluation-dir "$eval_dir" \
        --baseline-report "$baseline_report" \
        --baseline-resources "$BASELINE_RESOURCES" \
        --output "$summary"
    else
      "$CONDA" run --no-capture-output -n "$QUAST_ENV" python "$SCRIPT_DIR/collect_ablation.py" \
        --out-root "$out_root" --evaluation-dir "$eval_dir" \
        --output "$summary"
    fi
    echo "Summary (${variant}, ambiguity=${score}): ${summary}"
  done
}

run_variant "$VARIANT" "$SELECTED_BINARY" "$SELECTED_STAGES"

echo "Done. ${VARIANT} output is stored in its dedicated directory."
