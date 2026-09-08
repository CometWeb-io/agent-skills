# Target architecture

## Done

Platform hardening from the architecture review is complete:

- Private canonical repo with registry, tooling, CI, evals
- CW-AIP v2 payloads: context, evidence, decision, finding, roadmap, release
- Compatibility gate, 100+ routing cases, behavior fixtures
- Orchestrator execution_mode + multiagent alias sync
- Progressive disclosure (ER, Council LIGHT/STANDARD/DEEP)
- generate_adapters + public mirror dry-run + sync_public_repo
- Install scripts for Cursor / Claude / Codex from private
- Public sync PR pipeline into `MaciejZet/agent-skills`

## Optional follow-ups (not blocking)

1. Operator-run LLM blind comparisons on release tags
2. Per-release immutable eval report artifacts in GitHub Releases
3. Domain skills emitting v2 Finding/Roadmap/Release envelopes end-to-end
4. Cadence automation (scheduled sync PR)
