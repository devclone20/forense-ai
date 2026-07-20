#!/bin/bash
# Usage: ./recipe.sh user@host port "Name"
set -euo pipefail
HOST="$1"; PORT="${2:-22}"; NAME="${3:-remote}"
cmux ssh "$HOST" --port "$PORT" --name "$NAME" --no-focus
echo "Remote workspace opened: $NAME ($HOST)"
