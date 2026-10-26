# Context source map and helpers

Standalone resources; this directory is not a skill and has no routing or automatic preflight. The former `cometweb-context` skill was retired. Use only the sources needed for the question.

- [Source map](references/source-registry.md): claim-specific systems of record, bindings and fallback limits. Tracked files contain placeholders; private bindings stay in ignored `references/source-registry.local.json` and `references/repos.local.txt`.
- [ContextEnvelope contract](references/context-envelope.md): retained for consumers that require a formal `cometweb.context/v2` payload. Ordinary answers do not need an envelope. Its fields and semantics are unchanged.
- [Privacy and provenance](references/security-and-provenance.md): source sensitivity, currentness and disclosure limits. A context snapshot is not an Evidence Pack; `evidence-researcher` owns claim-evidence admission.

Run from the repository root:

```bash
python3 resources/context/scripts/context_plan.py "<goal>" --context-scope public_example --json
python3 resources/context/scripts/repo_snapshot.py --context-scope public_example --json
python3 resources/context/scripts/validate_context_envelope.py <context-envelope.json>
```

The planner suggests source groups; it does not retrieve them. The snapshot reads local Git state, not deployed code or effective provider settings. Public-example mode skips workspace inspection and private overlays. For one project use `project_context`, a declared project reference and exactly one snapshot `--repo`; only `workspace_private` loads private overlays. See the contract for CLI options.

Helpers are read-only. Schema validation checks supplied fields and classifications, not factual truth, free-text privacy, actual permissions or publication approval. Missing source authority stays a gap. A plan is not implementation, a merge is not deployment, and deployment is not an outcome. Nie wklejaj pełnych prywatnych dokumentów ani sekretów do odpowiedzi, wyszukiwań lub publicznych artefaktów.

Regression checks:

```bash
uv run pytest resources/context/tests tooling/tests/test_context_resources.py tooling/tests/test_context_privacy_handoffs.py -q
uv run python tooling/run_behavior_evals.py
```
