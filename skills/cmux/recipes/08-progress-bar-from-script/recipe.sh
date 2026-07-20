#!/bin/bash
set -euo pipefail
TOTAL=${1:-100}
for i in $(seq 1 "$TOTAL"); do
  RATIO=$(awk "BEGIN { printf \"%.3f\", $i/$TOTAL }")
  cmux set-progress "$RATIO" --label "Processing $i/$TOTAL"
  sleep 0.1
done
cmux clear-progress
cmux notify --title "Done" --body "Batch complete: $TOTAL items"
