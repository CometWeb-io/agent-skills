#!/usr/bin/env bash
# Install canonical skills into supported local Agent Skills hosts.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
"$ROOT/scripts/install-cursor.sh"
"$ROOT/scripts/install-claude.sh"
"$ROOT/scripts/install-codex.sh"
"$ROOT/scripts/install-qwen.sh"
"$ROOT/scripts/install-qoder.sh"
"$ROOT/scripts/install-lingma.sh"
echo "OK: all local hosts installed from $ROOT"
