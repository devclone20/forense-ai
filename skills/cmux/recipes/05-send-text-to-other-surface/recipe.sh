#!/bin/bash
# Usage: ./recipe.sh surface:7 "npm run build"
set -euo pipefail
SURFACE="$1"; CMD="$2"
cmux send-surface --surface "$SURFACE" "$CMD\n"
