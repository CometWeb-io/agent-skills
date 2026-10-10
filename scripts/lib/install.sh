#!/usr/bin/env bash
# Shared safe installation helpers for local Agent Skills hosts.
# shellcheck shell=bash

set -euo pipefail

INSTALL_BACKUP_ROOT="${SKILLS_BACKUP_DIR:-$HOME/.local/share/agent-skills/backups}"
INSTALL_BACKUP_DIR=""
# Set by parse_install_args: "install" or "uninstall", and 1 for a no-write preview.
INSTALL_MODE="install"
INSTALL_DRY_RUN=0
INSTALL_SKILLS=()
INSTALL_REF=""

install_usage() {
  cat <<USAGE
Usage: $(basename "$0") [--skill ID ...] [--ref SHA] [--dry-run] [--uninstall] [--help]

Links every skills/*/SKILL.md package of this checkout into the host's skills
directory. Reruns are no-ops; conflicting paths stop the run before any change.

  -n, --dry-run   run every check and print the planned changes without writing
  --uninstall     remove only links that point into this checkout's skills/
  --skill ID      limit to a named package (repeatable; default: all packages)
  --ref SHA       require this exact 40-character commit and a clean checkout
  -h, --help      show this help

Environment:
  SKILLS_REPLACE_CONFLICTS=1  back up and replace conflicting paths
  SKILLS_BACKUP_DIR=PATH      backup root (default ~/.local/share/agent-skills/backups)
USAGE
}

parse_install_args() {
  local arg
  while [[ "$#" -gt 0 ]]; do
    arg="$1"; shift
    case "$arg" in
      -n|--dry-run) INSTALL_DRY_RUN=1 ;;
      --uninstall) INSTALL_MODE="uninstall" ;;
      --skill)
        [[ "$#" -gt 0 && "$1" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]] || { echo "FAIL: --skill needs a skill ID" >&2; return 2; }
        INSTALL_SKILLS+=("$1"); shift ;;
      --ref)
        [[ "$#" -gt 0 && "$1" =~ ^[0-9a-f]{40}$ ]] || { echo "FAIL: --ref needs a full commit SHA" >&2; return 2; }
        INSTALL_REF="$1"; shift ;;
      -h|--help) install_usage; exit 0 ;;
      *)
        echo "FAIL: unknown argument: $arg" >&2
        install_usage >&2
        return 2
        ;;
    esac
  done
}

selected_skill() {
  local selected
  [[ "${#INSTALL_SKILLS[@]}" == "0" ]] && return 0
  for selected in ${INSTALL_SKILLS[@]+"${INSTALL_SKILLS[@]}"}; do
    [[ "$selected" == "$1" ]] && return 0
  done
  return 1
}

# Prints the action verb, prefixed with "would " in dry-run mode.
plan_verb() {
  if [[ "$INSTALL_DRY_RUN" == "1" ]]; then
    printf 'would %s' "$1"
  else
    printf '%s' "$2"
  fi
}

resolved_install_path() {
  local path="$1" base resolved index
  local -a missing=()

  # Reject climb-out before dirname collapsing can turn .. into a parent path.
  # Custom absolute targets without a ".." component remain allowed.
  case "/${path}/" in
    */../*)
      echo "FAIL: install target must not contain '..' path components: $path" >&2
      return 1
      ;;
  esac

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
      ..)
        echo "FAIL: install target must not contain '..' path components: $1" >&2
        return 1
        ;;
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
  if [[ "$INSTALL_DRY_RUN" != "1" ]]; then
    mkdir -p "$target"
  fi
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
    mkdir -p -- "$INSTALL_BACKUP_ROOT"
    # A fresh directory with an unpredictable suffix: a pre-created directory or
    # symlink at a guessable name cannot receive the backups.
    INSTALL_BACKUP_DIR="$(mktemp -d "$INSTALL_BACKUP_ROOT/$(date -u +%Y%m%dT%H%M%SZ)-XXXXXXXX")"
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

  if [[ "$INSTALL_DRY_RUN" == "1" ]]; then
    echo "would back up $path"
    return 0
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

  if [[ "$INSTALL_DRY_RUN" != "1" ]]; then
    mkdir -p "$(dirname "$destination")"
  fi
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

  if [[ "$INSTALL_DRY_RUN" != "1" ]]; then
    ln -s -- "$source" "$destination"
  fi
  echo "$(plan_verb link linked) $name -> $source"
}

# A link is managed by this checkout only when it is a symlink whose literal
# target is <source_root>/<its own name>. Anything else belongs to the user.
is_managed_link() {
  local path="$1" source_root="$2"
  [[ -L "$path" && "$(readlink "$path")" == "$source_root/$(basename "$path")" ]]
}

# Removes managed links whose skill package no longer exists in the checkout,
# so a renamed or retired skill does not leave a dangling entry behind.
prune_stale_links() {
  local target="$1" source_root="$2" entry
  [[ -d "$target" ]] || return 0
  for entry in "$target"/*; do
    is_managed_link "$entry" "$source_root" || continue
    [[ -f "$(readlink "$entry")/SKILL.md" ]] && continue
    if [[ "$INSTALL_DRY_RUN" != "1" ]]; then
      rm -- "$entry"
    fi
    echo "$(plan_verb prune pruned) stale link $(basename "$entry")"
  done
}

uninstall_skill_links() {
  local target="$1" source_root="$2" entry count=0
  resolved_install_path "$target" >/dev/null
  UNINSTALL_COUNT=0
  [[ -d "$target" ]] || return 0
  for entry in "$target"/*; do
    selected_skill "$(basename "$entry")" || continue
    if is_managed_link "$entry" "$source_root"; then
      if [[ "$INSTALL_DRY_RUN" != "1" ]]; then
        rm -- "$entry"
      fi
      echo "$(plan_verb unlink unlinked) $(basename "$entry")"
      count=$((count + 1))
    elif [[ -e "$entry" || -L "$entry" ]] && [[ -f "$source_root/$(basename "$entry")/SKILL.md" ]]; then
      echo "skip $(basename "$entry"): not a link to this checkout"
    fi
  done
  UNINSTALL_COUNT=$count
}

# Shared entry point for every host installer. Optional per-host hooks:
#   host_preflight  — extra checks; must not write
#   host_apply      — extra install steps after the skills are linked
#   host_uninstall  — extra removal steps
run_host_installer() {
  local label="$1" target="$2" source_root="$ROOT/skills" skill_names name source_status count=0
  shift 2
  parse_install_args "$@"
  if [[ -n "$INSTALL_REF" ]]; then
    [[ "$(git -C "$ROOT" rev-parse HEAD)" == "$INSTALL_REF" ]] || { echo "FAIL: checkout does not match --ref" >&2; return 2; }
    source_status="$(git -C "$ROOT" status --porcelain --untracked-files=all)" || { echo "FAIL: cannot inspect pinned checkout" >&2; return 2; }
    [[ -z "$source_status" ]] || { echo "FAIL: pinned installation requires a clean checkout" >&2; return 2; }
    echo "source commit: $INSTALL_REF"
  fi
  for name in ${INSTALL_SKILLS[@]+"${INSTALL_SKILLS[@]}"}; do
    [[ -f "$source_root/$name/SKILL.md" ]] || { echo "FAIL: unknown skill: $name" >&2; return 2; }
  done

  if [[ "$INSTALL_MODE" == "uninstall" ]]; then
    uninstall_skill_links "$target" "$source_root"
    if declare -F host_uninstall >/dev/null; then
      host_uninstall
    fi
    echo "OK: $(plan_verb "remove" "removed") $UNINSTALL_COUNT $label skill links from $target"
    return 0
  fi

  skill_names="$(list_skills)"
  if [[ "${#INSTALL_SKILLS[@]}" -gt 0 ]]; then
    skill_names="$(printf '%s\n' "${INSTALL_SKILLS[@]}" | sort -u)"
  fi
  [[ -n "$skill_names" ]] || { echo "FAIL: no skill packages found" >&2; return 1; }
  prepare_install_target "$target" "$source_root"
  preflight_install_conflicts "$target" "$source_root" "$skill_names"
  if declare -F host_preflight >/dev/null; then
    host_preflight
  fi
  while IFS= read -r name; do
    [[ -z "$name" ]] && continue
    if [[ ! -d "$source_root/$name" ]]; then
      echo "FAIL: missing skill directory $source_root/$name" >&2
      return 1
    fi
    install_skill_link "$source_root/$name" "$target/$name" "$name"
    count=$((count + 1))
  done <<< "$skill_names"
  if [[ "${#INSTALL_SKILLS[@]}" == "0" ]]; then
    prune_stale_links "$target" "$source_root"
  fi
  if declare -F host_apply >/dev/null; then
    host_apply
  fi
  print_install_backup_summary
  if [[ "$INSTALL_DRY_RUN" == "1" ]]; then
    echo "OK: dry run, $count $label skills would be installed in $target (nothing written)"
  else
    echo "OK: $count $label skills installed in $target"
  fi
}

print_install_backup_summary() {
  if [[ -n "$INSTALL_BACKUP_DIR" ]]; then
    echo "backup directory: $INSTALL_BACKUP_DIR"
  fi
}
