# Installation — web-app-auditor v1.1

The distributable skill is the complete `web-app-auditor/` directory. Keep the
relative paths intact because `SKILL.md` loads references, schemas, and scripts
on demand.

```text
web-app-auditor/
├── SKILL.md
├── agents/openai.yaml
├── references/
├── assets/
├── scripts/validate_report.py
├── tests/
├── extras/
├── LICENSE
└── INSTALL.md
```

## ChatGPT / OpenAI skill upload

Upload the packaged `skill.zip`. The ChatGPT-compatible `SKILL.md` frontmatter
contains only `name` and `description`; OpenAI UI metadata lives in
`agents/openai.yaml`.

## Claude Code / repository-based agents

If the host supports filesystem skills, copy the whole folder into the skill
location documented by that host, or run `./scripts/install-claude.sh` from the
repo root for `~/.claude/skills/`. A common repository-level location is:

```text
.agents/skills/web-app-auditor/
```

Some hosts also support product-specific directories such as `.cursor/skills/`,
`.claude/skills/` (Claude Code — see repo `./scripts/install-claude.sh`), or
`.agents/skills/`. Those conventions can change; prefer the current host
documentation over this file.

`extras/cursor-rule.mdc` and `extras/AGENTS.snippet.md` are optional adapters.
They do not replace the skill itself.

## Recommended invocation

```text
Use web-app-auditor.
Mode: area
Depth: standard
Target: /billing and its owned screens
Persona: signed-in owner
Environment: staging
Check interactions, data consistency, mobile, forms and states.
Do not execute external/destructive/financial side effects.
```

For exhaustive work:

```text
Use web-app-auditor.
Mode: page
Depth: forensic
Target: current screen
Environment: local
Test every in-scope control instance and material claim, except actions blocked
by the mutation safety policy.
```

## Report validation

When the host can create files and run code, produce `audit-report.json` and run:

```bash
python scripts/validate_report.py audit-report.json
```

A valid report exits `0`; protocol errors exit non-zero. The validator uses only
Python's standard library.

## Safety default

`production` and `unknown` are read-only. Use staging/test/local with disposable
data for mutation tests. Payment, real outbound communication, publishing,
permission/security changes, and irreversible production deletion are not
executed merely for audit coverage.
