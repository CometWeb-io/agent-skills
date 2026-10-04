# Bounded contract tracing

`contract-trace` is a bounded mode for one named `journey_id` across:

`UI -> API -> authorization -> service -> DB/queue/job -> durable UI state`

It requires all five scenario kinds: `happy`, `null_partial`,
`retry_duplicate`, `wrong_tenant`, and `rollback`. Each scenario is `pass`,
`fail`, `unknown`, or `blocked`; missing or unresolved scenarios make the
trace incomplete.

Browser evidence proves only browser-visible edges. Backend, authorization,
queue, database, and durable-state claims require joined runtime evidence with
matching revision, build, environment, and correlation identity. Never call
browser-only evidence full E2E proof.

The sidecar records `nodes`, `edges`, `evidence_ids`, and scenario `status`.
Every evidence row needs a stable `locator`. Evidence `channel` is `browser`, `backend`, or `joined`; `backend` is not
browser proof and must be joined to a pinned runtime artifact for a cross-layer
claim.

Validate the sidecar with:

```bash
python3 scripts/contract_trace_kernel.py contract-trace.json
```

The validator checks graph references, evidence channels, scenario accounting,
and bounded claims. It does not authenticate evidence or issue a release
verdict. Hand off incomplete traces to Release Readiness as unresolved
evidence, never as a clean gate.
