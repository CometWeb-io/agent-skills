# Installation — ai-council v5.0.0

Distributable unit: the whole `ai-council/` directory (keep `SKILL.md`, `references/`, `scripts/`, `agents/` paths intact).

## Cursor (recommended)

From the repo root:

```bash
./scripts/install-cursor.sh
```

Or symlink only this skill:

```bash
ln -s "$(pwd)/skills/ai-council" ~/.cursor/skills/ai-council
```

Optional: copy or link `extras/cursor-rule.mdc` into your project `.cursor/rules/`.

## Claude Code

From the repo root:

```bash
./scripts/install-claude.sh
```

Or symlink only this skill into `~/.claude/skills/`.

## ChatGPT / Codex

Build a ZIP from the repo root with `uv run python tooling/package_skill.py ai-council` (written to `dist/ai-council/<version>/skill.zip`) and upload it, or copy this folder into the host's skills path. Metadata: `agents/openai.yaml`.

## Invoke

```text
@ai-council — <your task in plain language>
```

Read `SKILL.md` for mode-specific contracts. Run scripts under `scripts/` when the host allows code execution — they enforce invariants prompt-only skills cannot.
