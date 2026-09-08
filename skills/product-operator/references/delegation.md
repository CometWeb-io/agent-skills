# Specialist delegation

Product Operator is the cross-source state synthesis and sequencing layer. Delegate when a specialist can
resolve a material claim or evidence gap that may change the product critical path.

## Core boundaries

### repo-to-roadmap
Use for deep repository-wide capability/debt analysis whose output is an evidence-based roadmap. Product
Operator should consume the resulting roadmap/state findings and decide what is critical **now** relative to
current product context and planning state. Do not duplicate the full repo analysis.

### release-readiness
Use for exhaustive pre-production readiness across product, QA, security, operations, docs, billing, support,
etc. Product Operator should invoke/consume it when the horizon is a serious production release, then sequence
its confirmed blockers against other work. Product Operator's `RELEASE` mode is orchestration, not a replacement
for exhaustive specialist readiness.

### customer-ops
Use for support/incidents/feedback/churn/customer operational signals. Product Operator consumes material
signals that change priorities; it should not become the ticket/support operations engine.

### evidence-researcher
Use when a material product decision depends on external/current evidence, primary sources, contradiction
search, or a formal claim/evidence ledger beyond normal product-state reconstruction.

### competitive-intelligence
Use for ongoing competitor profiling/delta. Product Operator consumes competitor changes only when they alter
current product priorities; it should not run continuous competitor surveillance itself.

### design-partner-finder
Use to find/qualify design partners/early adopters. Product Operator may identify "need design-partner evidence"
as a product learning action, but the finder owns account discovery/qualification.

### web-app-auditor
Use for observed user-facing QA: UI/UX, interactions, forms, state handling, data integrity, accessibility,
responsiveness, and critical flows. Product Operator consumes confirmed findings and sequences them.

### seo-geo-aeo-maxxing
Use for broad SEO/GEO/AEO diagnosis. Invoke only when search/AI visibility is material to the current goal.

### ai-council
Escalate consequential choices: large allocation, pricing/packaging, market entry, high-lock-in architecture,
material legal/security/privacy/reputation tradeoff, or strategic GO/NO-GO under uncertainty. Routine sequencing
stays in Product Operator.

### product-marketing
Use when canonical product context is missing/stale and goal/ICP/JTBD cannot be established well enough for
priority decisions.

### ai-humanize
Use only when the user explicitly requests naturalization/substantial rewrite of a publishable artifact. It is
not part of product-state reasoning.

## Generic handoff packet

Provide only:
- exact question;
- current product goal/horizon;
- relevant evidence/provenance;
- contradiction/uncertainty;
- what result would change the priority;
- required output shape if needed.

After specialist return, re-enter Product Operator: validate accepted evidence, update the state ledger, re-rank,
and re-sequence. Do not append every specialist recommendation automatically.
