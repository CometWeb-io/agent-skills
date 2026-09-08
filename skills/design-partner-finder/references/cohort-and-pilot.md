# Cohort and pilot design

Treat the cohort as a portfolio of experiments, not a leaderboard.

## Choose a cohort strategy

### `WEDGE_VALIDATION`

Use when a specific segment/workflow thesis already exists.

- Keep problem, user role, and implementation context relatively consistent.
- Seek repeated independent evidence across multiple representative partners.
- Use edge cases sparingly and only for named questions.

### `SEGMENT_DISCOVERY`

Use when the ICP or highest-velocity segment is still uncertain.

- Intentionally vary one or two dimensions such as company size, industry, persona, or maturity.
- Keep the core problem/workflow as constant as possible.
- Label variation explicitly so outcomes remain interpretable.

### `HORIZONTAL_TRANSFER`

Use when the same workflow should generalize across industries.

- Keep user role/workflow relatively fixed.
- Vary industry/context deliberately.
- Watch for hidden segment-specific requirements.

### `ENTERPRISE_STRESS_TEST`

Use when security, procurement, integration, scale, governance, or operational complexity is part of the thesis.

- Include representative core partners plus deliberately demanding environments.
- Do not confuse enterprise complexity with broad market representativeness.
- A lighthouse/logo candidate still needs real pain and engagement.

## Weighted hypothesis coverage

For each candidate record a coverage strength 0–5 for every Learning Contract hypothesis it can test.

Prioritize:

1. must-answer hypotheses,
2. high-importance hypotheses,
3. hypotheses below their desired independent replication count,
4. high-quality candidates with acceptable implementation/support cost.

Avoid a cohort in which five companies all answer the same easy question while a critical hypothesis has zero coverage.

## Replication and independence

A single partner can be an anecdote. For core hypotheses, seek enough independent partners to distinguish transferability from account-specific preference. Use the Learning Contract's desired replication, not a universal number.

Treat two brands operated by the same parent, two agencies using the same client workflow, or two candidates whose evidence comes from the same ecosystem as potentially correlated. Record a `duplicate_key` or lineage group when useful.

## Cost-to-learn

Estimate per candidate:

- implementation/support effort 0–5,
- procurement/security effort 0–5,
- expected learning yield 0–5,
- overlap with already-selected partners.

High learning with extreme cost can be inferior to a slightly lower-scoring partner that answers the same question quickly. Do not maximize score while ignoring team capacity.

## Selection script

`scripts/select_cohort.py` supports:

- `outreach_slate` — research-stage candidates (`PRIORITY_DISCOVERY`, `DISCOVERY`),
- `active_cohort` — live-qualified candidates (`PARTNER_READY`, optionally `ALIGNMENT_REQUIRED` when explicitly allowed),
- weighted hypothesis coverage,
- desired replication,
- segment/duplicate caps,
- effort/risk penalties,
- coverage diagnostics.

Treat the output as a transparent heuristic. Review any must-answer hypothesis left uncovered.

## Pilot success design

For every activated partner define:

- baseline workflow/current alternative,
- target user and owner,
- activation event,
- expected value event,
- usage/feedback cadence,
- measurable success and failure conditions,
- learning hypotheses tested,
- bespoke boundary,
- review date,
- graduation state.

A pilot is not successful merely because meetings happen. Prefer product/workflow behavior and measurable value evidence.
