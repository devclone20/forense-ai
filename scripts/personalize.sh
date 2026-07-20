#!/usr/bin/env bash
# inft-i01 — personalize a forged repo. Idempotent and non-destructive.
#
#   personalize.sh "Agent Name"     Set the marketplace name (won't clobber an
#                                   already-personalized name without --force).
#   personalize.sh --apply-owner    Fold .pi/owner.local.md into the LOCAL
#                                   .pi/APPEND_SYSTEM.md and untrack that file so
#                                   the owner profile is never committed.
#   Flags: --force  overwrite an existing name.
set -euo pipefail
cd "$(dirname "$0")/.."

PLACEHOLDER="iNFT i01"
MARKER="<!-- ─────────────────────────────────────────────────────────────────────────"
SENTINEL="<!-- OWNER-PROFILE-APPLIED -->"

say() { printf '%s\n' "$*"; }

apply_owner() {
  local prof=".pi/owner.local.md"
  local target=".pi/APPEND_SYSTEM.md"
  [ -f "$prof" ] || { say "✗ $prof not found. Write the owner profile there first (see owner/OWNER.example.md)."; exit 1; }

  if grep -qF "$SENTINEL" "$target" 2>/dev/null; then
    say "✓ Owner profile already applied — nothing to do (idempotent)."
  else
    { printf '\n%s\n\n## OWNER PROFILE\n\n' "$SENTINEL"; cat "$prof"; } >> "$target"
    say "✓ Owner profile folded into $target (local only)."
  fi

  # Untrack the personalized system prompt so PII is never committed/pushed.
  if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git rm --cached --quiet "$target" 2>/dev/null || true
    grep -qxF ".pi/APPEND_SYSTEM.md" .gitignore 2>/dev/null || printf '\n# personalized system prompt (contains owner profile)\n.pi/APPEND_SYSTEM.md\n' >> .gitignore
  fi

  # Safety check: owner files must be ignored.
  if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    for f in .pi/owner.local.md .pi/APPEND_SYSTEM.md; do
      git check-ignore -q "$f" && say "  ✓ $f is gitignored" || say "  ⚠ $f is NOT ignored — do not push until fixed"
    done
  fi
}

set_name() {
  local newname="$1" force="${2:-}"
  local current
  current="$(node -p "require('./identity.json').marketplace_name" 2>/dev/null || echo "")"

  if [ "$current" != "$PLACEHOLDER" ] && [ -n "$current" ] && [ "$force" != "--force" ]; then
    say "✓ Already personalized as \"$current\" (idempotent; pass --force to change)."
    return 0
  fi

  node -e '
    const fs=require("fs"), p="./identity.json";
    const j=JSON.parse(fs.readFileSync(p,"utf8"));
    j.marketplace_name=process.argv[1];
    delete j.marketplace_name_note;
    fs.writeFileSync(p, JSON.stringify(j,null,2)+"\n");
  ' "$newname"
  say "✓ identity.json marketplace_name → \"$newname\""

  # Reflect the name in the metadata template (name field only; leave <...> mint fields).
  node -e '
    const fs=require("fs"), p="./metadata/metadata.template.json";
    if(fs.existsSync(p)){const j=JSON.parse(fs.readFileSync(p,"utf8"));
      j.name=process.argv[1];
      fs.writeFileSync(p, JSON.stringify(j,null,2)+"\n");}
  ' "$newname" 2>/dev/null || true

  [ -x scripts/make-manifest.sh ] && bash scripts/make-manifest.sh >/dev/null && say "✓ manifest regenerated"
  say "  Your agent answers to \"$newname\", \"iNFT\", and \"Pi\"."
}

case "${1:-}" in
  ""|-h|--help) say "Usage: personalize.sh \"Agent Name\" [--force]  |  personalize.sh --apply-owner"; exit 0 ;;
  --apply-owner) apply_owner ;;
  *) set_name "$1" "${2:-}" ;;
esac
