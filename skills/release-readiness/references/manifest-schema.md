# Readiness Manifest v2 — engine 2.2 admission rules

The manifest is a declaration of assessed scope and evidence. Engine validation does
not authenticate a CI run, inspect an application, grant approval, or authorize a
deployment. `GO` is valid only for the declared candidate, context and `as_of`.

Generate a skeleton with `scripts/bootstrap_manifest.py`; required gates start as
`unknown`, evidence stays empty, and unknown risk flags are never assumed `no`.
The stricter admission rules in skill 1.1.0 deliberately invalidate some former
false-green manifests. Do not fill missing fields from guesses to regain `GO`.

## What the engine enforces

Artifact identity; scope completeness; profile/risk-derived required gates;
risk-tier mode floor; evidence admissibility; governance gates; risk-tier threshold
floors; blocker precedence; controlled-risk and accepted-risk rules; immutable
snapshot hash; revalidation triggers. Use its output as the default authority: if
evidence changes, update the manifest and re-run rather than overriding the result.

`scope.commercial` is the canonical key. `scope.commercial_model` is accepted as an
alias for manifests written from older instructions; supplying both with different
values is rejected.

Any other key under `scope` is not read. The engine reports each one in
`scope_warnings` (`code: unknown_scope_key`, the `key`, a `message`, and a
`suggestion` when a known key is close, e.g. `comercial` → `commercial`,
`governance_surface` → `governance_surfaces`). A risk flag written directly under
`scope` is reported with the suggestion `risk_flags.<flag>`. Warnings never change
the verdict or the contract hash: a misspelled required answer already reads as
unresolved. Fix every warning before relying on the result: a misspelled
`governance_surfaces` drops a routed governance gate. The bootstrapper rejects
these keys instead of warning.

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

## Field reference

Every key the engine reads. Values are compared lower-cased and trimmed.

```text
manifest_version      integer 2
profile               saas_web | api_service | mobile_app | desktop_app | internal_tool | oss_library | generic
mode                  fast | standard | deep
release               id, environment, as_of, commit_sha, image_digest, artifact_id,
                      build_number, config_digest, tag, deployment_id
scope                 audience, commercial, commercial_model, risk_flags,
                      governance_surfaces, risk_assessment_complete, notes
risk_flags            {flag: yes | no | unknown}
checks[]              id, domain, gate, title, owner, notes, status, severity, binding,
                      applicable, evidence_level, required_evidence, freshness, weight,
                      na_reason, evidence, control_owner, mitigation, control_due,
                      risk_acceptance
evidence              summary, candidate_ref, environment, last_verified_at, observed_at,
                      expires_at, config_digest, source_type, location
candidate_ref         commit_sha | image_digest | artifact_id | build_number | id | tag |
                      deployment_id | environment | config_digest (object), or ID string/list
risk_acceptance       approved_by, owner, rationale, mitigation, expires_at, status,
                      approval_status, approved
governance_gates[]    surface, status, evidence, rationale, control_owner, control, control_due
domain_weights        {domain: number >= 0}
thresholds            go_score, conditional_score, min_coverage (0-100; floors per risk tier)
```

`domain` is `product | qa | security | ops | docs | billing | support`. `gate` is one
of the canonical gate families: `release_scope_acceptance`, `candidate_verification`,
`security_release`, `release_delivery`, `recovery_strategy`, `observability`,
`operator_docs`, `consumer_docs`, `support_path`, `billing_entitlements`,
`billing_state_transitions`, `auth_access_control`, `migration_integrity`,
`sensitive_data_handling`, `api_compatibility`, `infra_resilience`, `store_delivery`,
`incident_regression`, `ai_safety_behavior`. Defaults: `status` `unknown`, `severity`
`major`, `binding` false, `applicable` true, `evidence_level` `missing`,
`required_evidence` `verified` when binding and `supported` otherwise, `freshness`
`unknown`, `weight` by severity. A governance gate's `status` defaults to
`counsel_required`; its mitigation key is `control` (a check uses `mitigation`).
`approval_status` is an alias of `risk_acceptance.status` with the same values.
`source_type` and `location` are recorded for reviewers; the engine does not read them.
A string `evidence` is read as its `summary`.

The bootstrapper's `--context` file takes `profile`, `mode`, `release` and `scope`
with the same rules, and rejects unknown scope keys.

## Candidate identity

`release` needs a nonempty `id`, a nonempty `environment` (any exact string; evidence must repeat it verbatim), an explicit-offset ISO
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
Unknown flag names are rejected, so a typo cannot silently conceal new scope; the
error names the closest valid flag.

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

Check `status`: `pass | pass_with_controls | accepted_risk | fail | unknown | na`.
`severity`: `blocker | critical | major | minor`.
`evidence_level` and `required_evidence`: `missing | claimed | supported | verified`.
`freshness`: `current | stale | mismatched | unknown`.

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

`evidence_issues` lists the reasons a positive or binding check was not admitted:
`evidence_summary_missing`, `observation_time_missing_or_invalid`,
`observation_times_conflict`, `observation_after_assessment`, `expiry_invalid`,
`evidence_expired`, `expiry_before_observation`,
`candidate_binding_missing_or_mismatched`, `environment_missing_or_mismatched`,
`configuration_missing_or_mismatched`, `environment_mismatched`.

## Controls, risk acceptance, and governance

A controlled pass needs nonempty string `control_owner` and `mitigation`, plus
`control_due` strictly after `as_of`. Null does not mean an owner exists.

Accepted risk is limited to nonbinding `major`/`minor`. Its `risk_acceptance`
object requires nonempty string `approved_by`, `owner`, `rationale`, `mitigation`,
and an unexpired `expires_at`. Optional `status` or `approval_status`, when
present, must be `approved` or `granted`; optional `approved`, when present, must
be the boolean `true`. A named approver next to `pending`, `requested` or `denied`
is a request, not an acceptance. These records are declarations, not proof of the
approver's authority. Accepted risk cannot clear a binding/blocker/critical issue.

A controlled pass or accepted risk whose control or acceptance is not in force
(missing owner, past due, pending, denied, expired, or inadmissible evidence) is
listed in `unresolved_conditions` and defers the release at any severity. Before
engine 2.2 a minor one read as an ordinary unknown and could yield an
unconditional `GO`, ranking above the same check recorded properly.

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

## Result keys

```text
verdict               GO | GO_WITH_CONTROLS | NO_GO | DEFER
reason                the decisive conditions, joined by "; "
check_states          {check id: effective_status after evidence admission}
gating_metrics        unrounded readiness_score and evidence_coverage used by the gate
readiness_score       display score, one decimal
evidence_coverage     display coverage, one decimal
required_gates        gate families derived from profile and scope
missing_required_gates
scope_gaps            unresolved scope answers (audience, commercial, risk flags, ...)
scope_warnings        unread scope keys: code, key, message, suggestion
binding_unknowns      binding checks without admissible evidence
blocking_failures     failed binding or blocker/critical/major checks
unresolved_conditions controls or risk acceptances not in force
contract_hash         normalized requirements fingerprint
contract_mismatch     true when --expected-contract-hash differs
snapshot_hash         manifest fingerprint
```

`effective_status` uses the check `status` values; an unproven positive claim becomes
`unknown`. With `--previous`, the delta adds `resolved_blockers`, `removed_blockers`,
`blockers_no_longer_proven_resolved`, `changed_check_requirements` and
`no_longer_required_gates`.
