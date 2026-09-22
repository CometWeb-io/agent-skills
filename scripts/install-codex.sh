#!/usr/bin/env bash
# Auto-discovers skills from skills/*/SKILL.md in the canonical public repo.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck source=lib/skills.sh
source "$ROOT/scripts/lib/skills.sh"

TARGET="${CODEX_SKILLS_DIR:-$HOME/.codex/skills}"
mkdir -p "$TARGET"
count=0
while IFS= read -r name; do
  [[ -z "$name" ]] && continue
  src="$ROOT/skills/$name"
  dest="$TARGET/$name"
  if [[ ! -d "$src" ]]; then
    echo "FAIL: missing skill directory $src" >&2
    exit 1
  fi
  if [[ -L "$dest" ]]; then
    rm "$dest"
  elif [[ -e "$dest" ]]; then
    echo "FAIL: $dest exists and is not a symlink — move it aside first" >&2
    exit 1
  fi
  ln -s "$src" "$dest"
  echo "linked $name -> $src"
  count=$((count + 1))
done < <(list_skills)
echo "OK: $count Codex skills installed in $TARGET"
