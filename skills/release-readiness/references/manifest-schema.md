# Readiness Manifest v2

The deterministic engine accepts one JSON object with `manifest_version: 2`. Prefer generating the initial skeleton with `scripts/bootstrap_manifest.py` so profile/risk-derived required gates are not omitted. The bootstrapper creates `UNKNOWN` placeholders only; it never creates passing evidence.

## Minimal complete SaaS example

```json
{
  "manifest_version": 2,
  "profile": "saas_web",
  "mode": "standard",
  "release": {
    "id": "v2.4.0",
    "commit_sha": "abc1234",
    "environment": "production",
    "as_of": "2026-08-25T22:00:00+02:00"
  },
  "scope": {
    "audience": "external",
    "commercial": "free",
    "risk_assessment_complete": true,
    "governance_surfaces": [],
    "risk_flags": {
      "first_production_release": "no",
      "auth_change": "no",
      "billing_change": "no",
      "schema_or_data_migration": "no",
      "sensitive_data_change": "no",
      "public_api_breaking_change": "no",
      "major_infra_change": "no",
      "mobile_store_release": "no",
      "incident_recovery_release": "no",
      "high_impact_ai_change": "no",
      "legal_or_regulatory_change": "no"
    }
  },
  "checks": [
    {
      "id": "qa.critical-path",
      "gate": "candidate_verification",
      "domain": "qa",
      "title": "Critical path passes on release candidate",
      "status": "pass",
      "severity": "critical",
      "binding": true,
      "evidence_level": "verified",
      "required_evidence": "verified",
      "freshness": "current",
      "evidence": {
        "summary": "CI run 4812 passed critical E2E",
        "candidate_ref": "abc1234",
        "last_verified_at": "2026-08-25T21:55:00+02:00",
        "source_type": "ci"
      }
    }
  ],
  "governance_gates": []
}
```

The example shows shape only. A real manifest must include every required baseline and conditional gate.

## Top-level fields

### `manifest_version`

Required. Must equal `2`.

### `profile`

Required:

- `saas_web`
- `api_service`
- `mobile_app`
- `desktop_app`
- `internal_tool`
- `oss_library`
- `generic`

### `mode`

Required by convention, defaulted by engine to `standard`:

- `fast`
- `standard`
- `deep`

Risk tier can force a higher minimum mode.

## Release object

Required for unconditional verdict:

- `id`;
- `environment`;
- `as_of` parseable ISO timestamp;
- one artifact identity: `commit_sha`, `artifact_id`, `image_digest`, or `build_number`.

Optional:

- `branch`;
- `tag`;
- `deployment_id`;
- `base_sha`;
- `change_summary`.

## Scope object

### Required semantic fields

`audience`:

- `external`
- `internal`
- `library_consumers`
- `unknown`

`commercial`:

- `paid`
- `free`
- `not_applicable`
- `unknown`

`risk_assessment_complete`: boolean. Must be `true` for unconditional verdict.

`governance_surfaces`: zero or more of:

- `legal`
- `privacy`
- `financial_risk`
- `responsible_ai`
- `reputation`
- `platform_policy`

### `risk_flags`

Every field must resolve to `yes | no | unknown`:

- `first_production_release`
- `auth_change`
- `billing_change`
- `schema_or_data_migration`
- `sensitive_data_change`
- `public_api_breaking_change`
- `major_infra_change`
- `mobile_store_release`
- `incident_recovery_release`
- `high_impact_ai_change`
- `legal_or_regulatory_change`

Missing flag defaults to `unknown`, which creates a scope gap and normally yields `DEFER`.

## Check object

Required:

- `id`: unique stable ID;
- `domain`: `product | qa | security | ops | docs | billing | support`;
- `status`: `pass | pass_with_controls | accepted_risk | fail | unknown | na`;
- `severity`: `blocker | critical | major | minor`.

Strongly recommended / conditionally required:

- `gate`: canonical gate family if satisfying a required gate;
- `binding`: defaults false;
- `applicable`: defaults true;
- `weight`: positive number, otherwise severity default;
- `evidence_level`: `verified | supported | claimed | missing`;
- `required_evidence`: default `verified` for binding, else `supported`;
- `freshness`: `current | stale | mismatched | unknown`;
- `evidence`: structured object;
- `owner`;
- `mitigation`;
- `na_reason` for N/A.

### Structured evidence

```json
{
  "summary": "what was observed",
  "candidate_ref": "commit/build/digest/release id",
  "last_verified_at": "ISO timestamp",
  "expires_at": "optional ISO timestamp",
  "environment": "optional environment",
  "source_type": "ci/runtime/repo/provider/docs/dashboard/ticket/human",
  "location": "optional evidence pointer"
}
```

Binding `PASS/PASS_WITH_CONTROLS` requires structured evidence summary and timestamp. When `required_evidence=verified`, candidate reference must match release identity.

## Controlled pass

Use only if the control actually makes the release condition acceptable.

Required:

```json
{
  "status": "pass_with_controls",
  "control_owner": "owner/team",
  "mitigation": "specific compensating control",
  "control_due": "future ISO timestamp/date"
}
```

Expired/missing control metadata downgrades the effective state to unknown.

## Accepted risk

Use only for non-binding `major` or `minor` risk. Never use for binding/blocker/critical.

```json
{
  "status": "accepted_risk",
  "risk_acceptance": {
    "approved_by": "authorized approver",
    "owner": "risk owner",
    "rationale": "why release proceeds",
    "mitigation": "what limits impact",
    "expires_at": "future ISO timestamp",
    "ticket": "optional decision record"
  }
}
```

A valid accepted risk can yield at most `GO_WITH_CONTROLS`.

## Governance gate object

```json
{
  "surface": "privacy",
  "status": "clear_with_controls",
  "evidence": {
    "summary": "current review basis"
  },
  "control_owner": "owner",
  "control": "specific constraint",
  "control_due": "future ISO timestamp"
}
```

Statuses:

- `not_required`
- `clear`
- `clear_with_controls`
- `counsel_required`
- `block`

`not_required` requires `rationale` when supplied as an explicit gate. `clear` requires evidence summary. `clear_with_controls` requires evidence + control metadata.

## Canonical gate families

- `release_scope_acceptance`
- `candidate_verification`
- `security_release`
- `release_delivery`
- `recovery_strategy`
- `observability`
- `operator_docs`
- `consumer_docs`
- `support_path`
- `billing_entitlements`
- `billing_state_transitions`
- `auth_access_control`
- `migration_integrity`
- `sensitive_data_handling`
- `api_compatibility`
- `infra_resilience`
- `store_delivery`
- `incident_regression`
- `ai_safety_behavior`

See `risk-routing.md` for which gates are required.

## Domain weights

Optional. Defaults:

```json
{
  "product": 15,
  "qa": 20,
  "security": 20,
  "ops": 20,
  "docs": 10,
  "billing": 8,
  "support": 7
}
```

Domains with no applicable checks are excluded and weights are re-normalized. N/A never earns points.

## Thresholds

Optional overrides may only make policy stricter. Risk-tier floors cannot be lowered.

```json
{
  "thresholds": {
    "go_score": 96,
    "conditional_score": 92,
    "min_coverage": 99
  }
}
```

Floors:

| Tier | GO | Conditional | Coverage |
| --- | ---: | ---: | ---: |
| R1 | 88 | 78 | 90 |
| R2 | 92 | 84 | 95 |
| R3 | 95 | 90 | 98 |

## Engine output highlights

- `verdict`
- `risk_tier`
- `required_mode_floor`
- `readiness_score`
- `evidence_coverage`
- `scope_gaps`
- `required_gates`
- `missing_required_gates`
- `required_governance_surfaces`
- `missing_governance_gates`
- `binding_failures`
- `binding_unknowns`
- `blocking_failures`
- `controlled_risks`
- `accepted_risks`
- `evidence_downgrades`
- `snapshot_hash`
- `revalidation_triggers`
- optional `delta` when `--previous` is supplied.
