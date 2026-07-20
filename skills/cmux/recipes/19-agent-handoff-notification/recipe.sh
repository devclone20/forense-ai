#!/bin/bash
# Usage: ./recipe.sh planner-surface executor-surface
set -euo pipefail
PLAN="$1"; EXEC="$2"
cmux trigger-flash --surface "$EXEC"
cmux notify --title "Handoff" --body "Planner finished — executor starts now"
cmux send-surface --surface "$EXEC" "# Planner output is in /tmp/plan.md — begin execution\n"
