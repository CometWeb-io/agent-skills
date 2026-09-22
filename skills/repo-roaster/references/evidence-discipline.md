# Repo Roaster evidence discipline

## Evidence states

- `OBSERVED_CODE`: directly observed source code.
- `OBSERVED_CONFIG`: directly observed configuration/build/infra material.
- `OBSERVED_TEST`: directly observed test or test result.
- `OBSERVED_HISTORY`: commit/diff/history evidence.
- `OBSERVED_RUNTIME`: direct reproduction or runtime behavior.
- `OBSERVED_LOG`: direct log/trace evidence.
- `OBSERVED_METRIC`: direct metric/telemetry evidence.
- `NOT_FOUND`: a material element was not found after a scope-sufficient absence search; requires `absence_proof`.
- `INFERRED`: bounded engineering interpretation; requires `inference_basis`.

Unverified questions belong in `verification_gaps`, not the defect list.

## Evidence strength

- `STRONG`: direct runtime/test evidence or a complete, well-bounded source/config path with little inferential distance.
- `MODERATE`: credible static/cross-file evidence with some runtime/config uncertainty.
- `WEAK`: plausible concern with substantial uncertainty; cannot support CRITICAL.

## Scope sensitivity

- `LOW`: unseen repository/runtime material is unlikely to reverse the finding.
- `MEDIUM`: unseen guards/config/deployment details could narrow severity.
- `HIGH`: unseen evidence could reasonably reverse the finding.

`HIGH` scope sensitivity cannot have high confidence. CRITICAL cannot use `HIGH` scope sensitivity.

## Reachability

- `PROVEN`: test/runtime/trace/log or a complete source execution path reaches the risky effect.
- `PLAUSIBLE`: a concrete source path exists but runtime execution was not directly observed.
- `STATIC_ONLY`: risky code/config exists but active reachability is not established.
- `UNKNOWN`: evidence is insufficient.

CRITICAL requires `PROVEN` or `PLAUSIBLE` and a non-empty execution path.

## Absence proof

`NOT_FOUND` requires:

- `searched_scope`: what was examined;
- `queries_or_locations`: searches, directories, manifests, or call sites inspected;
- `sufficiency_basis`: why that scope is enough for the bounded absence claim.

A single grep miss is never sufficient by itself for a material absence claim.

## Materiality

Each finding declares:

- `centrality`: `CENTRAL`, `SUPPORTING`, or `LOCAL` relative to a critical path/invariant;
- `consequence`: `HIGH`, `MEDIUM`, or `LOW`;
- `reversibility`: `EASY`, `MODERATE`, `HARD`, or `UNKNOWN`.

This does not replace reachability or blast radius. It prevents aesthetic code critique from being promoted into engineering risk.

## CRITICAL admission

CRITICAL requires:

- evidence strength `STRONG` or `MODERATE`;
- scope sensitivity `LOW` or `MEDIUM`;
- reachability `PROVEN` or `PLAUSIBLE`;
- non-empty `execution_path`;
- non-low confidence;
- known blast-radius class;
- link to a critical invariant, critical path, or trust-boundary surface;
- an engineering consequence consistent with security-boundary failure, cross-tenant exposure, irreversible material data loss/corruption, or systemic production failure.

## Source lineage

Every structured claim/finding anchor must include `source_id` referencing `source_manifest`. This keeps evidence traceable when multiple artifacts, revisions, supplements, logs, or repository snapshots are reviewed together. A locator without source identity is not sufficient for machine handoff.
