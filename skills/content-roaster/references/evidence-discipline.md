# Content Roaster evidence discipline

## Evidence states

- `OBSERVED`: directly present in the reviewed artifact.
- `MISSING`: an expected element is absent **and the reviewed scope is sufficient to establish the omission**.
- `INFERRED`: a bounded interpretation derived from observed material; include `inference_basis`.
- `VERIFY_EXTERNAL`: truth requires evidence outside the artifact; do not convert this into a factual verdict.

`MISSING` requires `omission_basis` explaining why the inspected scope is sufficient. A search miss is not enough.

## Evidence strength

- `STRONG`: direct, unambiguous source evidence or a proved omission with sufficient scope.
- `MODERATE`: credible but incomplete, context-dependent, or partly inferential evidence.
- `WEAK`: plausible concern with material uncertainty; cannot support BLOCKER.

## Scope sensitivity

- `LOW`: unseen content is unlikely to reverse the finding.
- `MEDIUM`: unseen content could narrow consequence/severity.
- `HIGH`: unseen content could reasonably reverse the finding.

`HIGH` scope sensitivity cannot have `high` confidence. BLOCKER cannot use `HIGH` scope sensitivity.

## Claim types and proof burden

| Claim type | Typical burden | Notes |
| --- | --- | --- |
| `SUBJECTIVE` | LOW-MEDIUM | Still needs internal coherence; no external truth implied. |
| `FACTUAL` | MEDIUM-HIGH | Verify externally when artifact is not the source of truth. |
| `MECHANISM` | MEDIUM-HIGH | Needs enough explanation/evidence for the requested commitment. |
| `QUANTITATIVE` | HIGH-VERY_HIGH | Needs source, denominator, population/time boundary where material. |
| `COMPARATIVE` | HIGH-VERY_HIGH | Needs comparator definition and comparable basis. |
| `OUTCOME` | HIGH-VERY_HIGH | Needs evidence linking product/service to claimed outcome. |
| `GUARANTEE` | VERY_HIGH | Must be precisely scoped and supportable. |

A claim that is unproved in the artifact is not automatically false. Use proof debt or external verification.

## Materiality

Each finding declares:

- `centrality`: `CENTRAL`, `SUPPORTING`, or `LOCAL`;
- `consequence`: `HIGH`, `MEDIUM`, or `LOW`;
- `reversibility`: `EASY`, `MODERATE`, `HARD`, or `UNKNOWN`.

This is not a score. It exists to prevent severity from being driven by wording preference.

## Proof debt

Use the proof-debt ledger only for claims whose evidence burden matters to reader action.

Debt types:

- `ABSENT_PROOF`
- `WEAK_PROOF`
- `MISMATCHED_PROOF`
- `EXTERNAL_VERIFICATION`
- `OVERCLAIM`

Status:

- `OPEN`
- `PARTIAL`
- `CLOSED`
- `NOT_APPLICABLE`

Do not create proof debt for purely subjective brand language unless it masquerades as an objective claim.

## Source lineage

Every structured claim/finding anchor must include `source_id` referencing `source_manifest`. This keeps evidence traceable when multiple artifacts, revisions, supplements, logs, or repository snapshots are reviewed together. A locator without source identity is not sufficient for machine handoff.
