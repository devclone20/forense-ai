#!/bin/bash
# Returns 0 if inside cmux, 1 otherwise.
SOCK="${CMUX_SOCKET_PATH:-/tmp/cmux.sock}"
[ -S "$SOCK" ] || { echo "Not inside cmux"; exit 1; }
[ -n "${CMUX_WORKSPACE_ID:-}" ] || { echo "No CMUX_WORKSPACE_ID"; exit 1; }
[ "$TERM_PROGRAM" = "ghostty" ] || { echo "Not a Ghostty/cmux terminal"; exit 1; }
echo "Inside cmux: workspace=$CMUX_WORKSPACE_ID surface=$CMUX_SURFACE_ID"
