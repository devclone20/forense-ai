#!/bin/bash
# Usage: ./recipe.sh https://example.com /tmp/shot.png
set -euo pipefail
URL="$1"; OUT="${2:-/tmp/cmux-shot.png}"
SURF=$(cmux --json browser open "$URL" | jq -r '.result.surface_ref')
cmux browser "$SURF" wait --load-state complete --timeout-ms 15000
cmux browser "$SURF" screenshot > "$OUT"
echo "Saved screenshot to $OUT"
