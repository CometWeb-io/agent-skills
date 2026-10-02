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
Every host installer runs the same code path (`scripts/lib/install.sh`) and
links each package as a symlink into the host's skills directory, so `git pull`
in this clone updates installed skills and moving or deleting the clone breaks
them:

| Host | Script | Default target | Override |
| --- | --- | --- | --- |
| Cursor | `install-cursor.sh` | `~/.cursor/skills` | `CURSOR_SKILLS_DIR` |
| Claude Code | `install-claude.sh` | `~/.claude/skills` | `CLAUDE_SKILLS_DIR` |
| Codex | `install-codex.sh` | `~/.codex/skills` | `CODEX_SKILLS_DIR` |
| Qwen Code | `install-qwen.sh` | `~/.qwen/skills` | `QWEN_SKILLS_DIR` |
| Qoder | `install-qoder.sh` | `~/.qoder/skills` | `QODER_SKILLS_DIR` |
| Lingma | `install-lingma.sh` | `~/.lingma/skills` | `LINGMA_SKILLS_DIR` |

Cursor also links `docs/generated-cursor-routing.mdc` as the routing rule
(`~/.cursor/rules/cometweb-agent-skills.mdc`, override with `CURSOR_RULES_DIR`).
`install-all.sh` runs all six. To try an installer without touching your real
host directories, point the variable at a scratch path:

```bash
CLAUDE_SKILLS_DIR="$(mktemp -d)/skills" ./scripts/install-claude.sh
```

Claude Code can also install the repository as a plugin
(`/plugin marketplace add CometWeb-io/agent-skills`, then
`/plugin install cometweb-agent-skills@cometweb-agent-skills`); ChatGPT and
Codex use the marketplace described in
[docs/OPENAI-MARKETPLACE.md](docs/OPENAI-MARKETPLACE.md).

## Preview, update and remove

```bash
./scripts/install-claude.sh --dry-run    # run every check, print the plan, write nothing
./scripts/install-claude.sh              # install or update
./scripts/install-claude.sh --uninstall  # remove this checkout's links
./scripts/install-all.sh --dry-run       # the same flags work for every host at once
```

`--uninstall` removes only symlinks that point into this checkout's `skills/`
(and, for Cursor, the routing rule it linked or generated). Your own skills,
copies and links to other checkouts are left in place. Rerunning an install
also prunes links to skills that were renamed or retired from this checkout.

`install-all.sh` previews every host first and changes nothing if any host
would fail, so a conflict in one host does not leave the others half-installed.

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
