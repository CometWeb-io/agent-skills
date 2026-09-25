# Install

This repository is the public canonical source: `CometWeb-io/agent-skills`.

```bash
./scripts/install-all.sh
# or individually:
./scripts/install-cursor.sh
./scripts/install-claude.sh
./scripts/install-codex.sh
```

Skills are discovered from `skills/*/SKILL.md` (includes `cometweb-context`).
Cursor also links `docs/generated-cursor-routing.mdc` as the routing rule.

The installers discover packages from `skills/*/SKILL.md`; they do not copy
private runtime bindings or credentials. Connector access and external side
effects remain host-specific and must be authorized by the user.

Installers are safe to rerun. By default, an existing skill directory, file,
or foreign symlink causes installation to stop **before changing any skill**.
To explicitly back up and replace conflicts, run for example:

```bash
SKILLS_REPLACE_CONFLICTS=1 ./scripts/install-all.sh
```

Conflicting entries are then moved to a dated backup under
`~/.local/share/agent-skills/backups/`. Set `SKILLS_BACKUP_DIR` to choose
another backup root. Existing custom Cursor routing files are preserved;
foreign routing symlinks also require the explicit replacement setting. If
any package lacks `SKILL.md`, installation stops before touching a host target.

The destination must not be the repository's `skills/` directory, its parent,
or a directory inside it (including symlink aliases). Installers reject that
overlap before changing any skill package.
