# Target architecture

## Done (platform usable)

- Private canonical repo with registry, tooling, CI, evals
- CW-AIP v2 payloads: context, evidence, decision, finding, roadmap, release
- Universal `validate_envelope.py` (core + payload + hash + `--final`)
- Registry is SSOT for descriptions, owns/triggers, and `routing_signals`
- Executable deterministic behavior evals for `cometweb-context` (no `or True`)
- Council progressive disclosure via `workflow-light|standard|deep.md`
- Install scripts + public mirror **tooling** (`publish_public_dry_run.py`, `sync_public_repo.py`)

## Not done (honest status)

- **Automated** public-sync PR GitHub Action (tooling exists; opens PR manually)
- Operator-run LLM blind comparisons on release tags (harness skeleton only)
- Domain skills emitting Finding/Roadmap/Release envelopes end-to-end in production flows

See `docs/PUBLIC_MIRROR.md` for the publish procedure.
