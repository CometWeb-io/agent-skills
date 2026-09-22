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

Existing symlinks are refreshed. A real file or directory with the same skill
name is never deleted or overwritten; move it aside explicitly before running
the installer again.
