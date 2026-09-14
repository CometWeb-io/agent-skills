# Installation — Product Operator 1.2.0-rc.1 candidate

Keep the entire directory named `product-operator`: SKILL.md, references, scripts,
agents, assets, examples and tests. The archive is a candidate, not a release or
proof that the current chat has loaded the skill.

## Local execution, independent of an agent host

Runtime scripts use the Python standard library. Python 3.10+ is required by the
syntax; see the delivery evidence for the exact interpreter actually tested.
From the extracted skill directory:

```bash
python3 scripts/self_check.py
python3 scripts/prepare_brief.py --input examples/plan.synthetic.json --language pl
```

The example is synthetic, not evidence about CometWeb. The first command checks
local files and deterministic behavior, not model quality or tool permissions.
Full developer regression tests additionally require pytest:

```bash
python3 -m pytest -q tests
```

## Host placement

Official source guidance checked 2026-09-12:

- Codex local personal scope: `~/.agents/skills/product-operator/SKILL.md`;
  project scope: `.agents/skills/product-operator/SKILL.md`.
- Claude Code local personal scope: `~/.claude/skills/product-operator/SKILL.md`;
  project scope: `.claude/skills/product-operator/SKILL.md`.
- Other hosts and ChatGPT web: use their supported skill/plugin import mechanism;
  copying local files alone does not make them available in a remote chat.

These documented locations were not tested in a running host during this build.
Check the host's skill inventory and exact loaded version after installation.
Review existing same-name installations before copying; do not overwrite them blindly.
No installer, plugin change, remote publish or automatic migration is run by this package.
Do not follow repository-root installer commands when using the standalone archive:
those scripts are not bundled dependencies.

Sources:
- https://learn.chatgpt.com/docs/build-skills
- https://code.claude.com/docs/en/skills
- https://agentskills.io/specification
