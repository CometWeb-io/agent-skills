# Customer Ops Operating Model v2

## Contents

1. Purpose and invariants
2. Canonical graph
3. Canonical entities
4. Case and entity state machines
5. Identity, dedupe, and lineage
6. Ownership and responsibility
7. Closure and learning loop

## 1. Purpose and invariants

Use a **case graph** rather than a flat ticket list. The graph is a reasoning and exchange
model: it preserves what the customer experienced, where the evidence came from, which
internal work is linked, what was promised, who currently owns the next action, and
whether the outcome was actually verified.

Do **not** create a shadow CRM/helpdesk just because this graph exists. Persist records only
when the organization has designated a storage location and the user asked for the write.

Core invariants:

- Preserve raw source IDs; do not replace source records with summaries.
- Keep customer-visible symptom separate from suspected/confirmed technical cause.
- Keep case state separate from engineering work state.
- Keep incident severity separate from operational priority and account escalation.
- Keep customer SLA separate from internal handoff targets.
- Keep explicit commitments separate from generic next actions.
- Keep account count separate from case/message count.
- Require evidence for current state; store timestamps/verification state.
- Preserve prior resolutions and reopen lineage instead of overwriting history.

## 2. Canonical graph

Use this relationship model as needed:

```text
Account
  ├─ Contact
  ├─ Conversation ──> Case ──> CaseEvent
  │                     ├─ Signal
  │                     ├─ Commitment
  │                     ├─ Handoff
  │                     ├─ Intervention
  │                     └─ Outcome
  │
  └─ Case ──> ProblemCluster ──> EngineeringWorkItem
                │                    └─ PR / release / deployment evidence
                └─ Incident ──> IncidentExposure ──> Account / Case
```

Not every workflow needs every node. Keep the smallest graph that preserves correctness.

## 3. Canonical entities

### Account

Canonical customer organization/billing account.

```text
account_id
account_name (only when needed)
segment / tier (sourced only)
commercial_status
renewal_at / decision_window (if applicable)
relationship_owner
source_of_truth
last_verified_at
```

Do not infer plan, revenue, renewal, or strategic importance from support tone.

### Contact

A person associated with an account. Minimize personal data.

```text
contact_id
account_id
name (only when needed)
channel
source_id
identity_confidence
```

### Conversation

Raw support/email/chat thread. It is evidence, not automatically the canonical case.

```text
conversation_id
channel
source
opened_at
last_activity_at
participants_ref
message_refs[]
provider_state
provider_sla_ref
```

### Case

Canonical operational unit for one customer problem/outcome.

```text
case_id
account_id
contact_id
conversation_ids[]
case_type
state
customer_symptom
customer_desired_outcome
expected_behavior
confirmed_impact
breadth
operational_priority
evidence_grade
account_escalation
retention_risk
owner_class
next_action
next_action_due_at / checkpoint_at
opened_at
last_activity_at
resolved_at
verified_at
closed_at
linked_cluster_ids[]
linked_incident_ids[]
linked_engineering_ids[]
linked_signal_ids[]
linked_commitment_ids[]
linked_handoff_ids[]
contradictions[]
evidence_gaps[]
```

### CaseEvent

Append-only transition/audit event. Use when lifecycle chronology matters.

```text
event_id
case_id
event_type
from_state
to_state
occurred_at
actor_or_system
reason
source
source_id
```

Do not silently rewrite a past state transition. Add a correcting event.

### Signal

Atomic customer/product/commercial evidence extracted from a source.

```text
signal_id
case_id / account_id
signal_type
polarity
strength
observed_at
source
source_id
evidence_kind
fact_or_verbatim
segment_context
confidence
```

A signal is not a verdict. Several signals may support or contradict one conclusion.

### ProblemCluster

Group of cases sharing a comparable underlying customer problem.

```text
cluster_id
state
problem_statement
affected_job
product_area
context_signature
case_ids[]
account_ids[]
case_count
account_count
segment_breakdown
earliest_seen_at
latest_seen_at
recurrence
workaround_status
support_load
linked_engineering_ids[]
confidence
counterexamples[]
```

Do not equate `case_count` with independent demand.

### Incident

Time-bounded service degradation/event requiring coordinated response.

```text
incident_id
state
customer_impact_severity
specialist_gates[]
started_at
detected_at
acknowledged_at
mitigated_at
recovered_at
verified_at
affected_scope
customer_symptoms[]
confirmed_facts[]
unknowns[]
hypotheses[]
timeline[]
incident_commander
technical_lead
customer_comms_owner
scribe
support_liaison
linked_case_ids[]
linked_engineering_ids[]
```

Security/privacy/legal classification is a specialist gate. Do not use a generic service
severity number as a substitute for the specialist response process.

### IncidentExposure

Links an incident to a customer/account and tracks customer-facing recovery/comms.

```text
exposure_id
incident_id
account_id
case_ids[]
exposure_state
impact_confirmed
customer_symptom
workaround_state
comms_state
last_customer_update_at
recovery_verified_at
followup_state
```

This prevents an incident from being declared recovered while affected customers remain
unverified or uninformed.

### Handoff

Explicit cross-team transfer/escalation.

```text
handoff_id
case_id
from_owner_class
to_owner_class
state
reason
requested_at
accepted_at
started_at
blocked_at
done_at
owner
checkpoint_at / due_at
blocking_reason
source
source_id
```

`WAITING_INTERNAL` without an explicit target/owner is process debt, not a handoff.

### Commitment

A source-backed customer-facing promise or explicit checkpoint obligation.

```text
commitment_id
case_id / account_id
commitment_type
promise_text
made_by
made_at
source
source_id
owner
due_at / checkpoint_at
state
fulfilled_at
renegotiated_from
notes
```

Do not create a commitment from vague language such as "we'll look into it" unless the
source clearly establishes an obligation/checkpoint.

### EngineeringWorkItem

Usually a GitHub issue/PR or equivalent.

```text
provider
repo
number_or_id
title
work_item_type
state
labels
assignees
parent_or_dependency_refs[]
linked_case_ids[]
linked_cluster_ids[]
verification_criteria[]
release_or_deployment_ref
last_verified_at
```

### Intervention

Deliberate action intended to resolve a case or reduce account risk.

```text
intervention_id
case_id / account_id
kind
owner
performed_at
status
result
source_id
```

Examples: troubleshooting step, CS outreach, billing correction, workaround, product fix.

### Outcome

Customer-visible result, separate from internal completion.

```text
outcome_id
case_id
resolution_summary
verification_method
verification_evidence
verified
customer_followup_state
followup_at
reopened
unverified_close_reason
```

## 4. Case and entity state machines

### Case

Default progression:

```text
NEW
  -> TRIAGED
  -> OWNED
  -> IN_PROGRESS
       -> WAITING_CUSTOMER
       -> WAITING_INTERNAL
       -> ENGINEERING
       -> INCIDENT
  -> RESOLVED
  -> VERIFIED
  -> CLOSED
```

Alternate/terminal states:

- `DUPLICATE` — canonical case identified; preserve source link.
- `MERGED` — conversations/cases intentionally consolidated.
- `NOT_REPRODUCED` — investigation ended without reproducing; not equivalent to resolved.
- `WONT_FIX` — internal decision not to change product; customer outcome still needs handling.
- `CANCELLED` — case withdrawn/invalidated with source-backed reason.

Rules:

- `TRIAGED` requires case type, customer symptom/outcome, owner class or `unassigned`, and
  one next action.
- `OWNED` requires an accountable owner/queue according to the organization's process.
- `RESOLVED` means a remedy/answer exists internally.
- `VERIFIED` means the original customer-visible outcome passed a defined check.
- `CLOSED` means verification/follow-up/commitment policy is complete, or an explicit
  approved unverified-close path is recorded.
- Reopen preserves the prior resolution and adds a new event; do not erase history.

### Problem cluster

```text
CANDIDATE -> CONFIRMED -> ACTIONED -> MONITORING -> RESOLVED
                    \-> WATCHING
```

Use `CANDIDATE` until the underlying problem/context is sufficiently consistent.

### Incident

```text
DETECTED -> INVESTIGATING -> IDENTIFIED -> MITIGATING -> MONITORING
         -> RECOVERED -> VERIFIED -> CLOSED
```

`IDENTIFIED` requires a supported cause/trigger, not a plausible hypothesis.

### Incident exposure

```text
SUSPECTED -> CONFIRMED -> MITIGATED -> RECOVERED -> VERIFIED -> FOLLOWED_UP
```

### Handoff

```text
PROPOSED -> ACCEPTED -> IN_PROGRESS -> DONE
                      \-> BLOCKED -> IN_PROGRESS
                      \-> REJECTED / REROUTED
```

### Commitment

```text
OPEN -> DUE_SOON -> OVERDUE
  \-> FULFILLED
  \-> RENEGOTIATED
  \-> CANCELLED
```

Only explicit source-backed changes can mark a commitment renegotiated/cancelled.

## 5. Identity, dedupe, and lineage

### Identity confidence

- `HIGH` — stable account/user/ticket IDs match.
- `MEDIUM` — verified account/email plus matching context.
- `LOW` — name/domain/text similarity only.

Never merge on `LOW` confidence without review.

### Problem dedupe dimensions

Compare:

1. customer-visible symptom/outcome,
2. affected product area/component,
3. environment/version,
4. trigger/preconditions,
5. error signature/telemetry pattern,
6. time window,
7. verified cause when available.

A deterministic fingerprint is an idempotency/candidate aid, not semantic proof.

### Lineage

Preserve relationships such as:

```text
customer case -> problem cluster -> GitHub issue -> fix PR -> release/deploy
              -> verification -> customer outcome -> possible regression
```

Regression should reference the earlier remedy and failed verification context.

## 6. Ownership and responsibility

Use one primary owner class for the next action:

- `support` — customer communication, basic troubleshooting, case hygiene.
- `customer_success` — relationship/retention/account intervention.
- `product` — problem framing/product decision.
- `engineering` — defect investigation/fix.
- `incident_commander` — active coordinated incident response.
- `billing` — invoice/payment/refund/account billing state.
- `security` / `privacy` / `legal` — specialist gate/response.
- `revops` — CRM/lifecycle/process issue.

Multiple contributors can exist, but each next action needs one accountable owner class.
Use `unassigned` rather than inventing a person.

## 7. Closure and learning loop

A customer problem is not closed by an internal artifact:

```text
symptom observed
 -> evidence captured
 -> case triaged/owned
 -> cluster/incident/engineering work linked if needed
 -> remedy delivered
 -> original symptom verified
 -> commitments reconciled
 -> customer follow-up complete/waived by policy
 -> case closed
 -> learning routed
```

If engineering work is closed but customer verification fails, reopen/escalate the case
and decide whether the original work item should reopen or a regression item is required.
