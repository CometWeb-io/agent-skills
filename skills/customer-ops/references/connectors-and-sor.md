# Connectors and Systems of Record

## Contents

1. Core routing rule
2. Fact-to-source routing
3. Capability discovery
4. Connector-specific guidance
5. Cross-source conflict protocol
6. Freshness and repeated reads
7. Persistence and shadow-state prevention
8. Write routing

## 1. Core routing rule

Choose the **system of record (SoR) per fact**. Customer Ops is a coordination layer, not
one universal database.

Prefer the source that originates or authoritatively controls the field. A convenient
summary or mirrored record should not override the actual SoR.

## 2. Fact-to-source routing

| Fact | Preferred SoR | Common supporting evidence |
|---|---|---|
| raw customer message | support system / Gmail / chat | CRM activity note |
| account/contact identity | CRM / account DB | support thread |
| plan/contract/renewal | CRM + billing/contract system | CS notes |
| payment/refund/invoice | billing provider | CRM |
| product usage | product analytics/app DB | support statement |
| bug work state | GitHub issue/PR/release | support note |
| deployment/release state | deployment/release system / GitHub release | issue comment |
| incident canonical state | incident tracker/designated incident doc | support + telemetry |
| customer-visible symptom | customer report + reproduction | logs/telemetry |
| technical root cause | engineering/postmortem evidence | support hypothesis |
| provider SLA state | helpdesk/provider | manually reconstructed clock only as fallback |
| customer follow-up sent | support/email communication record | CRM note |
| explicit promise | original communication record | case summary |
| handoff acceptance | target team's work system / explicit acknowledgement | source case |

If the organization's actual architecture differs, follow it and record the override.

## 3. Capability discovery

Before a connector workflow, build an internal table:

```text
SOURCE | READ | WRITE | LAST_CHECKED | FACTS NEEDED | AUTHORITATIVE? | LIMITS
```

Classify capability:

- `available-read`
- `available-write`
- `user-provided`
- `unavailable`
- `unknown`

If one missing source blocks a material conclusion, mark the output `PARTIAL` and name the
blocked conclusion. Do not compensate by guessing from weaker sources.

For paginated tools, continue until the requested scope is exhausted when practical. If
only a partial page/range can be read, state coverage explicitly.

## 4. Connector-specific guidance

### Gmail / support inbox

Use for:

- original customer language,
- timestamps and thread chronology,
- open questions and unanswered asks,
- explicit commitments/checkpoints,
- customer confirmation that a symptom persists or is resolved,
- drafting/replying only when requested.

Do not infer:

- plan value,
- contract/SLA terms,
- renewal date,
- usage health,
- actual deployment state,

when a better SoR exists.

When a thread is long, identify the latest customer ask and unresolved commitments before
summarizing history.

### HubSpot / CRM

Use for:

- account/contact identity,
- commercial/lifecycle state,
- owner,
- renewal/decision context,
- logged CS/sales/support activities,
- stored ticket records if CRM is the support SoR.

Do not let stale notes override newer direct evidence. Record the property timestamp when
available.

Do not bulk change lifecycle/risk/owner fields merely because analysis suggests a value;
follow write authority and the organization's field definitions.

### GitHub

Use for:

- issue dedupe/search,
- issue/PR state,
- engineering discussion/reproduction,
- labels/types/assignees/milestones actually used by the repository,
- related issues, parent/sub-issue/dependency relationships when available,
- fix/release evidence and verification context.

Before creation/update, inspect repository conventions. Do not invent labels or issue types.
Do not copy raw customer data into GitHub unless the repository is explicitly approved for
that data and the minimum necessary information is required.

### Notion / incident docs

Use for:

- canonical incident timeline if designated,
- postmortem,
- runbook/process records,
- structured operational memory if the organization explicitly uses Notion for it.

A Notion summary is not automatically more authoritative than the originating ticket,
GitHub issue, CRM property, billing record, or telemetry.

### Product analytics / telemetry

Use for:

- scope/breadth corroboration,
- usage decline or feature adoption,
- error/latency trend,
- segment/cohort evidence when identifiers/permissions allow.

Customer Ops consumes current telemetry. If instrumentation is missing or semantically
wrong, route the implementation problem to `analytics` rather than inventing data.

### Billing

Use for:

- subscription/payment status,
- invoice state,
- plan/amount,
- refund/credit facts,
- billing failures.

Never infer a payment failure from a customer complaint if billing data is available.
Financial writes require explicit authority.

### Files / Drive / attachments

Use for customer-provided logs, screenshots, exports, contracts, and incident evidence only
when relevant and authorized. Treat raw attachments according to their sensitivity.

A document copy of a live operational field may be stale; prefer the live SoR for current
state.

## 5. Cross-source conflict protocol

When two sources disagree:

1. record both values with timestamps;
2. identify the authoritative source for that field;
3. check whether one source is stale, delayed, cached, mirrored, or scoped differently;
4. if unresolved, label `CONFLICTED`;
5. block writes that depend on the disputed fact unless the user explicitly chooses how to
   proceed with the uncertainty visible.

Examples:

- `GitHub closed` vs `customer still failing`: customer-visible outcome remains unresolved.
- `CRM renewal date` vs `contract/billing`: contract/billing wins for commercial fact.
- `support says one customer` vs `telemetry broad`: incident scope should be re-evaluated.

## 6. Freshness and repeated reads

For current claims, record `last_verified_at`/event timestamp. Re-read material state when:

- the user asks for latest/current status,
- an incident is active,
- a queued write depends on the field,
- the previous source check is old relative to the process,
- a new customer report contradicts previous closure,
- a provider SLA/deadline may have changed,
- a GitHub issue/PR/release has likely advanced.

Do not call old connector output "current" solely because it is in chat history.

## 7. Persistence and shadow-state prevention

Do not create duplicate truth stores by default.

Examples:

- If support is the case SoR, do not create a parallel Notion case record unless the team
  intentionally uses Notion as a coordination mirror.
- If GitHub owns engineering state, CRM should link the issue rather than reproduce every
  technical comment.
- If billing owns subscription state, do not overwrite it from a CRM inference.

When a mirror is necessary, store stable source links/IDs and a last-synced timestamp.

## 8. Write routing

Reads and analysis are different from mutations. Before a write, use
`references/write-authority.md`.

Typical writes include:

- customer email/reply,
- helpdesk case status/assignment/tag,
- CRM property/activity,
- GitHub issue/comment/label/assignee/state,
- Notion incident/update,
- billing credit/refund,
- published incident/status communication.

For every completed write, preserve the external object ID and verify the resulting state
when the tool supports a read-back.
