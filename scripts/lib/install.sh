#!/usr/bin/env bash
# Shared safe installation helpers for local Agent Skills hosts.
# shellcheck shell=bash

set -euo pipefail

INSTALL_BACKUP_ROOT="${SKILLS_BACKUP_DIR:-$HOME/.local/share/agent-skills/backups}"
INSTALL_BACKUP_DIR=""

resolved_install_path() {
  local path="$1" base resolved index
  local -a missing=()

  while [[ ! -d "$path" ]]; do
    if [[ -L "$path" ]]; then
      echo "FAIL: install target contains a broken symlink: $path" >&2
      return 1
    fi
    missing+=("$(basename "$path")")
    path="$(dirname "$path")"
  done
  resolved="$(cd -P "$path" && pwd -P)"
  for ((index=${#missing[@]}-1; index>=0; index--)); do
    base="${missing[index]}"
    case "$base" in
      .|"") ;;
      ..) resolved="$(dirname "$resolved")" ;;
      *) resolved="${resolved%/}/$base" ;;
    esac
  done
  printf '%s\n' "$resolved"
}

prepare_install_target() {
  local target="$1"
  local source_root="$2"
  local target_real source_real

  target_real="$(resolved_install_path "$target")"
  source_real="$(resolved_install_path "$source_root")"
  if [[ "$target_real" == "/" || "$target_real" == "$source_real" ||
        "$target_real" == "$source_real"/* || "$source_real" == "$target_real"/* ]]; then
    echo "FAIL: install target overlaps the source skill tree: $target" >&2
    return 1
  fi
  mkdir -p "$target"
}

preflight_existing_path() {
  local path="$1" expected="$2"
  if [[ -L "$path" && "$(readlink "$path")" == "$expected" ]]; then
    return 0
  fi
  if [[ ( -e "$path" || -L "$path" ) && "${SKILLS_REPLACE_CONFLICTS:-0}" != "1" ]]; then
    echo "FAIL: conflicting installation path: $path (set SKILLS_REPLACE_CONFLICTS=1 to back up and replace)" >&2
    return 1
  fi
}

preflight_install_conflicts() {
  local target="$1" source_root="$2" skill_names="$3" name
  if [[ "${SKILLS_REPLACE_CONFLICTS:-0}" != "0" && "${SKILLS_REPLACE_CONFLICTS:-0}" != "1" ]]; then
    echo "FAIL: SKILLS_REPLACE_CONFLICTS must be 0 or 1" >&2
    return 1
  fi
  while IFS= read -r name; do
    [[ -z "$name" ]] && continue
    preflight_existing_path "$target/$name" "$source_root/$name" || return 1
  done <<< "$skill_names"
}

ensure_install_backup_dir() {
  if [[ -z "$INSTALL_BACKUP_DIR" ]]; then
    INSTALL_BACKUP_DIR="$INSTALL_BACKUP_ROOT/$(date -u +%Y%m%dT%H%M%SZ)-$$"
    mkdir -p "$INSTALL_BACKUP_DIR"
  fi
}

backup_existing_path() {
  local path="$1"
  local label="$2"
  local destination

  if [[ ! -e "$path" && ! -L "$path" ]]; then
    return 0
  fi
  if [[ "${SKILLS_REPLACE_CONFLICTS:-0}" != "1" ]]; then
    echo "FAIL: conflicting installation path: $path (set SKILLS_REPLACE_CONFLICTS=1 to back up and replace)" >&2
    return 1
  fi

  ensure_install_backup_dir
  destination="$INSTALL_BACKUP_DIR/$label"
  if [[ -e "$destination" || -L "$destination" ]]; then
    destination="${destination}.$RANDOM"
  fi
  mv -- "$path" "$destination"
  echo "backed up $path -> $destination"
}

install_skill_link() {
  local source="$1"
  local destination="$2"
  local name="$3"
  local current_target

  mkdir -p "$(dirname "$destination")"
  if [[ -L "$destination" ]]; then
    current_target="$(readlink "$destination")"
    if [[ "$current_target" == "$source" ]]; then
      echo "already linked $name -> $source"
      return 0
    fi
    backup_existing_path "$destination" "$name"
  elif [[ -e "$destination" ]]; then
    backup_existing_path "$destination" "$name"
  fi

  ln -s -- "$source" "$destination"
  echo "linked $name -> $source"
}

print_install_backup_summary() {
  if [[ -n "$INSTALL_BACKUP_DIR" ]]; then
    echo "backup directory: $INSTALL_BACKUP_DIR"
  fi
}
