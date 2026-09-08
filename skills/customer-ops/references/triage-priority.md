# Triage, Priority, Aging, and Queue Ordering

## Contents

1. Decision axes
2. Two-pass triage
3. Risk gates
4. Fallback operational priority
5. Account escalation
6. Evidence grade
7. Queue ordering
8. Aging and blocked work
9. Re-triage triggers
10. Dedupe and queue hygiene

## 1. Decision axes

Keep these separate:

- `customer_impact_severity` — incident-level impact when coordinated incident exists.
- `operational_priority` — execution order for a case/problem.
- `evidence_grade` — strength/currentness of proof.
- `retention_risk` — account churn/non-renewal operational risk.
- `account_escalation` — relationship/commercial attention.
- `sla/deadline_state` — authoritative timing state.

Never infer one directly from another.

## 2. Two-pass triage

For a large queue:

### Pass 1 — inventory

Capture cheap metadata across the full available scope:

```text
source id
account/contact id if available
opened/last activity
provider state
native priority/SLA if present
owner
subject/short symptom
linked incident/engineering ids
```

Do not read every long thread first if doing so prevents queue coverage.

### Pass 2 — deep read

Read full evidence for:

- incident candidates,
- security/privacy/data-loss/legal/fraud/financial-harm signals,
- native SLA breached/near-breach,
- P0/P1 candidates,
- explicit cancellation/non-renewal/switch intent,
- overdue commitments,
- stalled/ownerless handoffs,
- ambiguous identity/dedupe,
- cases needed to establish an emerging cluster.

If the connector cannot provide the complete queue, label coverage `PARTIAL`.

## 3. Risk gates

Before ordinary priority ranking, flag:

- broad service unavailability or coordinated incident candidate,
- customer data loss/corruption,
- suspected unauthorized access/credential exposure,
- privacy/confidentiality exposure,
- legal/regulatory demand,
- fraud/material financial harm,
- customer safety harm where relevant,
- public/reputational escalation that needs specialist handling.

A gate means **special handling is required**, not that every allegation is confirmed.
Preserve original evidence and route to the specialist owner.

## 4. Fallback operational priority

Use the organization's documented priority policy first. When none exists, use this
fallback. The kernel implements the same fallback deterministically.

### Dimensions `0..4`

#### `impact`

- `0` — informational/no meaningful customer harm.
- `1` — nuisance/cosmetic/minor friction.
- `2` — meaningful secondary workflow blocked/degraded.
- `3` — core workflow materially blocked/degraded.
- `4` — critical ongoing harm/outage-like failure/material data-integrity impact.

#### `urgency`

- `0` — no action deadline/current harm.
- `1` — low urgency.
- `2` — normal operational urgency.
- `3` — time-sensitive/customer work materially blocked now.
- `4` — immediate active harm/critical deadline/rapidly worsening state.

#### `breadth`

- `0` — unknown/unconfirmed.
- `1` — one user.
- `2` — one account/team.
- `3` — multiple independent accounts/meaningful segment.
- `4` — broad/systemic/global.

#### `recurrence`

- `0` — unconfirmed/one-off.
- `1` — isolated repeat.
- `2` — repeated same account/workflow.
- `3` — repeated across accounts/time.
- `4` — rapidly growing/systemic/regression pattern.

#### `workaround`

Higher means worse:

- `0` — easy, safe, verified workaround.
- `1` — usable workaround with minor cost.
- `2` — costly/partial workaround.
- `3` — weak/unreliable workaround.
- `4` — no safe viable workaround.

### Base priority

Use impact/urgency first, then modifiers.

- `P0` — rare; immediate coordination/work displacement justified.
- `P1` — urgent, actively owned/progressed.
- `P2` — normal planned operational work; age visibly.
- `P3` — low urgency/backlog/informational.

Fallback rules:

1. `P0` only when `impact=4`, `urgency=4`, `workaround>=3`, and either
   `breadth>=3` or `recurrence=4`.
2. Otherwise `impact=4` or (`impact>=3` and `urgency>=3`) starts at `P1`.
3. `impact>=2` or `urgency>=2` starts at `P2`.
4. Everything else starts at `P3`.
5. Raise one level (max `P1`, unless the explicit P0 rule is met) when material breadth,
   recurrence, or lack of workaround creates a clearly larger operational burden:
   - `breadth>=3`, or
   - `recurrence>=3`, or
   - `workaround>=3` with `impact>=2`.

Do not use a weighted sum to turn weak dimensions into a fake P0.

### Triage rank score

The kernel may return a `rank_score` for deterministic ordering **within comparable
priority bands**. It is not the priority definition, SLA, severity, or business value and
should normally remain out of customer-facing output.

## 5. Account escalation

Commercial/relationship attention is separate from operational priority.

Possible levels:

- `STANDARD`
- `EXPEDITED`
- `EXECUTIVE`

Inputs may include sourced:

- explicit cancellation/non-renewal/exec escalation,
- renewal/decision window,
- contractual commitment/deadline,
- strategic account designation,
- relationship breakdown.

Fallback:

- `EXECUTIVE` for explicit critical relationship risk or sourced executive escalation.
- `EXPEDITED` for strong relationship/renewal risk, strategic-account handling policy, or
  contractual deadline requiring faster coordination.
- `STANDARD` otherwise.

Account escalation can affect who is involved and checkpoint cadence. It must not rewrite
incident severity or customer harm.

## 6. Evidence grade

Use `HIGH | MEDIUM | LOW | CONFLICTED | UNKNOWN` from
`references/evidence-and-provenance.md`.

Examples:

- `P1 + LOW evidence` → investigate fast, do not state cause as fact.
- `P2 + HIGH evidence` → normal priority but well-defined work.
- `CONFLICTED` → surface the conflict and block dependent writes where needed.

## 7. Queue ordering

Default action ordering:

1. active incidents / incident candidates requiring coordination,
2. security/privacy/data-loss/legal/fraud/material-harm gates,
3. provider-native SLA `BREACHED` / imminent authoritative deadline,
4. `P0`,
5. `P1`,
6. explicit churn/non-renewal/switch intent with actionable owner,
7. overdue customer commitments,
8. blocked/ownerless handoffs,
9. `P2` by aging/recurrence/requester wait,
10. `P3`/backlog.

Within a band, use:

- older unanswered customer wait,
- longer blocked/internal wait,
- stronger breadth/recurrence,
- account escalation as a **tie-break/coordination modifier**,
- dependencies blocking other cases.

Never let high account value push a minor nuisance ahead of an active severe-harm case.

## 8. Aging and blocked work

Useful age fields:

- age since case opened,
- age since latest customer message,
- age since latest internal action,
- age in current state,
- age waiting customer,
- age waiting internal/engineering,
- handoff age since requested/accepted,
- commitment time-to-due/overdue.

A recently updated ticket can still contain an old broken promise. Track commitments and
handoffs explicitly rather than using `last_activity_at` as a proxy.

Surface:

- unassigned critical cases,
- cases bounced between teams repeatedly,
- blocked handoffs without a checkpoint,
- waiting-on-customer cases where the customer already replied,
- stale `RESOLVED` cases never verified/closed.

## 9. Re-triage triggers

Reassess when:

- breadth grows/shrinks,
- workaround succeeds/fails,
- new data-loss/security/privacy/legal signal appears,
- customer impact changes,
- native SLA state changes,
- renewal/decision window becomes material,
- reproduction disproves/confirms the original symptom,
- engineering fix deploys,
- customer still fails after a supposed fix,
- a new case turns an isolated report into a cluster/incident candidate.

Do not let the first priority label become permanent truth.

## 10. Dedupe and queue hygiene

When duplicates are found:

- preserve each source object,
- designate canonical case/problem cluster,
- link duplicates rather than erasing them,
- keep case count and independent account count,
- close/merge external records only when the user's requested mutation/process permits it.

A deterministic fingerprint may detect identical structured reports; semantic review is
still required before merging.
