#!/bin/bash
set -euo pipefail
if "$@"; then
  cmux trigger-flash --surface "${CMUX_SURFACE_ID:-}"
  cmux set-status tests "PASS" --color "#10b981"
else
  cmux set-status tests "FAIL" --color "#ef4444"
  cmux notify --title "Tests failed" --body "Check the surface"
  exit 1
fi
