#!/usr/bin/env bash
set -euo pipefail

SOURCE=${1:-/home/yczhang/zyc/final_result/zymo/data/long_reads.fa}
OUTPUT_DIR=${2:-/home/work/wenhai/dadec/data/zymo}
SEQKIT_BIN=${SEQKIT_BIN:-/home/work/wenhai/bin/seqkit}
SEED=${SEED:-11}

if [[ ! -r "$SOURCE" ]]; then
    echo "ERROR: source FASTA is not readable: $SOURCE" >&2
    exit 1
fi

if [[ ! -x "$SEQKIT_BIN" ]]; then
    if command -v seqkit >/dev/null 2>&1; then
        SEQKIT_BIN=$(command -v seqkit)
    else
        echo "ERROR: seqkit not found. Set SEQKIT_BIN=/path/to/seqkit" >&2
        exit 1
    fi
fi

mkdir -p "$OUTPUT_DIR"

labels=(5 10 20 30 40)
fractions=(0.05 0.10 0.20 0.30 0.40)
outputs=()
current_tmp=""

cleanup_tmp() {
    if [[ -n "$current_tmp" && -e "$current_tmp" ]]; then
        rm -f -- "$current_tmp"
    fi
}
trap cleanup_tmp EXIT INT TERM

log() {
    printf '[%(%F %T)T] %s\n' -1 "$*"
}

log "source: $SOURCE"
log "output_dir: $OUTPUT_DIR"
log "seqkit: $("$SEQKIT_BIN" version)"
log "seed: $SEED"

for idx in "${!labels[@]}"; do
    label=${labels[$idx]}
    fraction=${fractions[$idx]}
    output="$OUTPUT_DIR/long_reads_${label}.fa"
    outputs+=("$output")

    if [[ -s "$output" ]]; then
        log "skip existing non-empty file: $output"
        continue
    fi

    current_tmp="$OUTPUT_DIR/.long_reads_${label}.fa.tmp.$$"
    log "sampling ${fraction} -> $output"
    "$SEQKIT_BIN" sample -s "$SEED" -p "$fraction" "$SOURCE" -o "$current_tmp"
    [[ -s "$current_tmp" ]]
    mv "$current_tmp" "$output"
    current_tmp=""
done

manifest_tmp="$OUTPUT_DIR/.sampling_manifest.tsv.tmp.$$"
{
    printf 'sample\tsource\toutput\tfraction\tseed\tseqkit_version\n'
    seqkit_version=$("$SEQKIT_BIN" version)
    for idx in "${!labels[@]}"; do
        label=${labels[$idx]}
        fraction=${fractions[$idx]}
        printf 'long_reads_%s\t%s\t%s/long_reads_%s.fa\t%s\t%s\t%s\n' \
            "$label" "$SOURCE" "$OUTPUT_DIR" "$label" "$fraction" "$SEED" "$seqkit_version"
    done
} > "$manifest_tmp"
mv "$manifest_tmp" "$OUTPUT_DIR/sampling_manifest.tsv"

stats_tmp="$OUTPUT_DIR/.sampling_stats.tsv.tmp.$$"
"$SEQKIT_BIN" stats -a -T "${outputs[@]}" > "$stats_tmp"
mv "$stats_tmp" "$OUTPUT_DIR/sampling_stats.tsv"

log "wrote manifest: $OUTPUT_DIR/sampling_manifest.tsv"
log "wrote stats: $OUTPUT_DIR/sampling_stats.tsv"
