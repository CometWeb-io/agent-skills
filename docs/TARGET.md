# Target architecture

## Done (P0 + P1 hardening)

- Repo truth: README matches on-disk layout
- Canonical `registry/skills.json` + `hosts.json`
- CW-AIP v2 core + ContextEnvelope JSON Schema + semantic validator
- Compatibility gate (incl. Codex description ≤ 1024)
- Routing evals (100+ cases) + context behavior fixtures
- CI validate workflow (incl. orchestrator sync + public mirror dry-run)
- Orchestrator `execution_mode` + multiagent alias + `sync_orchestrator.py`
- Context path redaction, remote freshness, registry-first bindings
- Council LIGHT / STANDARD / DEEP cognitive profiles
- Evidence Researcher progressive disclosure (`kernel-cli.md`)
- `generate_adapters.py` → docs table, Cursor routing, `agents/openai.yaml`
- `publish_public_dry_run.py` strips private path templates for mirror preview

## Remaining P2

1. Automated sync PR into `MaciejZet/agent-skills` from dry-run output
2. Per-skill immutable `dist/<skill>/<version>/skill.zip` + pinned eval report on release
3. Blind baseline comparison harness for LLM behavior evals (operator-run)
4. Expand CW-AIP v2 payload schemas beyond Context (Evidence/Decision wrappers)
5. Install scripts for private canonical → Cursor/Claude/Codex (pointing at this repo)
