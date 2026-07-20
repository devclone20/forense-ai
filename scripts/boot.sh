#!/usr/bin/env bash
# inft-i01 — boot the agent with project resources TRUSTED.
# Pi silently ignores .pi/* (soul, skills, settings) in a non-interactive/untrusted
# project unless approved. `-a` (approve) grants trust for this run, so the soul and
# skills actually load. Pass any extra pi args through (e.g. -p "prompt").
set -euo pipefail
cd "$(dirname "$0")/.."

if ! command -v pi >/dev/null 2>&1; then
  echo "✗ 'pi' not found. Run: bash scripts/setup.sh   (or: npx @earendil-works/pi-coding-agent -a)"
  exit 1
fi

exec pi -a "$@"
