#!/usr/bin/env bash
# Install into Cursor + Claude Code + Codex from this canonical private repo.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
"$ROOT/scripts/install-cursor.sh"
"$ROOT/scripts/install-claude.sh"
"$ROOT/scripts/install-codex.sh"
echo "OK: all hosts installed from $ROOT"
