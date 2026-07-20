#!/bin/bash
set -euo pipefail
cmux list-workspaces --json | jq -c '.result.workspaces[]' | while read -r ws; do
  REF=$(echo "$ws" | jq -r '.workspace_ref')
  CWD=$(echo "$ws" | jq -r '.cwd // ""')
  [ -z "$CWD" ] && continue
  NAME=$(basename "$CWD")
  cmux rename-workspace --workspace "$REF" --name "$NAME"
  echo "$REF -> $NAME"
done
