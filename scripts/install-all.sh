#!/usr/bin/env bash
# Install canonical skills into supported local Agent Skills hosts.
# Arguments (--dry-run, --uninstall, --help) are passed to every host installer.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOSTS="cursor claude codex qwen qoder lingma"

dry_run=0
for arg in "$@"; do
  case "$arg" in
    -h|--help) exec "$ROOT/scripts/install-cursor.sh" --help ;;
    -n|--dry-run) dry_run=1 ;;
  esac
done

# Preflight every host before touching any: a conflict in the last host must
# not leave the first ones installed.
if [[ "$dry_run" == "0" ]]; then
  for host in $HOSTS; do
    if ! "$ROOT/scripts/install-$host.sh" --dry-run "$@" >/dev/null; then
      echo "FAIL: preflight failed for $host; no host was changed" >&2
      exit 1
    fi
  done
fi

"$ROOT/scripts/install-cursor.sh" "$@"
"$ROOT/scripts/install-claude.sh" "$@"
"$ROOT/scripts/install-codex.sh" "$@"
"$ROOT/scripts/install-qwen.sh" "$@"
"$ROOT/scripts/install-qoder.sh" "$@"
"$ROOT/scripts/install-lingma.sh" "$@"
echo "OK: all local hosts processed from $ROOT"
