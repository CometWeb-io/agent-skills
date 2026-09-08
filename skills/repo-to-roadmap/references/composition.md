# Composition With Other Skills v2

## repo-to-roadmap owns

- assessment/target-state contract,
- whole-project topology and coverage,
- project truth model and capability inventory,
- normalized Evidence Ledger,
- desired-vs-current gap map,
- cross-domain hard dependencies,
- release/readiness synthesis,
- roadmap candidates, lanes, waves, and validation,
- baseline snapshots and delta invalidation,
- downstream roadmap handoff contract.

## product-operator - downstream execution operator

Use after a baseline/delta roadmap exists to answer:

- what enters the current cycle,
- what should happen this week,
- how issues/PRs map to active roadmap items,
- what changed in execution state,
- what should be stopped/deferred under current capacity.

Do not turn `repo-to-roadmap` into a daily sprint manager. `repo-to-roadmap` owns project truth and roadmap validity; `product-operator` owns execution cadence.

## evidence-researcher - evidence deepening

If available, use when material claims require a dedicated claim/evidence ledger, primary-source research, contradiction search, or freshness work beyond repository evidence. Import verified claim/evidence records rather than duplicating research.

## AI Council - contested material decisions

Use when project evidence does not uniquely determine a high-impact choice, for example:

- build vs buy vs remove,
- irreversible platform/architecture migration,
- scope cut under scarce capacity,
- high-impact risk acceptance,
- material product/GTM trade-off,
- portfolio conflict across projects.

Feed the Council accepted evidence/claims and alternatives. Import its result as `decision_ref`, not implementation evidence.

## product-teardown / competitive-intelligence

If available, use external-product or competitor analysis to discover implementable patterns, strategic gaps, or market constraints. Do not convert a competitor feature into roadmap priority without a target-state/customer/business rationale.

## customer-ops / customer-research

Use for support, incidents, churn signals, VOC/JTBD, and observed pain. Import material findings into outcome claims. Do not infer prevalence from a few anecdotes.

## design-partner-finder

Use after the roadmap exposes hypotheses that require external validation/design partners. The design-partner list does not prove product demand; it enables validation work.

## Security / privacy specialists

Use security scan/diff/threat-model or privacy expertise for deep discovery/validation. Repo-to-roadmap may detect a suspicious or unverified surface but should not impersonate a specialist audit.

## web-app-auditor

Use for live product/UI verification, critical flows, cross-screen consistency, form behavior, accessibility/interaction states, and visible data integrity.

## SEO / GEO / AEO / analytics / CRO / signup / onboarding / pricing / paywalls / churn

Use only when those domains materially affect the requested target state. Import validated findings into the common claim/capability/item model; do not reproduce every specialist recommendation.

## Handoff rules

Read `references/handoffs.md` when passing work downstream.

When ingesting any specialist result:

1. preserve source/finding IDs and date,
2. separate facts from recommendations,
3. preserve contradictions/limitations,
4. normalize only material claims,
5. avoid duplicate rediscovery,
6. let repo-to-roadmap sequence cross-domain work only after gates/dependencies are explicit.
