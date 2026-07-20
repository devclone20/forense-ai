#!/bin/bash
set -euo pipefail
WS="${CMUX_WORKSPACE_ID:?run inside cmux}"
PANE=$(cmux list-panes --workspace "$WS" --json \
  | jq -r --arg me "$CMUX_SURFACE_ID" '.result.panes | map(select((.surfaces // []) | map(.surface_ref) | index($me) | not)) | .[0].pane_ref // empty')
if [ -z "$PANE" ]; then
  cmux new-pane --workspace "$WS" --type terminal --direction right --focus false
  PANE=$(cmux list-panes --workspace "$WS" --json | jq -r '.result.panes[-1].pane_ref')
fi
echo "Helper pane: $PANE"
