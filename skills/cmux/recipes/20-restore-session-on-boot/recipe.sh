#!/bin/bash
# Add to ~/.zshrc or ~/.bashrc
if command -v cmux >/dev/null 2>&1 && [ -S "${CMUX_SOCKET_PATH:-/tmp/cmux.sock}" ]; then
  cmux restore-session 2>/dev/null || true
fi
