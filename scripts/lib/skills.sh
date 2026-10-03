#!/usr/bin/env bash
# Discover skill package names from skills/*/SKILL.md in the canonical public repo.
# shellcheck shell=bash

_SKILLS_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$_SKILLS_LIB_DIR/../.." && pwd)"

# True when a directory holds files but every one of them is an untracked cache
# (__pycache__/, *.pyc, *.pyo, .DS_Store). That is what `git pull` leaves behind
# after it deletes a retired skill whose scripts were once run: git removes the
# tracked files but cannot remove the ignored caches, so the directory survives.
is_cache_residue_dir() {
  local dir="$1" file found=0
  while IFS= read -r -d '' file; do
    case "$file" in
      */__pycache__/*|*.pyc|*.pyo|*/.DS_Store) found=1 ;;
      *) return 1 ;;
    esac
  done < <(find "$dir" \( -type f -o -type l \) -print0)
  [[ "$found" == "1" ]]
}

list_skills() {
  local d name
  for d in "$ROOT"/skills/*; do
    [[ -d "$d" ]] || continue
    if [[ ! -f "$d/SKILL.md" ]]; then
      if is_cache_residue_dir "$d"; then
        echo "WARN: skipping $d: no SKILL.md, only cache files left (a retired skill after git pull?); remove it with: rm -rf '$d'" >&2
        continue
      fi
      echo "FAIL: missing skill entrypoint $d/SKILL.md" >&2
      return 1
    fi
  done
  for d in "$ROOT"/skills/*/SKILL.md; do
    [[ -f "$d" ]] || continue
    name="$(basename "$(dirname "$d")")"
    printf '%s\n' "$name"
  done | sort
}
