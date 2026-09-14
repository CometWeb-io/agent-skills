# Readiness Manifest v2 — engine 2.1 admission rules

The manifest is a declaration of assessed scope and evidence. Engine validation does
not authenticate a CI run, inspect an application, grant approval, or authorize a
deployment. `GO` is valid only for the declared candidate, context and `as_of`.

Generate a skeleton with `scripts/bootstrap_manifest.py`; required gates start as
`unknown`, evidence stays empty, and unknown risk flags are never assumed `no`.
The stricter admission rules in skill 1.1.0 deliberately invalidate some former
false-green manifests. Do not fill missing fields from guesses to regain `GO`.

## Root contract

The input is one JSON object, at most 4 MiB. Duplicate keys, non-finite numbers,
non-JSON native values and excessive nesting are invalid. `manifest_version` must
be integer `2`, not `2.0` or a boolean.

`profile`: `saas_web | api_service | mobile_app | desktop_app | internal_tool |
oss_library | generic`. Default: `generic`.

`mode`: `fast | standard | deep`. Default: `standard`; risk flags can force a
higher floor. `checks` must be a nonempty array. `governance_gates` is an array,
empty only when no routed surface requires one. Optional `domain_weights` and
`thresholds` may not disable the hard gates.

## Candidate identity

`release` needs a nonempty `id`, a known `environment`, an explicit-offset ISO
`as_of`, and at least one immutable identity below. Null, booleans, objects and
placeholder strings are not identities. Optional malformed identity fields create
an identity gap even when another valid identity exists.

| Field | Admitted identity |
| --- | --- |
| `commit_sha` | Full 40- or 64-character lowercase hexadecimal object ID; resolve abbreviated IDs before assessment |
| `image_digest` | Complete `sha256:` or `sha512:` digest, not an image tag |
| `artifact_id` | Exact nonempty identifier of an immutable artifact in the system of record |
| `build_number` | Exact nonempty string or nonnegative integer, scoped by the release system and environment |
| `config_digest` | Optional exact configuration fingerprint; when supplied, verified evidence must carry it too |

An artifact ID/build number is not proven immutable merely because it parses.
The evidence collector is responsible for verifying that property. Branch, tag,
deployment ID and release name are descriptive fields, not substitutes for a
missing immutable identity. No prefix match is used.

All temporal fields use `YYYY-MM-DDTHH:MM:SS[.fraction]Z` or an explicit `+HH:MM`
offset. Bare dates and naive timestamps are inadmissible; the engine does not
silently assume UTC. Future assessments are deferred. Historical assessments
remain historical and must not be sold as current permission to release.

## Scope and required gates

`scope.audience`: `external | internal | library_consumers | unknown`.
`scope.commercial`: `paid | free | not_applicable | unknown`.
`scope.risk_assessment_complete` must be the boolean `true` for an unconditional
verdict. Each risk flag below is `yes | no | unknown`; missing flags stay unknown.
Unknown flag names are rejected, so a typo cannot silently conceal new scope.

```text
first_production_release       auth_change
billing_change                 schema_or_data_migration
sensitive_data_change          public_api_breaking_change
major_infra_change             mobile_store_release
incident_recovery_release      high_impact_ai_change
legal_or_regulatory_change
```

Profile and risk flags derive the required gate families; a required family needs
applicable binding members. Governance surfaces are `legal`, `privacy`,
`financial_risk`, `responsible_ai`, `reputation`, and `platform_policy`.
See `risk-routing.md` and `domain-checks.md` for domain interpretation. Do not
misclassify flags or remove checks merely to improve the result.

## Check and evidence contract

Checks have a stable string `id`, canonical `domain`, optional canonical `gate`,
`title`, `severity`, `status`, and evidence. `binding`/`applicable` must be real
booleans; `"false"`, `0`, and `1` are not accepted booleans.

Statuses: `pass | pass_with_controls | accepted_risk | fail | unknown | na`.
Severities: `blocker | critical | major | minor`.
Evidence levels: `missing | claimed | supported | verified`.
Freshness: `current | stale | mismatched | unknown`.

The minimum required evidence is engine-owned. Binding `operator_docs`,
`consumer_docs` and `support_path` can use `supported`; other canonical binding
gates require `verified`. A requested weaker level is raised to the floor, not
accepted as an escape hatch. Higher user requirements remain effective.

Every positive assessed status needs a nonempty evidence summary, admissible
observation time, required evidence level and current freshness. This includes
nonbinding material checks and accepted risk; relabeling a check nonbinding does
not turn an unsupported positive claim into a verified closure.

For verified binding evidence, `environment` is mandatory and must exactly match
the release. If multiple immutable identities are pinned, all must match.

```json
{
  "summary": "Describe the actual observation and its limits",
  "candidate_ref": {
    "commit_sha": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "artifact_id": "example-immutable-build-artifact"
  },
  "environment": "production",
  "last_verified_at": "2026-09-12T17:00:00Z",
  "source_type": "ci",
  "location": "Pointer to the actual artifact in the authorized system"
}
```

This is a shape example, not real evidence. A scalar `candidate_ref` can bind a
single immutable ID; a list must cover every pinned ID without conflicting
entries. A structured object is preferred for multiple fields. A matching release
name plus a mismatching commit does not pass. Explicitly supplied mismatching
context also invalidates otherwise-supported static evidence.

`last_verified_at` and `observed_at` are aliases only when they identify the same
instant. If both are supplied and disagree, neither is cherry-picked. Observation
must not be after `as_of`. Optional `expires_at`, when present, must parse and be
strictly after the assessment and observation. An invalid expiry is not ignored.

`evidence_issues` lists reasons such as `environment_missing_or_mismatched`,
`candidate_binding_missing_or_mismatched`, and `expiry_invalid`.

## Controls, risk acceptance, and governance

A controlled pass needs nonempty string `control_owner` and `mitigation`, plus
`control_due` strictly after `as_of`. Null does not mean an owner exists.

Accepted risk is limited to nonbinding `major`/`minor`. Its `risk_acceptance`
object requires nonempty string `approved_by`, `owner`, `rationale`, `mitigation`,
and an unexpired `expires_at`. These records are declarations, not proof of the
approver's authority. Accepted risk cannot clear a binding/blocker/critical issue.

`na` needs a substantive nonempty `na_reason`; not tested means `unknown`.

Governance states remain `not_required | clear | clear_with_controls |
counsel_required | block`. `clear`/`clear_with_controls` need a nonempty summary
and admissible current timestamps. Supplied contradictory candidate/environment
references are rejected. Required surfaces cannot be cleared as `not_required`.
`block` still has precedence over scores and other missing information.

## Scoring and uncertainty

Weights must be finite; check weights must be positive. Domain weights can be
nonnegative, with a positive active total. Large finite weights are normalized
before arithmetic. NaN and infinity cannot turn comparisons into false positives.

Display values retain one decimal place, but decisions compare unrounded metrics.
For example, coverage `89.99` cannot pass a `90` floor because it displays as
`90.0`. Read `gating_metrics` for the quantities used by the gate.

An unverified blocker/critical/major finding defers the result even when it is
nonbinding or its domain has zero scoring weight. Binding and governance failures
are never averaged away.

| Risk tier | GO floor | Conditional floor | Coverage floor |
| --- | ---: | ---: | ---: |
| R1 | 88 | 78 | 90 |
| R2 | 92 | 84 | 95 |
| R3 | 95 | 90 | 98 |

## Frozen requirements and truthful deltas

The result's `contract_hash` fingerprints normalized scope, check requirements,
mode, domain weights and thresholds, excluding status/evidence observations.
Keep an independently stored hash before gathering new evidence:

```bash
python scripts/readiness_engine.py --input readiness.json \
  --expected-contract-hash '<independently-stored-sha256>' --ci-policy strict
```

Changing requirements yields `DEFER` unless a known blocker already demands
`NO_GO`. A hash supplied by the same party as a changed manifest is not an
independent approval. It must come from the reviewed scope contract.

`--previous` freezes to the previous manifest's contract by default. Deliberate
scope changes require a separately reviewed new hash via `--expected-contract-hash`.
They remain scope changes in the delta; they do not count as fixes.

A removed, weakened, excluded, or newly-unverified blocker is not listed in
`resolved_blockers`. The result separates `removed_blockers`,
`blockers_no_longer_proven_resolved`, and `changed_check_requirements`.
A missing gate added as unknown is present, not resolved. A risk flag turned off
moves its gate to `no_longer_required_gates`, not to resolved gates.

Changed requirements, environment or configuration suppress numerical deltas
(`scores_comparable: false`, `score_delta: null`, `coverage_delta: null`).
Different environments/configurations cannot provide closure for the old context.
Reversed assessment chronology is rejected.

`snapshot_hash` fingerprints the manifest; it is distinct from `contract_hash`.
Output states `assessment_basis: declared_manifest`,
`evidence_authentication: not_performed`, and
`deployment_authorization: not_provided`. These boundaries also apply to `GO`.
