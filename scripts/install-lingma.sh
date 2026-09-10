#!/usr/bin/env bash
# Link canonical CometWeb skills into Lingma's skills directory.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck source=lib/skills.sh
source "$ROOT/scripts/lib/skills.sh"

TARGET="${LINGMA_SKILLS_DIR:-$HOME/.lingma/skills}"
mkdir -p "$TARGET"
count=0
while IFS= read -r name; do
  [[ -z "$name" ]] && continue
  src="$ROOT/skills/$name"
  dest="$TARGET/$name"
  [[ -d "$src" ]] || { echo "FAIL: missing skill directory $src" >&2; exit 1; }
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
echo "OK: $count Lingma skills installed in $TARGET"
