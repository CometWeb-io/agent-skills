#!/usr/bin/env bash
# Auto-discovers skills from skills/*/SKILL.md in the canonical public repo.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck source=lib/skills.sh
source "$ROOT/scripts/lib/skills.sh"
# shellcheck source=lib/install.sh
source "$ROOT/scripts/lib/install.sh"

TARGET="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
skill_names="$(list_skills)"
[[ -n "$skill_names" ]] || { echo "FAIL: no skill packages found" >&2; exit 1; }
prepare_install_target "$TARGET" "$ROOT/skills"
preflight_install_conflicts "$TARGET" "$ROOT/skills" "$skill_names"
count=0
while IFS= read -r name; do
  [[ -z "$name" ]] && continue
  src="$ROOT/skills/$name"
  dest="$TARGET/$name"
  if [[ ! -d "$src" ]]; then
    echo "FAIL: missing skill directory $src" >&2
    exit 1
  fi
  install_skill_link "$src" "$dest" "$name"
  count=$((count + 1))
done <<< "$skill_names"
print_install_backup_summary
echo "OK: $count Claude Code skills installed in $TARGET"
