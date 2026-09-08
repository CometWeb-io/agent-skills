# Operational Feedback and Retention Risk

## Contents

1. Scope and bias
2. Atomic feedback extraction
3. Problem clustering
4. Product evidence packs
5. Retention-risk model
6. Expressed intent vs leading indicators
7. Evidence grade and time pressure
8. Intervention routing
9. Watchlist lifecycle
10. Anti-patterns

## 1. Scope and bias

This module handles feedback and churn/non-renewal signals that arise during customer
operations. It is not broad market research and not a validated churn-prediction model.

Support evidence is systematically biased toward:

- customers experiencing problems,
- active users who know how to contact support,
- customers/accounts with higher support access,
- issues serious enough to generate a contact.

Therefore:

- never call support-ticket frequency "market demand" without a denominator/bias warning;
- keep account count separate from message/case count;
- hand off broad VOC/persona/JTBD research to `customer-research`.

## 2. Atomic feedback extraction

For each material statement/event capture:

```text
source_id
account_id (if known)
observed_at
underlying_job_or_problem
requested_solution (if any)
constraint / why it matters
signal_type
polarity
intensity
affected_workflow
frequency_context
segment_context
evidence_kind
verbatim (only if useful/permitted)
evidence_grade
```

Separate:

- **problem** — failed desired outcome/job,
- **requested solution** — what the customer proposes,
- **constraint** — deadline/workflow/organizational reason it matters,
- **evidence** — what proves the problem,
- **support load** — operational cost to support, distinct from product value.

A feature request is not automatically the real problem.

### Feedback taxonomy

Use the narrowest useful label:

- `bug`
- `performance`
- `data_quality`
- `usability`
- `expectation_gap`
- `feature_request`
- `integration`
- `docs_gap`
- `billing`
- `pricing_value`
- `onboarding`
- `access_auth`
- `other`

## 3. Problem clustering

Create a `CANDIDATE` cluster only when signals/cases share a comparable underlying problem.
Compare:

- job/workflow,
- trigger/context,
- product area/component,
- expected outcome,
- failure mode,
- environment/version when relevant,
- time pattern,
- workaround.

Do not cluster solely on words such as "slow", "export", "report", or "integration".

### Cluster measurements

Always distinguish:

```text
case_count
account_count
independent_account_count if identity is known
segment_breakdown
window
earliest/latest seen
recurrence
support_load
workaround status
evidence grade
```

Ten cases from one account are not ten independent customers.

### Cluster confidence

- `HIGH` — consistent problem across multiple independent accounts/current evidence.
- `MEDIUM` — repeated but concentrated in one account/segment or some context ambiguity.
- `LOW` — single account/single case or unclear shared problem.
- `CONFLICTED` — candidate cluster contains material counterexamples.

Do not force a cluster to stay merged when new evidence shows different failure modes.
Split while preserving lineage.

## 4. Product evidence packs

Customer Ops can produce:

```text
problem statement / affected job
case_count + account_count
segments represented
window/recency
customer impact/intensity
support load (touches/time if available)
requested solutions
current workaround/alternative
engineering dependencies
representative customer language (if permitted)
commercial context (sourced only)
counterexamples / contradictions
evidence gaps
evidence grade
```

Do not assign roadmap priority solely from this pack. Product priority requires broader
strategy, capacity, opportunity cost, and non-support evidence; hand off to
`product-operator`/product decision workflow when available.

### Knowledge/self-service candidate

A repeated case may justify docs/self-service work when:

- the underlying problem is stable and non-defect-like,
- resolution is known and safe,
- repeated support load is material,
- self-service does not conceal a product defect or risky workaround.

Route content implementation to the appropriate documentation/copy workflow.

## 5. Retention-risk model

Use an ordinal operational heuristic. Prefer company/validated model output if it exists;
do not overwrite a real model with this fallback.

Fallback dimensions `0..3`:

### `cancel_intent`

- `0` — none observed.
- `1` — dissatisfaction / vague "may reconsider".
- `2` — non-renewal/competitor consideration or explicit evaluation.
- `3` — explicit cancel/non-renewal/switch/migration intent.

### `support_pain`

- `0` — none.
- `1` — isolated/minor issue.
- `2` — repeated unresolved meaningful issue.
- `3` — repeated severe failure, blocked core workflow, or broken commitments.

### `usage_decline`

- `0` — none/unknown.
- `1` — mild change.
- `2` — material decline.
- `3` — key workflow/product usage stopped/collapsed.

Only score this when usage evidence is actually available.

### `billing_risk`

- `0` — none/unknown.
- `1` — minor friction.
- `2` — failed payment/material plan concern.
- `3` — repeated/material billing failure or cancellation mechanics underway.

### `relationship_risk`

- `0` — none.
- `1` — mild negative sentiment.
- `2` — champion/stakeholder concern/escalation.
- `3` — champion lost/executive escalation/trust breakdown.

### `renewal_pressure`

- `0` — none/unknown/distant.
- `1` — relevant but not near.
- `2` — approaching decision window.
- `3` — imminent active renewal/non-renewal decision.

### `competitive_pressure`

- `0` — none.
- `1` — generic competitor mention.
- `2` — active comparison/evaluation.
- `3` — explicit switch/migration underway.

## 6. Expressed intent vs leading indicators

Do not hide the difference in one number.

### Expressed exit intent

Examples:

- "Cancel the subscription."
- "We will not renew."
- "We are migrating to X."

This is direct evidence of a decision/intention and should raise operational response even
if usage data looks healthy.

### Leading indicators

Examples:

- usage decline,
- repeated unresolved pain,
- billing failure,
- stakeholder/champion change,
- repeated support escalation,
- active competitor evaluation.

These can justify a watchlist but require corroboration. One weak leading signal should not
produce HIGH/CRITICAL risk.

## 7. Evidence grade and time pressure

Return at least:

```text
risk_level: LOW | MEDIUM | HIGH | CRITICAL
evidence_grade: HIGH | MEDIUM | LOW | CONFLICTED | UNKNOWN
expressed_exit_intent: NONE | CONSIDERING | EXPLICIT
time_pressure: LOW | MEDIUM | HIGH | IMMEDIATE
strongest_drivers[]
missing_evidence[]
```

Fallback risk logic (kernel):

- explicit exit intent (`cancel_intent=3`) → at least `HIGH`;
- explicit exit intent + material support/competitive/renewal pressure → `CRITICAL`;
- severe support pain + severe relationship breakdown → at least `HIGH`;
- several independent material leading indicators → `MEDIUM`/`HIGH` depending strength;
- one weak/ambiguous signal → `LOW`/`MEDIUM`, never pseudo-precise probability.

No raw weighted score needs to appear in the user-facing watchlist.

## 8. Intervention routing

Route by driver, not by generic "save the customer" instinct.

| Primary driver | Typical owner/next step |
|---|---|
| unresolved defect | support + engineering; CS coordinates relationship |
| incident exposure | incident/support + CS follow-up |
| missing capability | product evidence pack; no false roadmap promise |
| usage/value gap | CS/onboarding/product education |
| billing failure | billing/CS |
| pricing/value concern | CS + pricing/offer policy as appropriate |
| competitor migration | CS/product/competitive research when material |
| trust/broken commitment | relationship owner + commitment repair/escalation |
| business closed/no need | respect outcome; do not force save tactics |

Do not automatically discount, pause, refund, or promise a feature. Those actions require
the relevant policy/skill/authority.

## 9. Watchlist lifecycle

A watchlist should evolve, not accumulate permanent red flags.

Suggested record:

```text
account_id
opened_at
current_risk_level
previous_risk_level
expressed_exit_intent
time_pressure
evidence_grade
drivers[]
linked_cases/incidents/issues
owner
next_action
next_review_at
resolved_at
resolution_reason
```

Reassess when:

- issue is verified fixed,
- customer confirms recovery,
- renewal/decision outcome changes,
- usage recovers/declines materially,
- champion/relationship state changes,
- competitor migration starts/stops,
- billing issue resolves,
- evidence was contradicted.

Do not keep an account CRITICAL after the underlying evidence becomes stale/resolved.

## 10. Anti-patterns

Do not:

- output "85% churn probability" from this heuristic,
- use sentiment alone as churn evidence,
- infer usage decline without analytics/product data,
- count many messages from one account as broad market demand,
- automatically offer discounts for product-quality failures,
- promise roadmap timing to save an account without authority,
- use strategic account value to rewrite incident severity,
- ignore a low-value account's severe product harm,
- turn one competitor mention into competitive-intelligence conclusions,
- let watchlist risk stay permanently high after the facts change.
