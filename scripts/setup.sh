#!/usr/bin/env bash
# iclone (iCLONE iNFT monorepo) — Pi substrate setup. Installs the Pi coding agent +
# opensrc at PINNED versions, with --ignore-scripts for BOTH, and never uses sudo. Prints
# every command before it runs. Safe to re-run (installs are additive/idempotent).
# This only wires the INTERACTIVE Pi substrate; it does NOT touch the Python economy
# runtime in the existing app runtime.
set -euo pipefail
cd "$(dirname "$0")/.."

PI_VERSION="${PI_VERSION:-0.80.10}"
OPENSRC_VERSION="${OPENSRC_VERSION:-0.7.3}"
PI_PKG="@earendil-works/pi-coding-agent@${PI_VERSION}"
OPENSRC_PKG="opensrc@${OPENSRC_VERSION}"

say() { printf '%s\n' "$*"; }
run() { say "  \$ $*"; "$@"; }

say "── forense · Pi substrate setup ────────────────────────────────"

# ── Preflight ────────────────────────────────────────────────────
if ! command -v node >/dev/null 2>&1; then
  say "✗ Node.js (≥18) is required and was not found."
  case "$(uname -s)" in
    Darwin) say "  macOS:  brew install node" ;;
    Linux)  say "  Linux:  install nvm → https://github.com/nvm-sh/nvm , then: nvm install --lts" ;;
    *)      say "  Install Node from https://nodejs.org" ;;
  esac
  exit 1
fi
NODE_MAJOR="$(node -p 'process.versions.node.split(".")[0]')"
[ "$NODE_MAJOR" -ge 18 ] || { say "✗ Node ≥18 required (found $(node -v)). Upgrade Node."; exit 1; }
command -v git >/dev/null 2>&1 || { say "✗ git is required."; exit 1; }
say "  ✓ node $(node -v), npm $(npm -v), git present"

# ── Install substrate (pinned, no scripts, no sudo) ──────────────
say "→ Installing Pi coding agent + opensrc (pinned, --ignore-scripts, no sudo)…"
if npm install -g --ignore-scripts "$PI_PKG" "$OPENSRC_PKG" 2>/dev/null; then
  say "  ✓ installed globally: $PI_PKG , $OPENSRC_PKG"
  INSTALL_MODE=global
else
  say "  ! global install failed (likely EACCES — we will NOT sudo)."
  say "  → Falling back to a user-owned npm prefix (~/.npm-global)…"
  npm config set prefix "$HOME/.npm-global"
  run npm install -g --ignore-scripts "$PI_PKG" "$OPENSRC_PKG"
  case ":$PATH:" in
    *":$HOME/.npm-global/bin:"*) : ;;
    *) say "  ⚠ Add this to your shell profile so 'pi' is found:"
       say "      export PATH=\"\$HOME/.npm-global/bin:\$PATH\"" ;;
  esac
  INSTALL_MODE=user-prefix
fi
say "  (No global permission? You can also run Pi ad-hoc: npx $PI_PKG)"

# ── Verify wiring ────────────────────────────────────────────────
say "→ Verifying repo wiring…"
for f in .pi/settings.json .pi/APPEND_SYSTEM.md soul/neural_soul.md identity.json skills/cmux/SKILL.md AGENTS.md; do
  [ -f "$f" ] && say "  ✓ $f" || { say "  ✗ MISSING: $f"; exit 1; }
done
command -v pi      >/dev/null 2>&1 && say "  ✓ pi $(pi --version 2>/dev/null || echo installed) ($INSTALL_MODE)"
command -v opensrc >/dev/null 2>&1 && say "  ✓ opensrc installed"

NAME="$(node -p "require('./identity.json').marketplace_name" 2>/dev/null || echo 'Forense')"
say ""
say "── Substrate ready. Next:"
say "   1) Connect key:  run 'pi' then '/login' (you type the key, never the assistant)"
say "   2) Boot:         bash scripts/boot.sh        (= pi -a, trusts this project's soul+skills)"
say "   3) Terminal:     bash scripts/install-command.sh   (then type '$NAME' in the CLONE FRAME iT terminal)"
say "   Current name: \"$NAME\" — it also answers to \"iNFT\" and \"Pi\"."
