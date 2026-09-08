# Installation — evidence-researcher v1.0.0

Distributable unit: the whole `evidence-researcher/` directory (keep `SKILL.md`, `references/`, `scripts/`, `agents/` paths intact).

## Cursor (recommended)

From the repo root:

```bash
./scripts/install-cursor.sh
```

Or symlink only this skill:

```bash
ln -s "$(pwd)/skills/evidence-researcher" ~/.cursor/skills/evidence-researcher
```

Optional: copy or link `extras/cursor-rule.mdc` into your project `.cursor/rules/`.

## Claude Code

From the repo root:

```bash
./scripts/install-claude.sh
```

Or symlink only this skill into `~/.claude/skills/`.

## ChatGPT / Codex

Upload a ZIP of this skill folder (see repo `scripts/package-releases.sh`) or copy into the host's skills path. Metadata: `agents/openai.yaml`.

## Invoke

```text
@evidence-researcher — <your task in plain language>
```

Read `SKILL.md` for mode-specific contracts. Run scripts under `scripts/` when the host allows code execution — they enforce invariants prompt-only skills cannot.
