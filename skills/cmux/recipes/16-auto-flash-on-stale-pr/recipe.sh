#!/bin/bash
set -euo pipefail
cmux list-workspaces --json | jq -c '.result.workspaces[]' | while read -r ws; do
  REF=$(echo "$ws" | jq -r '.workspace_ref')
  PR=$(echo "$ws" | jq -r '.pr_url // ""')
  [ -z "$PR" ] && continue
  COMMENTS=$(gh pr view "$PR" --json comments -q '.comments | length' 2>/dev/null || echo 0)
  if [ "$COMMENTS" -gt 0 ]; then
    cmux trigger-flash --workspace "$REF"
  fi
done
