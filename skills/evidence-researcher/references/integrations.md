# Integration Contracts

## General handoff

A consumer receives:

- Research Contract and `as_of`,
- material claims with status/epistemic kind,
- accepted evidence edges and source provenance,
- temporal status and lineage/independence groups,
- contradiction state,
- gaps and refresh requirements,
- Evidence Pack hash.

The consumer may apply stricter gates.

## AI Council

Evidence Researcher is upstream of Council deliberation.

Provide:

- accepted material factual evidence,
- claim/source/evidence IDs,
- source class/role and independence group,
- directness/authority/scope/measurement assessments,
- temporal metadata,
- contradiction and gap state.

Critical boundary:

- `verified_for_research` means inspected for the research run.
- It does **not** mean `verified_for_decision`.
- For material current law/regulation/security/vendor-policy/internal-system claims, AI Council must apply its own decision-specific freshness and gate policy.
- Do not issue `GO | NO-GO | TEST | DEFER` inside Evidence Researcher.

## Web App Auditor

Separate:

- reproduced observation -> FACT with test/locator evidence,
- inferred cause -> INFERENCE with dependencies,
- recommendation -> downstream audit output, not evidence claim.

## SEO/GEO/AEO

Separate observed index/crawl/page/source facts from SEO doctrine and recommendations. Current SERP/search-engine behavior requires current evidence; generic SEO guidance is not proof of a page-specific state.

## Product Operator / Repo-to-Roadmap / Release Readiness

Supply verified facts about:

- repository/product state,
- customer evidence,
- operational constraints,
- market/competitor evidence,
- current blockers and uncertainties.

The consuming skill owns prioritization, sequencing, readiness verdicts, or roadmap actions.

## Customer research / sales / marketing

Qualitative observations remain qualitative. Preserve sample/source independence and do not turn repeated phrasing from copied reviews or one campaign source into market-wide fact.

## Writing/Humanization

Preserve factual constraints, caveats, and provenance. Editing may improve prose but must not strengthen evidence status or erase uncertainty.
