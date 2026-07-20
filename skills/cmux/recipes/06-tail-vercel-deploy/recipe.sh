#!/bin/bash
set -euo pipefail
WS="${CMUX_WORKSPACE_ID:?inside cmux}"
cmux new-pane --workspace "$WS" --type terminal --direction right --focus false
PANE=$(cmux list-panes --workspace "$WS" --json | jq -r '.result.panes[-1].pane_ref')
cmux new-surface --pane "$PANE" --type terminal --focus false
SURF=$(cmux list-pane-surfaces --pane "$PANE" --json | jq -r '.result.surfaces[-1].surface_ref')
cmux set-status deploy "tailing" --icon "arrow.up.circle" --color "#3b82f6"
cmux send-surface --surface "$SURF" "vercel logs --follow\n"
