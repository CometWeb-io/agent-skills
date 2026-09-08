# Target State Profiles

## Purpose

Anchor the roadmap to an explicit definition of "done enough". Profiles are planning defaults, not universal standards. Override them with explicit product constraints and mark irrelevant domains `NOT_APPLICABLE` with rationale.

## Profiles

### PROTOTYPE

Optimize for proving the core idea. Usually require:

- one demonstrable core journey,
- reproducible local/test execution,
- enough data handling to avoid misleading results,
- known limitations and non-goals.

Do not import production controls merely because they are good practice.

### INTERNAL_BETA

Add:

- stable critical journeys for internal users,
- basic failure visibility,
- repeatable deployment/test path,
- access boundaries appropriate to internal use,
- feedback capture.

### PUBLIC_BETA

Add, when applicable:

- explicit auth/session/permission behavior,
- safer data lifecycle and migrations,
- runtime observability and incident response path,
- release/rollback confidence,
- user-facing error states,
- privacy/security review of exposed surfaces,
- support/feedback intake.

### CLIENT_READY

Use when a real client must be able to rely on the product. Add, when applicable:

- verified client-critical journeys,
- deterministic environment/configuration setup,
- access/tenant/data boundaries,
- operational ownership and escalation path,
- backup/recovery or equivalent state-protection controls,
- documentation/runbooks sufficient for delivery/support,
- clear product limitations,
- acceptance evidence for promised capabilities.

### PAID_PRODUCTION

Use when customers pay for a live service. Add, when applicable:

- verified billing/entitlement lifecycle,
- release and rollback controls,
- data integrity/migration/recovery posture,
- security/privacy controls appropriate to exposure,
- production observability and alerting,
- support/incident operations,
- critical journey verification in production-like conditions,
- instrumentation for the commercial/product outcomes that matter.

### SCALE_READY

Use only when scaling pressure is part of the target. Add evidence for:

- capacity/performance constraints,
- failure isolation and recovery,
- operational toil/bottlenecks,
- deployment throughput/stability,
- ownership and runbook maturity,
- architecture limits that are actually approaching, not hypothetical.

### CUSTOM

Define requirements directly from the user's explicit target state.

## Target State Contract

Create stable requirement IDs:

```json
{
  "target_profile": "PAID_PRODUCTION",
  "requirements": [
    {
      "id": "T-001",
      "domain": "core_flow",
      "requirement": "Paid customer can complete the primary workflow end-to-end",
      "mandatory": true,
      "applicability": "APPLIES",
      "source": "explicit_user_goal"
    }
  ]
}
```

Allowed applicability:

- `APPLIES`
- `NOT_APPLICABLE`
- `UNKNOWN`

A mandatory requirement with `UNKNOWN` applicability is a verification gap, not an automatic blocker.
