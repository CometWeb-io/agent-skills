# Customer Incident Operations v2

## Contents

1. Incident definition
2. Declaration and severity
3. Specialist gates
4. Roles
5. First-response workflow
6. Facts, hypotheses, unknowns
7. Timeline and decision log
8. Customer exposure map
9. Communication contract
10. Recovery, verification, closure
11. Postmortem and prevention
12. Anti-patterns

## 1. Incident definition

Treat a problem as an incident when customer impact requires coordinated response across
people/systems beyond ordinary isolated support handling.

Signals may include:

- critical service/capability unavailable,
- multiple independent customers with a shared failure,
- broad telemetry anomaly aligned with customer symptoms,
- customer data integrity risk,
- material financial harm,
- coordinated rollback/mitigation/comms need.

Do not declare an incident from emotional intensity alone. Conversely, do not leave ten
matching urgent cases fragmented if they are one shared service failure.

One customer can justify incident coordination when the impact is critical enough; account
count is not the sole declaration criterion.

## 2. Declaration and severity

Use the organization's documented incident policy first.

The fallback kernel returns **customer-impact severity** from confirmed impact/breadth/
criticality/workaround. Keep it separate from specialist security/privacy/legal response.

### `SEV1 — critical customer impact`

Typical patterns:

- broad critical customer-facing outage,
- critical ongoing data-integrity/customer-harm event,
- critical function unavailable broadly with no safe workaround,
- rapidly expanding critical incident requiring immediate coordination.

### `SEV2 — major customer impact`

- core functionality unavailable/severely degraded for a meaningful subset,
- multiple customers blocked with weak/no viable workaround,
- major impact requiring active coordinated response.

### `SEV3 — limited incident impact`

- limited customer degradation requiring coordination,
- small scope or usable workaround,
- material inconvenience without broad critical loss of function.

### `NOT_INCIDENT`

- isolated ordinary support case,
- feature request/expectation mismatch,
- unconfirmed report with no coordinated-response need,
- internal/non-production issue without material customer impact.

Do not use customer tier/revenue to define severity.

## 3. Specialist gates

These are **separate from service severity**:

- suspected/confirmed unauthorized access → `security`
- personal/confidential data exposure → `privacy`
- customer data loss/corruption → `security/privacy` as applicable + impact handling
- regulatory notice/formal demand/legal threat → `legal`
- fraud/material financial harm → `financial/billing/legal` as applicable
- material public/reputation exposure → `reputation/communications` gate

A security/privacy incident may be critically important even when ordinary service-impact
severity is not yet known. Do not force it into a generic SEV solely to signal importance.

Limit disclosure and preserve original evidence. Do not put exploit details or sensitive
customer data into broad channels/ordinary GitHub issues.

## 4. Roles

Use role names unless actual owners are sourced:

- `incident_commander` — coordination, state, priorities, decision checkpoints.
- `technical_lead` — diagnosis/mitigation/recovery work.
- `customer_comms` — canonical internal/customer/status communication.
- `scribe` — timeline/decisions/evidence links.
- `support_liaison` — case aggregation, customer symptom/exposure verification.
- `security/privacy/legal` — specialist gate owners when triggered.

One person may hold multiple roles in a small team. Use `unassigned` rather than inventing
names.

## 5. First-response workflow

1. Validate that the reported symptom is credible enough to investigate.
2. Determine whether coordinated incident response is warranted.
3. Establish fallback/company severity + specialist gates.
4. Assign/identify incident commander and canonical incident record.
5. Aggregate matching customer cases conservatively.
6. Start an exposure map for affected/suspected accounts.
7. Separate confirmed facts, unknowns, and hypotheses.
8. Start a timestamped timeline/decision log.
9. Identify safe mitigation/rollback/workaround options from evidence.
10. Align support/customer communication with canonical incident state.
11. Reassess severity/scope as evidence changes.

Do not wait for perfect root cause before declaring/mitigating a credible material incident.
Do not declare recovery before customer-visible evidence supports it.

## 6. Facts, hypotheses, unknowns

Maintain three explicit lists.

### Confirmed facts

Examples:

- two accounts reproduce the same error,
- error rate increased at a known time,
- specific endpoint is failing,
- rollback completed,
- customer workflow succeeds after mitigation.

### Hypotheses

Each hypothesis should include:

```text
hypothesis
evidence_for
evidence_against
next discriminating test
confidence
```

### Unknowns

Examples:

- true affected scope,
- incident start time,
- data integrity,
- regional/version scope,
- root cause,
- workaround safety,
- recovery durability.

Never let a plausible hypothesis leak into customer communication as fact.

## 7. Timeline and decision log

Timeline entry:

```text
timestamp
actor/system
event
evidence/source
incident state effect
```

Capture at least:

- earliest known customer impact,
- detection,
- acknowledgement,
- incident declaration,
- severity/gate changes,
- mitigation attempts,
- deployment/rollback changes,
- canonical customer/status communications,
- recovery evidence,
- verification,
- closure.

Decision entries should capture material tradeoffs (rollback vs forward fix, degraded mode,
communication scope) with owner and evidence. Do not rewrite history after the fact.

## 8. Customer exposure map

An incident's technical status and customer recovery status are different.

For each known/suspected account:

```text
account_id
exposure_state: SUSPECTED | CONFIRMED | MITIGATED | RECOVERED | VERIFIED
case_ids[]
confirmed symptom
workaround state
last customer update
follow-up required
recovery verification
```

Use this map to answer:

- who is actually affected,
- who has been told what,
- who needs workaround guidance,
- who must be proactively updated after recovery,
- whether service recovery is verified across the affected population/sample.

Do not publish the exposure list broadly unless appropriate.

## 9. Communication contract

During an active incident, support replies/status updates should align with the canonical
incident message. Avoid divergent ETAs/root-cause stories across agents.

Each update should contain only what is useful and confirmed:

1. **Status** — investigating/mitigating/monitoring/recovered as supported.
2. **Customer impact** — what users may experience; distinguish known vs suspected scope.
3. **Confirmed action** — mitigation/workaround currently in place, if verified.
4. **Next checkpoint** — actual committed checkpoint or "no confirmed ETA yet".

Do not hardcode a universal communication cadence. Follow organizational policy and update
before customers rely on materially stale information.

### Root cause

Do not state a cause externally until sufficiently confirmed and approved for the audience.
"A deployment is correlated with the start" is not the same as "the deployment caused it".

### ETA

Do not manufacture one. A next update/checkpoint is safer than a speculative repair time.
Any explicit customer-facing ETA becomes a commitment and belongs in the commitment ledger.

### Workarounds

Only communicate a workaround that is:

- relevant,
- tested/documented enough for the context,
- safe for data/account state,
- not more harmful than the incident.

## 10. Recovery, verification, closure

Separate:

- `MITIGATED` — impact reduced/contained.
- `RECOVERED` — service appears restored.
- `VERIFIED` — explicit customer-visible checks pass.
- `CLOSED` — incident/exposure follow-up and required actions are complete by policy.

Verification examples:

- critical endpoint succeeds across affected region/version,
- error rate returns to expected baseline for an observation window,
- customer workflow completes for representative/affected tenant,
- data reconciliation confirms integrity,
- affected customer confirms symptom no longer occurs.

"Dashboard is green" or "PR merged" is not sufficient by itself if the original customer
symptom has not been checked.

After recovery:

1. verify service/customer outcomes;
2. reconcile exposure list;
3. send/prepare follow-up for affected accounts when authorized;
4. reconcile commitments made during incident;
5. create/link durable prevention work;
6. run postmortem when severity/process requires it.

## 11. Postmortem and prevention

Minimum postmortem fields:

```text
summary
customer impact and exposure
start/detect/ack/mitigate/recover/verify timestamps
root cause (confirmed only)
contributing factors
detection gaps
response/coordination review
customer communication review
support-routing/triage review
what worked / failed
action items with owner + due/checkpoint
linked issues/PRs/releases
repeat/regression prevention
```

Focus on system/process causes, not blame.

Customer Ops should extract prevention work into the proper owner systems rather than
turning the postmortem itself into a backlog.

## 12. Anti-patterns

Do not:

- declare every urgent ticket an incident,
- delay a safe mitigation solely to finish root-cause analysis,
- use account value as severity,
- state customer count from raw ticket count,
- publish hypotheses/ETAs as facts,
- declare recovery from internal issue closure alone,
- lose affected-account follow-up after technical recovery,
- put sensitive security/privacy evidence into broad incident/GitHub channels,
- close incident action items without owners/checkpoints,
- omit support/comms failures from a technical-only postmortem.
