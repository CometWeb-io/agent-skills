# Target architecture

## Done in P0 (this hardening pass)

- Repo truth: README matches on-disk layout
- Canonical `registry/skills.json` + `hosts.json`
- CW-AIP v2 core + ContextEnvelope JSON Schema + semantic validator
- Compatibility gate (incl. Codex description ≤ 1024)
- Routing + context behavior eval fixtures
- CI validate workflow
- Orchestrator `execution_mode` + multiagent as thin alias
- Context path redaction + remote freshness fields
- Council LIGHT profile documented as default cognitive gate

## Remaining P1

1. `tooling/generate_adapters.py` writing Cursor rules + OpenAI yaml from registry only
2. Move remaining operational bindings out of `cometweb-context` SKILL into
   `references/source-registry.json` (machine-readable)
3. Expand trigger evals to 20–30 cases per foundation skill boundary
4. Progressive disclosure pass on Evidence Researcher cookbook sections
5. Public mirror pipeline (`public-safety-check` → sync subset)

## Remaining P2

1. Per-skill semver release artifacts with pinned eval reports
2. Immutable `dist/<skill>/<version>/skill.zip`
3. Blind baseline comparison harness for LLM behavior evals (operator-run)
