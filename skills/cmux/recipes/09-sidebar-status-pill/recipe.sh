#!/bin/bash
# Usage: ./recipe.sh "key" "value" "#color"
set -euo pipefail
KEY="${1:-build}"; VAL="${2:-running}"; COLOR="${3:-#3b82f6}"
cmux set-status "$KEY" "$VAL" --color "$COLOR" --icon hammer
echo "Pinned: $KEY = $VAL"
echo "Clear with: cmux clear-status $KEY"
