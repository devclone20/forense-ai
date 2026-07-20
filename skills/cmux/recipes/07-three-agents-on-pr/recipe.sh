#!/bin/bash
# Usage: ./recipe.sh <pr-url>
set -euo pipefail
WS="${CMUX_WORKSPACE_ID:?inside cmux}"
PR="$1"
gh pr diff "$PR" > /tmp/cmux-pr.diff
cmux new-pane --workspace "$WS" --type terminal --direction right --focus false
PANE=$(cmux list-panes --workspace "$WS" --json | jq -r '.result.panes[-1].pane_ref')
for role in code security tests; do
  cmux new-surface --pane "$PANE" --type terminal --focus false
done
SURFS=($(cmux list-pane-surfaces --pane "$PANE" --json | jq -r '.result.surfaces[-3:][].surface_ref'))
cmux send-surface --surface "${SURFS[0]}" "claude 'Review /tmp/cmux-pr.diff for correctness'\n"
cmux send-surface --surface "${SURFS[1]}" "claude 'Audit /tmp/cmux-pr.diff for security'\n"
cmux send-surface --surface "${SURFS[2]}" "claude 'Score test coverage of /tmp/cmux-pr.diff'\n"
cmux notify --title "PR Review" --body "3 agents reviewing $PR"
