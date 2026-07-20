#!/bin/bash
# Usage: ./recipe.sh surface:7
set -euo pipefail
SURF="${1:?missing surface ref}"
SOCK="${CMUX_SOCKET_PATH:-/tmp/cmux.sock}"
echo '{"id":"r","method":"surface.read_text","params":{"surface_id":"'"$SURF"'","lines":40}}' \
  | nc -U "$SOCK" \
  | jq .
