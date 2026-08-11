#!/usr/bin/env bash
set -euo pipefail

WORK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$WORK_DIR/workflow.pid"
LOG_FILE="$WORK_DIR/workflow.log"
UNIT="dadec-drosophila-assembly.service"

if systemctl --user is-active --quiet "$UNIT"; then
  echo "Assembly workflow service is already running: $UNIT" >&2
  exit 2
fi

systemctl --user reset-failed "$UNIT" 2>/dev/null || true
systemd-run --user \
  --unit "$UNIT" \
  --collect \
  --property "WorkingDirectory=$WORK_DIR" \
  --property "StandardOutput=append:$LOG_FILE" \
  --property "StandardError=append:$LOG_FILE" \
  "$WORK_DIR/run.sh" --printshellcmds "$@"

workflow_pid="$(systemctl --user show "$UNIT" --property MainPID --value)"
printf '%s\n' "$workflow_pid" > "$PID_FILE"
printf 'Started %s with PID %s\nLog: %s\n' "$UNIT" "$workflow_pid" "$LOG_FILE"
