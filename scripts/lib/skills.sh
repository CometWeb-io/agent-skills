#!/usr/bin/env bash
# Discover skill package names from skills/*/SKILL.md in the canonical public repo.
# shellcheck shell=bash

_SKILLS_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$_SKILLS_LIB_DIR/../.." && pwd)"

list_skills() {
  local d name
  for d in "$ROOT"/skills/*; do
    [[ -d "$d" ]] || continue
    if [[ ! -f "$d/SKILL.md" ]]; then
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
