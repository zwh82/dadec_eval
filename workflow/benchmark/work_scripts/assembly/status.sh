#!/usr/bin/env bash
set -euo pipefail

WORK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$WORK_DIR/../../.." && pwd)"
OUTPUT_ROOT="$ROOT/benchmark/runs/drosophila_43x/assembly"
PID_FILE="$WORK_DIR/workflow.pid"
LOG_FILE="$WORK_DIR/workflow.log"
UNIT="dadec-drosophila-assembly.service"

if systemctl --user is-active --quiet "$UNIT"; then
  printf 'Workflow service: %s (running)\n' "$UNIT"
elif systemctl --user is-failed --quiet "$UNIT"; then
  printf 'Workflow service: %s (failed)\n' "$UNIT"
else
  printf 'Workflow service: %s (not running)\n' "$UNIT"
fi

if [[ -s "$PID_FILE" ]]; then
  workflow_pid="$(<"$PID_FILE")"
  printf 'Workflow PID: %s\n' "$workflow_pid"
else
  printf 'Workflow PID: not recorded\n'
fi

printf 'Assemblies: '
find "$OUTPUT_ROOT" -mindepth 3 -maxdepth 3 -type f -name assembly.fa 2>/dev/null | wc -l
printf 'QUAST reports: '
find "$OUTPUT_ROOT" -mindepth 4 -maxdepth 4 -type f -path '*/quast/report.tsv' 2>/dev/null | wc -l
printf 'Active processes:\n'
systemctl --user status "$UNIT" --no-pager --lines=0 2>/dev/null || true

if [[ -f "$OUTPUT_ROOT/summary.tsv" ]]; then
  printf 'Summary: %s\n' "$OUTPUT_ROOT/summary.tsv"
fi

if [[ -f "$LOG_FILE" ]]; then
  printf 'Workflow log: %s\n' "$LOG_FILE"
fi
