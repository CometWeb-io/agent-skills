#!/usr/bin/env bash
# The Python checker takes an explicit target and propagates all failures.
# Usage: bash tooling/public-safety-check.sh --root dist/public-mirror
set -euo pipefail
TOOLING="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$TOOLING/public_safety.py" "$@"
