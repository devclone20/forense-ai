#!/bin/bash
# Usage: ./recipe.sh https://yoursite.com/contact "Jane" "jane@example.com"
set -euo pipefail
URL="$1"; NAME="$2"; EMAIL="$3"
SURF=$(cmux --json browser open "$URL" | jq -r '.result.surface_ref')
cmux browser "$SURF" wait --load-state complete --timeout-ms 15000
cmux browser "$SURF" snapshot --interactive
# Replace e1/e2/e3 with the refs from the snapshot above
cmux browser "$SURF" fill e1 "$NAME"
cmux browser "$SURF" fill e2 "$EMAIL"
cmux browser "$SURF" click e3
cmux browser "$SURF" wait --text "Thanks" --timeout-ms 10000
cmux browser "$SURF" snapshot --interactive
