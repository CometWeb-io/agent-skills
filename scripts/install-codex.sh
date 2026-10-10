#!/usr/bin/env bash
# shellcheck source-path=SCRIPTDIR
# Link canonical CometWeb skills into Codex's user skills directory.
# Auto-discovers skills/*/SKILL.md; run with --help for --dry-run and --uninstall.
#
# Codex documents $HOME/.agents/skills as the user skills location. Earlier
# versions of this installer linked into $CODEX_HOME/skills (~/.codex/skills);
# with the default target, links this checkout made there are moved into the
# backup directory once the new links exist, so each skill is installed once.
# Setting CODEX_SKILLS_DIR (for example to ~/.codex/skills) keeps that exact
# target and leaves every other directory alone.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck source=lib/skills.sh
source "$ROOT/scripts/lib/skills.sh"
# shellcheck source=lib/install.sh
source "$ROOT/scripts/lib/install.sh"

TARGET="${CODEX_SKILLS_DIR:-$HOME/.agents/skills}"
LEGACY_DIR=""
if [[ -z "${CODEX_SKILLS_DIR:-}" ]]; then
  LEGACY_DIR="${CODEX_HOME:-$HOME/.codex}/skills"
  # Same path-escape gate as the target, before anything is written.
  resolved_install_path "$LEGACY_DIR" >/dev/null
fi

# True when there is a legacy directory to migrate that is not the target
# itself (a ~/.codex/skills symlinked to ~/.agents/skills holds the new links).
legacy_applies() {
  local legacy_real target_real
  [[ -n "$LEGACY_DIR" && -d "$LEGACY_DIR" ]] || return 1
  legacy_real="$(resolved_install_path "$LEGACY_DIR")" || return 1
  target_real="$(resolved_install_path "$TARGET")" || return 1
  [[ "$legacy_real" != "$target_real" ]]
}

# Moves this checkout's links out of the legacy directory into the backup
# directory. Anything else there (a user's own skill, a link to another
# checkout) is left in place.
host_apply() {
  local entry name moved=0
  legacy_applies || return 0
  for entry in "$LEGACY_DIR"/*; do
    is_managed_link "$entry" "$ROOT/skills" || continue
    name="$(basename "$entry")"
    selected_skill "$name" || continue
    if [[ "$INSTALL_DRY_RUN" == "1" ]]; then
      echo "would move legacy link $name out of $LEGACY_DIR"
    else
      ensure_install_backup_dir
      mv -- "$entry" "$INSTALL_BACKUP_DIR/codex-legacy-$name"
      echo "moved legacy link $name from $LEGACY_DIR -> $INSTALL_BACKUP_DIR/codex-legacy-$name"
    fi
    moved=$((moved + 1))
  done
  if [[ "$moved" -gt 0 ]]; then
    echo "$(plan_verb migrate migrated) $moved Codex skill links from $LEGACY_DIR to $TARGET"
  fi
}

host_uninstall() {
  local saved="$UNINSTALL_COUNT"
  legacy_applies || return 0
  uninstall_skill_links "$LEGACY_DIR" "$ROOT/skills"
  UNINSTALL_COUNT=$((saved + UNINSTALL_COUNT))
}

run_host_installer "Codex" "$TARGET" "$@"
