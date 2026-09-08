# SLA, Deadlines, and Support Metrics

## Contents

1. SLA source-of-truth rule
2. Timing objects
3. Provider-native semantics
4. Deadline fallback
5. Internal handoff targets
6. Metric definitions
7. Quality over speed
8. Comparability and reporting
9. Anti-patterns

## 1. SLA source-of-truth rule

A support SLA is not just `opened_at + target_minutes`. Provider and contract semantics may
change the clock based on metric type, office hours, waiting states, reopen behavior,
workflow reassignment, and policy precedence.

Therefore:

1. Prefer the provider/contract/policy's **native current SLA state or due timestamp**.
2. If the provider exposes a due time, use that timestamp as authoritative for countdown.
3. If only a policy definition is available, reconstruct the clock only when every relevant
   semantic is known and current.
4. If semantics are incomplete, return `UNKNOWN` rather than a precise breach time.

Do not hardcode vendor behavior into this skill. When vendor-specific reconstruction is
material, verify the current official provider documentation live.

## 2. Timing objects

Keep these concepts separate:

- `first_response` — first qualifying response after case/conversation start.
- `next_response` — response to a later customer message.
- `periodic_update` — required update cadence while work continues.
- `requester_wait` — time the customer waits while responsibility is internal.
- `agent_work` — time actively owned/worked by support.
- `resolution` — time to resolution according to provider/policy semantics.
- `time_to_close` — time to final close, if distinct from resolved.
- `group/handoff_ownership` — internal team ownership target.
- `commitment_deadline` — explicit promise/checkpoint, not necessarily an SLA.

A case can have several timing objects simultaneously. Do not summarize them as one
"SLA" number without the user's policy saying so.

## 3. Provider-native semantics

When a helpdesk/provider exposes native SLA information, retain:

```text
provider
policy/id
metric
native_status
native_due_at
business_hours/calendar
pause state/reason
last_verified_at
```

Prefer the provider's native status for claims such as `BREACHED`, `PAUSED`, or target due.

If the provider's native metric conflicts with a manual calculation, assume the manual
calculation is incomplete until the provider policy is verified.

Examples of semantic dimensions that can vary:

- whether office hours/holidays count,
- whether `waiting on customer` pauses a clock,
- whether snooze/pending/on-hold pauses specific metrics,
- what event starts/restarts first/next reply,
- what happens after reopen,
- which workflow/policy wins when multiple policies match,
- whether internal notes satisfy a target,
- whether resolution and close are distinct.

Never infer these from vendor name alone.

## 4. Deadline fallback

When the authoritative source provides a normalized `due_at`, the kernel may classify the
deadline using `due_at`, `now`, and an optional warning window.

Default normalized states:

- `PAUSED` — authoritative source says the metric is paused.
- `BREACHED` — now >= due_at and target is still active/unmet.
- `AT_RISK` — due time is within the supplied warning window.
- `OK` — active and not within warning window.
- `MET` — authoritative source says the target was met.
- `FIXED` — target was missed but later fulfilled, if the source distinguishes it.
- `UNKNOWN` — insufficient/contradictory timing evidence.

Do not invent a universal 75% threshold. Warning windows should come from provider UI,
team policy, or an explicit operational default clearly labeled as such.

If the only inputs are `start_at` and `target_minutes`, do not reconstruct a provider SLA
unless `clock_mode=continuous` is explicit and all pause/business-hour semantics are known.

## 5. Internal handoff targets

Customer-facing SLA and internal team accountability are different.

Track internal handoff timing separately:

```text
handoff_requested_at
accepted_at
started_at
checkpoint_at / due_at
blocked_at
done_at
```

Useful internal measures:

- time to accept ownership,
- time waiting unassigned,
- time blocked,
- time owned by each team,
- number of reroutes/reassignments.

Do not claim an internal group SLA exists unless the organization's system/policy defines
one.

## 6. Metric definitions

### Queue / volume

- new cases,
- open cases,
- unowned cases,
- backlog by age/state/priority,
- incident-linked case count,
- account count affected by clusters/incidents.

Always distinguish cases from customers/accounts.

### Response and waiting

- first response time,
- next response time,
- requester wait time,
- longest unanswered customer message age,
- time waiting customer vs time waiting internal.

### Resolution quality

- first resolution time,
- full/final resolution time,
- reopen rate,
- multi-touch/agent-touch count when semantically available,
- verified-fix rate,
- unverified-close rate,
- regression/reopen after engineering closure.

### Handoff quality

- time to accept,
- handoff age,
- blocked handoff count,
- reassignment/reroute count,
- ownerless handoff count.

### Commitment quality

- open commitments,
- due-soon,
- overdue,
- fulfilled on time,
- renegotiated before breach,
- ownerless commitments.

### Incident operations

When timestamps exist and definitions are clear:

- time to detect,
- time to acknowledge,
- time to mitigation,
- time to recovery,
- time to customer-visible verification,
- incident exposure follow-up completion.

### Retention watch

Use counts/movement, not unvalidated probabilities:

- accounts entering/leaving HIGH/CRITICAL operational risk,
- explicit exit-intent count,
- risk drivers by category,
- unresolved product dependencies on at-risk accounts.

## 7. Quality over speed

Do not optimize first response/resolution time in isolation.

Fast closure can hide poor quality if:

- tickets reopen,
- customer continues to reproduce the symptom,
- agents bounce cases between owners,
- customer waits while internal clocks look good,
- support sends a superficial response to stop the timer,
- an engineering issue closes before release/customer verification.

Pair speed metrics with at least one quality metric when evaluating operations.

Recommended pairs:

| Speed metric | Quality counterbalance |
|---|---|
| first response | unresolved ask / next response / CSAT if available |
| resolution time | reopen rate / verified-fix rate |
| one-touch rate | reopen / escalation / customer confirmation |
| incident recovery | exposure verification / repeat incident |
| handoff speed | reroute count / acceptance quality |

## 8. Comparability and reporting

Every metric/report should state:

```text
window
denominator
provider/source
business-hours vs calendar-time semantics
included/excluded states
coverage status
material policy/instrumentation changes
```

Do not compare periods as if equivalent when any of these changed materially:

- SLA policy,
- office hours,
- bot/AI routing,
- team routing/assignment,
- case/ticket taxonomy,
- support channels,
- instrumentation,
- customer mix,
- pagination/coverage.

## 9. Anti-patterns

Do not:

- derive contractual breach from an approximate manual clock,
- use average response time to hide a small severe tail,
- report ticket count as customer count,
- praise low resolution time while reopen rate climbs,
- treat `Solved/Closed` in a support tool as verified product resolution,
- compare calendar and business-hour metrics without labeling them,
- mix bot/automation time with human response semantics without checking provider rules,
- invent SLA targets when the plan/policy is unknown.
