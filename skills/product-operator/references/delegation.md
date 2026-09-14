# Specialist delegation

Product Operator is the cross-source state synthesis and sequencing layer. Delegate when a specialist can resolve a material claim, gate, or choice that may change the critical path.

## Core boundaries

### repo-to-roadmap
Use for deep repository-wide capability/debt analysis. Product Operator consumes verified roadmap/state findings and decides what is critical now. Do not duplicate the full repo analysis.

### release-readiness
Use for exhaustive pre-production readiness across product, QA, security, operations, docs, billing, support, etc. Product Operator sequences confirmed blockers; it does not recreate every gate.

### customer-ops
Use for support/incidents/feedback/churn/customer operational signals. Product Operator consumes only signals that change priority.

### evidence-researcher
Use when a material decision depends on external/current evidence, primary sources, contradiction search, or a formal evidence ledger beyond normal state reconstruction.

### competitive-intelligence
Use for ongoing competitor profiling/delta. Product Operator consumes only changes that alter current priorities.

### design-partner-finder
Use to discover/qualify design partners or early adopters. Product Operator may identify the learning need but not do account discovery itself.

### web-app-auditor
Use for observed user-facing QA: UX, interactions, forms, state handling, data integrity, accessibility, responsiveness, and critical flows.

### seo-geo-aeo-maxxing
Use for broad SEO/GEO/AEO diagnosis when visibility is material to the goal.

### pricing
Use for price level, tiers, packaging, value metric, freemium/trial structure, annual/monthly structure, and monetization mechanics. A pricing conflict is not resolved by whichever number is newest in code.

### offers
Use for pilot/offer structure, value framing, guarantees, scope, bonuses, scarcity, and payment structure. For SaaS pricing mechanics, use Pricing first.

### ai-council
Escalate consequential choices: large allocation, pricing/packaging trade-offs, market entry, high-lock-in architecture, material legal/security/privacy/reputation/financial trade-offs, or strategic GO/NO-GO under uncertainty. Routine sequencing stays in Product Operator.

**Free vs paid pilot:** Product Operator must not choose. Route domain work to `pricing` / `offers`; use `ai-council` when the choice materially changes the GTM/revenue motion or resource allocation.

### legal / finance gatekeeper
Use the authoritative human/professional source when the question is what is legally/financially permitted (for example seller identity, invoices, tax, payment acceptance). Product Operator cannot replace that authority. Treat the missing answer as `VERIFY NOW`.

### product-marketing
Use when canonical product context is missing/stale and goal/ICP/JTBD cannot be established well enough for priority decisions.

### ai-humanize
Use only when the user explicitly requests naturalization/substantial rewrite of a publishable artifact. It is not part of product-state reasoning.

## Generic handoff packet

Provide only:
- exact question;
- current product goal/horizon;
- relevant evidence/provenance;
- contradiction/uncertainty;
- what result would change the priority;
- required output shape if needed.

After specialist return, re-enter Product Operator: validate accepted evidence, update the state ledger, re-rank, and re-sequence. Do not append every specialist recommendation automatically.
