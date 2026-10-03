# Universal Workflow

Read this file before the first case, queue, incident, or account pass of a task. The
front door keeps the stage names and the rules a stage must never drop; this file
holds the full procedure for each stage.

Execute these stages in order unless the selected mode explicitly skips one.

## A. Frame the operational decision

- State what action/decision the work must enable.
- Bound the queue/account/time window/repositories in scope.
- Route each material fact to its system of record.
- Decide what evidence is required before any external write.

## B. Inventory cheaply, then deepen selectively

For large queues, use two passes:

1. metadata/summary pass across the complete in-scope inventory;
2. full evidence pass for incident candidates, safety gates, SLA risk, P0/P1, explicit
   churn/non-renewal intent, overdue commitments, stalled handoffs, and ambiguous cases.

If pagination/result limits prevent full inventory, say so. Do not claim complete coverage.

## C. Normalize evidence and provenance

Separate:

`reported | observed | reproduced | telemetry-confirmed | engineering-confirmed | commercial-record | inferred`

Keep `confirmed facts`, `hypotheses`, `unknowns`, and `contradictions` distinct. Current
operational facts need a timestamp/verification state.

## D. Deduplicate conservatively

- Preserve raw source records.
- Distinguish identity dedupe from problem dedupe.
- Search existing GitHub work before proposing a new engineering issue.
- Treat deterministic fingerprints as candidate keys, never proof of semantic identity.
- Track `case_count` and `account_count` separately.

## E. Run gates before ordinary ranking

Surface before normal queue ordering:

- active incident or credible incident candidate,
- security/privacy/data-loss/legal/fraud/material financial-harm signal,
- provider-native SLA breach/near-breach,
- explicit cancellation/non-renewal/switch intent,
- overdue customer commitment,
- ownerless or blocked critical handoff.

Risk-gating a case does not prove root cause or incident scope.

## F. Classify, route, and assign one next action

Choose one primary next-action owner class:

`support | customer_success | product | engineering | incident_commander | billing | security | privacy | legal | revops | unassigned`

If no owner class applies yet, use `unassigned`; do not invent a person. Use handoff acceptance and due state
from `commitments-and-handoffs.md` for cross-team work rather than hiding it in
`WAITING_INTERNAL`.

## G. Act only within authority

Reads, drafts, writes, sends, financial actions, destructive actions, and sensitive
publication have different authority. Apply `write-authority.md` before any mutation.

Before a write:

- verify target identity/repository/account,
- dedupe/idempotency-check when applicable,
- minimize customer data,
- validate factual claims,
- match the mutation to explicit user intent.

After a write, verify the resulting state and report the returned external ID/state.

## H. Verify the customer outcome

Internal completion is not customer resolution. Use:

`RESOLVED → VERIFIED → CLOSED`

`VERIFIED` requires an explicit criterion tied to the original customer-visible symptom.
If a PR is merged but not deployed, a ticket is solved but immediately reopens, or the
customer still reproduces the symptom, keep the case unresolved/unverified.

## I. Close the learning loop

After resolution, check whether the case creates:

- a recurring problem cluster,
- regression/prevention engineering work,
- docs/self-service candidate,
- analytics gap,
- customer-research input,
- retention follow-up,
- post-incident action,
- product evidence pack.

Route the specialist work instead of expanding Customer Ops into a monolith.

