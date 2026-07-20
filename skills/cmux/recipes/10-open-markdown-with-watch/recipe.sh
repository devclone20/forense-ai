#!/bin/bash
# Usage: ./recipe.sh path/to/plan.md
set -euo pipefail
FILE="${1:?missing path}"
cmux markdown open "$FILE" --direction right
