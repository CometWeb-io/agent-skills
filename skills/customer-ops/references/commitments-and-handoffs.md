# Commitments and Internal Handoffs

## Contents

1. Why these are first-class entities
2. Commitment extraction
3. Commitment lifecycle
4. Handoff lifecycle
5. Acceptance and ownership
6. Timing and escalation
7. Broken promises and trust repair
8. Ops-brief integration
9. Anti-patterns

## 1. Why these are first-class entities

A case can look active while the actual customer obligation is silently overdue, and a
case can look "with engineering" while nobody in engineering has accepted ownership.

Therefore track:

- **Commitments** — explicit customer-facing promises/checkpoints.
- **Handoffs** — explicit transfers/escalations between owner classes/teams.

Do not hide either inside generic notes or `WAITING_INTERNAL`.

## 2. Commitment extraction

Create a commitment only when the source establishes a real obligation/checkpoint.

Strong examples:

- "We'll update you by Tuesday 3pm."
- "I will confirm whether the patch shipped tomorrow."
- "We will refund the invoice after finance approval" (promise may still require policy).
- "Next update in two hours" during incident.

Weak/non-commitment examples:

- "We'll look into it."
- "Engineering is investigating."
- "We hope to have this fixed soon."

For each commitment capture:

```text
commitment_id
case/account
promise_text
commitment_type: UPDATE | ACTION | ETA | CREDIT_REFUND | FOLLOWUP | OTHER
made_by
made_at
source + source_id
owner
due_at / checkpoint_at (only if explicit or policy-defined)
state
fulfilled_at
renegotiated_from
notes
```

An ETA communicated to a customer is both a forecast and a commitment; do not create one
without an authoritative engineering/incident commitment.

## 3. Commitment lifecycle

Default:

```text
OPEN -> DUE_SOON -> OVERDUE
  \-> FULFILLED
  \-> RENEGOTIATED
  \-> CANCELLED
```

Rules:

- `FULFILLED` requires evidence that the promised action/update occurred.
- `RENEGOTIATED` requires evidence the customer/authorized process received a new
  checkpoint/expectation; silently changing an internal due date is not renegotiation.
- `CANCELLED` requires a source-backed reason/authority.
- If no due/checkpoint exists, keep `OPEN` and avoid invented overdue status.
- Closing the parent case does not automatically fulfill outstanding commitments.

Use the kernel `commitment-status` when an explicit due/checkpoint exists.

## 4. Handoff lifecycle

Use:

```text
PROPOSED -> ACCEPTED -> IN_PROGRESS -> DONE
                      \-> BLOCKED -> IN_PROGRESS
         \-> REJECTED / REROUTED
```

Recommended fields:

```text
handoff_id
case_id
from_owner_class
to_owner_class
reason
requested_at
accepted_at
started_at
blocked_at
done_at
owner/team
checkpoint_at / due_at
blocking_reason
source + source_id
linked engineering/task id
```

### `PROPOSED`

Support/CS/product requests another team to take an action but acceptance is not proven.

### `ACCEPTED`

Target owner/team/system has accepted according to the organization's process.

### `IN_PROGRESS`

Work has actually begun/entered the target workflow.

### `BLOCKED`

Target work cannot progress; capture blocker and next unblock action.

### `DONE`

The target team's task is complete. `DONE` does not imply the customer case is verified.

## 5. Acceptance and ownership

Do not infer acceptance from:

- an @mention,
- a message posted in a channel,
- a GitHub issue created with no assignee/triage convention,
- moving the case to `WAITING_INTERNAL`,
- a bot notification.

Acceptance can be established by:

- explicit owner acknowledgement,
- assignment under an agreed workflow,
- target-system state that the organization defines as accepted,
- documented routing automation that creates ownership.

If unclear, use `PROPOSED`/`unassigned` and surface the gap.

## 6. Timing and escalation

Track separate timing:

- request → acceptance,
- acceptance → start,
- time blocked,
- time to checkpoint/due,
- completion.

Prefer an explicit internal/group SLA if the organization has one. Otherwise report age
without inventing a breach threshold.

Escalate attention when:

- critical handoff is unaccepted/unassigned,
- accepted handoff is past authoritative checkpoint,
- case repeatedly bounces/reroutes,
- target team marked done but customer verification failed,
- blocker has no owner/next action,
- customer commitment depends on the stalled handoff.

Do not escalate merely because a normal task is old if the policy/priority does not require
it; show age and owner instead.

## 7. Broken promises and trust repair

Broken commitments are a relationship-risk signal, especially when repeated.

When a commitment is overdue:

1. verify it was actually promised and remains outstanding;
2. identify owner/current case/incident state;
3. establish what can truthfully be communicated now;
4. do not invent a new ETA to compensate for the missed ETA;
5. create a new explicit checkpoint only when authorized and realistic;
6. record the broken commitment as a retention/relationship signal where relevant.

Repeated broken commitments can raise `support_pain`/`relationship_risk`, but the signal
must remain source-backed.

## 8. Ops-brief integration

Surface commitments/handoffs in this order:

### Now

- overdue customer commitments,
- critical unaccepted handoffs,
- blocked handoffs that block P0/P1/incident recovery,
- commitments due before the next operating window.

### Next

- upcoming checkpoints,
- accepted handoffs with material dependencies,
- follow-up that must happen after deployment/recovery.

### Quality

Track where useful:

- overdue commitment count/rate,
- fulfilled on-time rate,
- time to handoff acceptance,
- ownerless handoff count,
- reroute/reassignment count,
- blocked handoff age,
- customer cases closed with open commitment count (target should normally be zero).

## 9. Anti-patterns

Do not:

- infer a promise from vague intent,
- silently move a missed due date,
- mark a promise fulfilled because internal work completed if the promised customer update
  was not sent,
- mark engineering as owner from an @mention alone,
- call a handoff `DONE` proof that the customer symptom is fixed,
- hide ownerless handoffs in `WAITING_INTERNAL`,
- create a new optimistic ETA after a missed ETA without evidence,
- close a case while a material customer commitment is still open unless an explicit
  approved exception is recorded.
