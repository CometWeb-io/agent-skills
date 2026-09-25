#!/usr/bin/env bash
# Link canonical CometWeb skills into Lingma's skills directory.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck source=lib/skills.sh
source "$ROOT/scripts/lib/skills.sh"
# shellcheck source=lib/install.sh
source "$ROOT/scripts/lib/install.sh"

TARGET="${LINGMA_SKILLS_DIR:-$HOME/.lingma/skills}"
skill_names="$(list_skills)"
[[ -n "$skill_names" ]] || { echo "FAIL: no skill packages found" >&2; exit 1; }
prepare_install_target "$TARGET" "$ROOT/skills"
preflight_install_conflicts "$TARGET" "$ROOT/skills" "$skill_names"
count=0
while IFS= read -r name; do
  [[ -z "$name" ]] && continue
  src="$ROOT/skills/$name"
  dest="$TARGET/$name"
  [[ -d "$src" ]] || { echo "FAIL: missing skill directory $src" >&2; exit 1; }
  install_skill_link "$src" "$dest" "$name"
  count=$((count + 1))
done <<< "$skill_names"
print_install_backup_summary
echo "OK: $count Lingma skills installed in $TARGET"
