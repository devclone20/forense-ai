#!/bin/bash
# Usage: ./recipe.sh <command> [args...]
set -euo pipefail
LOG=$(mktemp)
if ! "$@" 2>&1 | tee "$LOG"; then
  TAIL=$(tail -n 5 "$LOG" | tr '\n' ' | ')
  cmux notify --title "Build FAILED" --body "$TAIL"
  cmux trigger-flash --surface "${CMUX_SURFACE_ID:-}"
  exit 1
fi
cmux notify --title "Build OK" --body "Command finished successfully"
