#!/bin/bash
# Usage: ./recipe.sh https://example.com "#submit"
set -euo pipefail
URL="$1"; SEL="$2"
SURF=$(cmux --json browser open "$URL" | jq -r '.result.surface_ref')
cmux browser "$SURF" wait --selector "$SEL" --timeout-ms 15000
cmux browser "$SURF" snapshot --interactive
# Look up ref for $SEL in the snapshot output, then:
# cmux browser "$SURF" click eN
