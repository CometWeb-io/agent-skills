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
`extras/cursor-routing.mdc` is a compact fallback for checkouts without the
full rule; a link an older install made to it is re-pointed to the full rule on
the next run. Both are generated from `registry/skills.json` by
`tooling/generate_adapters.py`, so neither lists a different skill set.

Codex and other hosts that read `AGENTS.md` get the same routing table from
`extras/AGENTS.snippet.md`. No installer edits your `AGENTS.md`; paste the block
between its `BEGIN`/`END` markers into a project's `AGENTS.md` (or `CLAUDE.md`)
and replace that block when you update. Some packages also ship a per-skill project rule
at `skills/<skill>/extras/cursor-rule.mdc` that you can copy into a project's
`.cursor/rules/`; the installer does not link those.
`install-all.sh` runs all six. To try an installer without touching your real
host directories, point the variable at a scratch path:

```bash
CLAUDE_SKILLS_DIR="$(mktemp -d)/skills" ./scripts/install-claude.sh
```

## Plugin marketplaces

Claude Code can also install the repository as a plugin:

```bash
claude plugin marketplace add CometWeb-io/agent-skills
claude plugin install cometweb-agent-skills@cometweb-agent-skills
```

or `/plugin marketplace add` and `/plugin install` inside a session. The
marketplace entry in `.claude-plugin/marketplace.json` points at the `main`
branch on GitHub, so adding a local clone as the marketplace still installs
what is on GitHub, not your working tree. To try uncommitted changes, start a
session with `claude --plugin-dir "$PWD"` from the clone instead;
`claude --plugin-dir "$PWD" plugin details cometweb-agent-skills` lists the
skills that session would load.

Claude Code keeps each installed plugin in a cache keyed by the `version` in
`.claude-plugin/plugin.json`. `claude plugin marketplace update` followed by
`claude plugin update cometweb-agent-skills@cometweb-agent-skills` replaces the
cached copy only when that version has changed; with the same version it
reports "already at the latest version" and keeps the old skill set. Codex
caches installed plugins by version in the same way, which is why every skill
change bumps the plugin version ([CONTRIBUTING.md](CONTRIBUTING.md#plugin-version)).

To validate the manifests without touching your own Claude Code settings, give
the CLI a scratch config directory:

```bash
scratch="$(mktemp -d)"
HOME="$scratch" CLAUDE_CONFIG_DIR="$scratch/claude" \
  claude plugin validate --strict .claude-plugin/plugin.json
HOME="$scratch" CLAUDE_CONFIG_DIR="$scratch/claude" \
  claude plugin validate --strict .claude-plugin/marketplace.json
```

ChatGPT and Codex use `.agents/plugins/marketplace.json`: a workspace admin
imports `https://github.com/CometWeb-io/agent-skills` as a marketplace with an
empty Path. [docs/OPENAI-MARKETPLACE.md](docs/OPENAI-MARKETPLACE.md) covers
branches, sync and local use; `tooling/validate_openai_plugin.py` checks the
manifest.

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
any package lacks `SKILL.md`, installation stops before touching a host target
(a folder holding only cache files is skipped instead; see below).

The destination must not be the repository's `skills/` directory, its parent,
or a directory inside it (including symlink aliases). Installers reject that
overlap before changing any skill package.

## Upgrade after `git pull`

```bash
git pull
./scripts/install-all.sh --dry-run   # shows "would link <new>" and "would prune stale link <old>"
./scripts/install-all.sh
```

Because the links point into the clone, changed skills are live as soon as
`git pull` finishes. Rerun the installer to link skills that were added and to
prune links to skills that were renamed or retired. A retired skill whose
scripts you once ran can leave its folder behind with only `__pycache__` files
in it, because git does not delete ignored files. The installer skips such a
folder with a `WARN: skipping` line that tells you to delete it. A folder
without `SKILL.md` that holds anything else still stops the run.
`tooling/tests/test_installer_upgrade_path.py` covers this with a real clone.
