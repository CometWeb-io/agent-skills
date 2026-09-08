# Target architecture

## Done (P0–P2 platform)

- Repo truth + registry/hosts + CW-AIP v2 (context/evidence/decision)
- Compatibility gate, routing 100+ cases, behavior fixtures, CI
- Orchestrator execution_mode + sync, progressive disclosure
- generate_adapters (Cursor + OpenAI yaml)
- publish dry-run + sync_public_repo.py
- Install scripts discovering all skills (Cursor/Claude/Codex)
- Blind/baseline eval harness skeleton (`run_blind_eval_harness.py`)

## Remaining

1. Open/maintain PR syncing private → public `agent-skills` on a cadence
2. Finding/Roadmap/Release v2 payload schemas
3. Operator-run LLM blind comparisons wired to release tags
4. Optional: centrum symlink switch from public → private install
