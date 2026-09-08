# Evidence and Provenance

## Contents

1. Evidence model
2. Evidence grades
3. Temporal truth
4. Contradictions
5. Identity confidence
6. Coverage and sampling
7. Claim writing rules
8. Evidence packs

## 1. Evidence model

Every material customer-ops conclusion should be traceable to one or more source records.
Classify evidence by what it actually proves.

### Evidence kinds

- `reported` — customer/agent says something happened.
- `observed` — operator/tool directly observes the current product/system state.
- `reproduced` — the reported symptom is reproduced under known conditions.
- `telemetry_confirmed` — logs/metrics/analytics corroborate scope or behavior.
- `engineering_confirmed` — engineering evidence confirms cause/state/fix.
- `commercial_record` — CRM/billing/contract record supports commercial fact.
- `communication_record` — sent/received message proves a commitment/update occurred.
- `inferred` — conclusion derived from other evidence; not directly observed.

Do not upgrade `reported` to `confirmed` just because the report is credible. A customer
report can be sufficient to act urgently while remaining a report.

## 2. Evidence grades

Use an ordinal grade; do not imply statistical confidence.

### `HIGH`

Typical patterns:

- direct reproduction plus corroborating source,
- current telemetry/log evidence matching the symptom,
- exact current system-of-record value,
- multiple independent matching customer reports with stable identity/context.

### `MEDIUM`

Typical patterns:

- credible customer report plus partial corroboration,
- one direct source with incomplete scope,
- current evidence with unresolved context ambiguity.

### `LOW`

Typical patterns:

- one ambiguous or stale report,
- inferred identity/scope,
- hypothesis without corroboration,
- sentiment-only conclusion.

### `CONFLICTED`

Use when material sources disagree and the conflict has not been resolved. Do not average
conflicting facts into a synthetic answer.

### `UNKNOWN`

Use when the required evidence has not been checked or is unavailable.

High urgency + low evidence means **investigate quickly**, not "pretend confirmed".

## 3. Temporal truth

Operational state decays quickly. For current claims capture:

```text
source
source_id
observed_at / last_verified_at
as_of
```

Examples requiring current verification:

- issue/PR state,
- deployment/release state,
- account owner/renewal/commercial status,
- active support ticket state,
- incident status/severity/scope,
- provider-native SLA state,
- current usage/health signal,
- open commitment/handoff.

Historical records remain valid evidence about the past but cannot silently support a
claim about the present.

If the user asks "what is happening now?", "latest", or for an ops brief, re-check the
material systems of record where available.

## 4. Contradictions

When sources disagree:

1. record both claims with source/timestamp;
2. identify which system is authoritative for the field;
3. check whether one source is stale, mirrored, delayed, or scoped differently;
4. label the field `CONFLICTED` if unresolved;
5. do not perform a write that depends on the disputed fact until resolved or explicitly
   approved with the uncertainty visible.

Common contradictions:

- customer says issue persists; GitHub issue says closed,
- CRM says renewal next month; contract/billing says different date,
- support ticket says one account; telemetry shows broader impact,
- status page says recovered; customer exposure still fails verification,
- agent says workaround works; customer reports data risk.

Do not resolve contradictions by majority vote. Prefer authority + fresher direct evidence.

## 5. Identity confidence

Identity and problem matching are different tasks.

### Customer/account identity

- `HIGH` — stable system IDs link records.
- `MEDIUM` — verified account/email/domain plus matching context.
- `LOW` — names, domains, free text, or semantic similarity only.

Never merge customer records on `LOW` confidence automatically.

### Problem identity

A shared problem requires comparable:

- customer-visible symptom/outcome,
- workflow/product area,
- trigger/context,
- environment/version when relevant,
- time pattern,
- error/telemetry signature if available.

A similar feature name is not enough.

## 6. Coverage and sampling

For queues and multi-source analyses, track what was actually covered.

Use:

```text
coverage_status: COMPLETE | PARTIAL | SAMPLED | UNKNOWN
scope_requested
objects_found
objects_read_fully
pagination_exhausted: yes/no/unknown
critical_sources_missing[]
```

Rules:

- If the connector returns only the first page and no continuation is available, use
  `PARTIAL` rather than "all tickets".
- For large queues, inventory all available metadata first, then read full content for
  high-risk/ambiguous items.
- If the user explicitly asks for a sample, label selection logic and sample size.
- Do not extrapolate queue frequencies to all customers without a denominator and bias
  warning.

## 7. Claim writing rules

Use wording proportional to evidence.

Good:

- "Customer reports export is empty; not yet reproduced."
- "Two independent accounts report the same symptom in the last 40 minutes."
- "GitHub issue #123 is closed, but deployment state is not verified."
- "CRM currently shows renewal on 2026-09-30 as of <timestamp>."

Bad:

- "The export service is broken" from one report.
- "Root cause is pagination" from an untested hypothesis.
- "The customer will churn" from negative sentiment.
- "Fixed" because a PR merged.

For inferences, expose the chain:

```text
Inference: likely shared defect
Support: matching symptom + same component + two accounts + same time window
Against: no telemetry yet
Evidence grade: MEDIUM
Next test: reproduce / check telemetry
```

## 8. Evidence packs

When handing work to another skill/team, include the smallest evidence set that preserves
correctness.

### Engineering evidence pack

```text
customer-visible symptom
expected vs actual
scope/breadth
reproduction status
known environment/version
error/telemetry references
workaround status
case/cluster IDs
verification criteria
privacy classification
```

### Product evidence pack

```text
underlying job/problem
account_count + case_count
segments represented
window/recency
severity/intensity
support-load signal
requested solutions
workaround/current alternatives
representative language if permitted
contradictions/counterexamples
engineering dependency
evidence gaps
```

### Retention evidence pack

```text
expressed intent
leading indicators
support pain
usage/commercial evidence
relationship evidence
renewal/decision window
what is missing
owner/next action
```

### Incident evidence pack

```text
current customer symptom
known affected scope
earliest/latest timestamps
confirmed facts
unknowns
hypotheses
workaround/mitigation evidence
exposure list refs
security/privacy/legal gate state
verification criteria
```
