# Evidence, credibility, and freshness

## Claim states

Use exactly one state for each material claim:

- `observed` — directly supported by a source.
- `confirmed` — directly established through the company/user or an authoritative internal source.
- `inferred` — reasoned from evidence; label the inference.
- `unknown` — insufficient evidence.
- `contradicted` — credible evidence conflicts with the claim.

Never convert `unknown` into a negative fact.

## Substantiation states

For portfolio/customer/product claims that materially affect qualification:

- `substantiated`
- `partially_substantiated`
- `unverified`
- `contradicted`

`unverified` is an evidence state, not an accusation.

## Evidence lineage

Two pages repeating the same announcement are one lineage. Record when practical:

- source URL or connector reference,
- publisher/owner,
- source type,
- publication date or `date unavailable`,
- `last_verified_at`,
- whether primary/official, independent secondary, or derivative,
- claim IDs supported.

High confidence requires more than source count; it requires useful independence and directness.

## Freshness states

For claims presented as current, use:

- `CURRENT` — checked recently enough for the decision and no newer conflicting evidence was found.
- `NEAR_EXPIRY` — still usable but should be refreshed before a consequential invitation/pilot decision if easy.
- `STALE` — too old for the current claim or superseded by newer evidence.
- `UNKNOWN` — date/continuity cannot be established.

Do not encode one universal TTL. Triggers, current roles, integrations, active initiatives, pricing/policies, and company status decay faster than durable historical facts. Refresh based on how quickly the claim can change and how binding it is to the recommendation.

## Contradiction search

For top candidates search separately for evidence that would falsify the thesis. Examples:

- the relevant initiative ended,
- the product/workflow no longer exists,
- the named stakeholder moved roles,
- the implementation stack is incompatible,
- the use case is exceptional rather than representative,
- a material customer/capability claim lacks provenance,
- a competitive/IP conflict makes collaboration unsafe.

A top candidate without a reasonable counter-search is not fully diligenced.

## Dimension confidence

For every scored dimension, preferably record confidence 0–5 and state whether it is public/inferred/live-confirmed. Use the candidate score as a fit estimate, not as false precision.

Public research can support `problem_evidence`, `urgency`, `representativeness`, `learning_value`, `implementation_plausibility`, `stakeholder_path`, and credibility. It normally cannot confirm actual feedback commitment, user access, internal approval, or pilot readiness.
