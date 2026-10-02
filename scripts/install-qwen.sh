#!/usr/bin/env bash
# shellcheck source-path=SCRIPTDIR
# Link canonical CometWeb skills into Qwen Code's native skills directory.
# Auto-discovers skills/*/SKILL.md; run with --help for --dry-run and --uninstall.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck source=lib/skills.sh
source "$ROOT/scripts/lib/skills.sh"
# shellcheck source=lib/install.sh
source "$ROOT/scripts/lib/install.sh"

run_host_installer "Qwen Code" "${QWEN_SKILLS_DIR:-$HOME/.qwen/skills}" "$@"
