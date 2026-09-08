# Evidence Model v2

## Principle

Roadmap quality cannot exceed claim quality. Keep the chain explicit:

`source -> evidence row -> claim -> capability/gap -> roadmap item -> acceptance proof`

Never jump directly from a file, issue, or intuition to a priority.

## Claim schema

Use stable claim IDs. Material claims should include:

```json
{
  "claim_id": "C-014",
  "text": "Primary checkout path enforces entitlement after payment",
  "claim_lane": "implementation",
  "claim_type": "behavior",
  "materiality": "high",
  "current_sensitive": false,
  "evidence": []
}
```

Allowed lanes:

- `implementation`
- `intent`
- `outcome`
- `operational`
- `external`

Recommended claim types:

- `presence` - an artifact/config/path exists.
- `behavior` - a flow behaves as asserted.
- `release` - code/config is actually releasable/released at the stated scope.
- `outcome` - user/business/operational outcome is observed.
- `intent` - approved desired state/decision.
- `operational` - deploy/recovery/monitoring/ownership behavior.
- `external_current` - current vendor/platform/standard/policy constraint.
- `absence` - a required capability/artifact is demonstrably absent.

## Evidence row

```json
{
  "source_ref": "github:owner/repo:path@sha#L10-L30",
  "source_type": "code",
  "direction": "support",
  "directness": "direct",
  "freshness": "NOT_TIME_SENSITIVE",
  "scope_match": "exact",
  "independence_key": "repo:path@sha",
  "fingerprint": "optional-stable-source-fingerprint"
}
```

Allowed directness:

- `direct`
- `supporting`
- `inferred`

Allowed freshness:

- `CURRENT`
- `NEAR_EXPIRY`
- `NOT_TIME_SENSITIVE`
- `STALE`
- `SUPERSEDED`
- `UNKNOWN`

Allowed scope match:

- `exact`
- `partial`
- `weak`

Use `fingerprint` when the source can be compared across delta assessments, for example commit SHA, blob SHA, CI run ID, deploy ID, document version, or external `last_verified_at` marker.

## Source authority by lane

### Implementation

Prefer runtime/test/CI/deployment evidence for behavior, code/config/migrations for presence, then change history. Documentation and intent do not prove implementation.

### Intent

Prefer explicit user requirement, approved decision, or current product context. Code can reveal de facto behavior but cannot redefine approved intent silently.

### Outcome

Prefer analytics/runtime/incidents/customer research/support depending on the claim. Code does not prove adoption, conversion, customer pain, reliability, or revenue impact.

### Operational

Prefer CI/deploy/runtime/incident/config evidence. A runbook alone proves documented intent, not operational capability.

### External

For current-sensitive claims prefer current official/primary sources. Record verification time outside the kernel when the source is time-sensitive.

## Admissibility

For `current_sensitive: true`, only `CURRENT` or `NEAR_EXPIRY` evidence may support the binding conclusion. `STALE`, `SUPERSEDED`, or `UNKNOWN` can be retained for history but must not make a current claim pass.

For non-time-sensitive repository claims pinned to a commit/ref, use `NOT_TIME_SENSITIVE`.

The kernel reports inadmissible rows separately. Do not convert an inadmissible row into a lower-confidence current fact.

## Claim-type verification rules

### Presence

Direct code/config/schema/inventory evidence can verify presence at the pinned ref.

### Behavior

Code presence alone cannot reach `VERIFIED`. Require a behavior-bearing source such as a relevant test, CI execution, runtime observation, or equivalent direct execution evidence.

### Release

Require release/deployment/runtime/CI artifact evidence appropriate to the claim. A merged PR or commit is change evidence, not release proof.

### Outcome

Require an outcome-bearing source. Do not infer user/business outcome from implementation quality.

### External current

Require admissible current official/primary evidence for material current claims.

### Absence

Use the negative-evidence protocol below. A search miss alone is not absence proof.

## Negative-evidence protocol

Before asserting `MISSING` or a material absence claim, record an `absence_check`:

```json
{
  "status": "ABSENCE_VERIFIED",
  "inventory_complete": true,
  "scopes_checked": ["apps/web", "packages/auth"],
  "dynamic_registration_checked": true,
  "generated_or_config_driven_paths_checked": true,
  "notes": "No route, handler, feature flag registration, or generated binding exists at pinned ref"
}
```

Allowed statuses:

- `ABSENCE_VERIFIED`
- `NOT_FOUND_IN_SEARCH`
- `INCOMPLETE_SEARCH`
- `UNKNOWN`

Only `ABSENCE_VERIFIED` can support a strong `absence` claim. If repository access cannot establish this, use `UNKNOWN` capability state and create `VERIFY_NOW` when material.

## Correlation and independence

Use the same `independence_key` for evidence derived from the same underlying source. If independence is unknown, keep it unknown; do not give each row fake independence.

Examples of correlated evidence:

- PR description and issue copied into the PR,
- generated documentation derived from the same source file,
- multiple tests that all mock the same unverified boundary,
- several summaries of one incident.

## Contradictions

Record contradictory evidence with `direction: contradict`.

Do not average away a material contradiction. Report `CONTESTED` when contradiction remains strong enough to affect the claim. Resolve by inspecting the source with greater authority/scope, or surface the uncertainty.

## Confidence bands

Use bands as heuristic decision support, not calibrated probabilities:

- `VERIFIED`
- `STRONG`
- `MODERATE`
- `WEAK`
- `HYPOTHESIS`

The kernel may emit a numeric heuristic score for sorting/validation. Do not present it as statistical probability.

## Evidence-to-roadmap rule

A roadmap item linked mainly to weak/hypothesis claims is allowed only when it is:

- a verification/validation item,
- an explicit user-mandated outcome,
- or a suspected material blocker clearly labeled as unverified.

Do not spend substantial implementation capacity to solve an unverified problem when a cheaper evidence step can change the decision.
