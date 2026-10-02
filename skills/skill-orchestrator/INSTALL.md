# Installation — skill-orchestrator

Distributable unit: the whole `skill-orchestrator/` directory (keep `SKILL.md`, `references/`, `scripts/`, `agents/` paths intact).

## Cursor (recommended)

From the repo root:

```bash
./scripts/install-cursor.sh
```

Or symlink only this skill:

```bash
ln -s "$(pwd)/skills/skill-orchestrator" ~/.cursor/skills/skill-orchestrator
```

## Claude Code

From the repo root:

```bash
./scripts/install-claude.sh
```

Or symlink only this skill into `~/.claude/skills/`.

## ChatGPT / Codex

Build a ZIP from the repo root with `uv run python tooling/package_skill.py skill-orchestrator` (written to `dist/skill-orchestrator/<version>/skill.zip`) and upload it, or copy this folder into the host's skills path. Metadata: `agents/openai.yaml`.

## Invoke

```text
@skill-orchestrator — <goal spanning multiple skills>
```

Example:

```text
@skill-orchestrator — Verify pricing claims, then Council on GO/NO-GO for the new tier.
```

Read `SKILL.md` for archetypes. Run `scripts/orchestrate_kernel.py` when the host allows code execution.
