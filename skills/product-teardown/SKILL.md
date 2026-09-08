---
name: product-teardown
description: Analyze external products, websites, apps, APIs, documentation, and source repositories to extract evidence-backed, transferable, implementable product and engineering patterns rather than generic competitor summaries. Use when the user asks to teardown, reverse-engineer at a product/architecture level, benchmark, study, or learn from another product/repo; asks what workflows, UX mechanics, architecture, onboarding, monetization, developer experience, operations, reliability, or implementation ideas are worth adapting; asks "what can we borrow/learn/implement from X" or Polish equivalents such as "przeanalizuj produkt/repo", "wyciagnij wzorce", or "co warto wdrozyc". Also use for multi-product pattern synthesis and source-to-target adaptation. Do not use as the primary skill for ongoing competitor monitoring/delta analysis, broad competitor dossiers, external-facing comparison pages, or a roadmap of the user's own repo with no external/reference target.
---

# Product Teardown v2

Turn external observation into a defensible implementation decision. The unit of work is a **transferable pattern**, not a feature list, screenshot inventory, technology list, or competitor profile.

## Core contract

Preserve this chain for every material recommendation:

`source evidence -> source observation -> mechanism hypothesis -> destination problem evidence -> transfer conditions -> adaptation option -> implementation path -> validation -> action`

Never collapse the stages.

- Seeing UI proves only visible behavior/state, not backend architecture, rationale, adoption, or outcome.
- Seeing code proves implementation in the inspected version, not production use, customer value, or causal impact.
- Seeing a successful company use a pattern does not prove the pattern caused success.
- Seeing the same pattern across several products proves prevalence, not effectiveness.

Use claim states consistently:

- `OBSERVED` - directly supported by inspectable evidence.
- `INFERRED` - interpretation derived from observed evidence.
- `HYPOTHESIS` - proposed rationale, causal mechanism, expected effect, or transfer claim requiring validation.
- `UNKNOWN` - material point not established by available evidence.

Read `references/evidence-model.md` whenever building or judging the evidence ledger.

## Two independent axes

### Teardown shape

Choose one:

- `SOURCE_ONLY` - inspect a source and produce a pattern library. Never emit `ADOPT` without destination evidence.
- `SOURCE_TO_TARGET` - inspect one source and map patterns into a destination product/repo.
- `MULTI_SOURCE_TO_TARGET` - compare several sources, synthesize pattern families, then map the useful variants into the destination.

### Depth mode

Choose the smallest mode that can answer the request:

- `SNAPSHOT` - narrow question, usually 2-5 material candidates, low evidence budget.
- `STANDARD` - default. Flow/system map plus prioritized pattern portfolio and target mapping.
- `DEEP` - end-to-end capability tracing, contradiction search, multi-source synthesis when relevant, destination-equivalent checks, implementation alternatives, and explicit experiments/spikes.

Use the mode budgets and verdict proof burdens in `references/proof-burdens.md`.

Do not expand scope merely because more material is available. Stop when additional inspection is unlikely to change a top-pattern verdict, a material uncertainty, a blocker, or the implementation path.

## Workflow

### 1. Resolve the decision contract

Identify:

- source target(s): URL, app, screenshots, docs, repository, files, API, or combination;
- destination context: product/repo/team that may adopt the pattern;
- decision question: what should improve or what should be learned;
- teardown shape and depth mode;
- current-state requirement: whether claims must describe the source "as of now";
- requested output: findings, implementation packet, multi-source synthesis, or handoff.

If the destination is unavailable, use `SOURCE_ONLY`. Mark target fit as unknown and cap action at `CANDIDATE` or `REJECT`.

### 2. Establish source identity and version

Before interpretation, record what was actually inspected:

- product/site/app identity and relevant plan/account/platform/state;
- repository, branch/tag/commit, package/workspace, and license when code is involved;
- documentation/release/changelog version when material;
- `observed_at` or `as_of` for behavior that can change.

Never silently combine evidence from incompatible releases, plans, platforms, cohorts, or branches.

### 3. Route tools by authority

Prefer direct and first-party evidence.

For repositories:

1. Use the connected repository source when available, especially for private code.
2. Inspect manifests, entrypoints, architecture boundaries, code, tests, CI, migrations, releases, issues/PRs, and runtime/config evidence only as relevant.
3. Treat README and marketing claims as documentation claims until code/tests/runtime evidence corroborate them.

For products/apps/sites:

1. Prefer live behavior or user-provided screenshots for UI/flow claims.
2. Prefer official docs/help/changelog/API docs for documented capabilities.
3. Use a clearly associated source repository for implementation claims.
4. Use third-party/community evidence for reported perception, failure modes, or gaps, not as authoritative implementation evidence.

For the destination:

- repository is system of record for current code state;
- analytics/experiments are system of record for measured behavior;
- product docs/requirements are evidence of intended behavior, not necessarily shipped behavior;
- issue/project trackers are evidence of planned work, not shipped work.

Never send private source chunks into public search.

### 4. Build source and destination maps before extracting patterns

For products/apps/sites, inspect relevant flows and states using `references/product-playbook.md`.

For repositories, establish architecture and trace relevant capabilities end to end using `references/repo-playbook.md`.

For the destination, build only the minimum map required to answer:

- does the underlying problem exist;
- what equivalent capability already exists;
- what constraints, architecture, business model, scale, and team shape affect transfer;
- what metric or baseline would show improvement.

Do not turn the destination pass into a repo-wide roadmap or general product audit.

### 5. Build a dual evidence ledger

Record evidence at a locator precise enough to re-check it: URL/section, screenshot/state identifier, repo path plus line/range, commit/release, issue/PR, trace, test, or document section.

Maintain separate lanes for:

**Source evidence**
- behavior;
- implementation;
- rationale;
- outcome.

**Destination evidence**
- problem;
- existing capability;
- constraints;
- baseline/outcome.

For each material evidence item capture source, locator, subject, lane, claim state, version/time, note, confidence, and independence group when relevant.

### 6. Extract candidates at mechanism level

A candidate pattern must express:

`problem -> mechanism -> implementation shape -> expected effect -> conditions -> failure modes`

Reject entries that are only:

- "they have feature X";
- a visual imitation with no mechanism;
- a library/framework name with no product or engineering tradeoff;
- speculative business rationale presented as fact;
- a generic best practice that did not require teardown evidence;
- a code technique with no destination problem.

Use the abstraction ladder and taxonomy in `references/pattern-transfer.md`.

### 7. De-copy before transfer

Translate source-specific details into a reusable principle before proposing target work.

Prefer:

- copying the **problem framing** and **mechanism**;
- preserving source-specific implementation only as evidence;
- adapting interaction, architecture, data model, and operational shape to destination constraints;
- preserving destination brand, design system, terminology, and product strategy.

Do not recommend copying proprietary text, visual assets, distinctive trade dress, private implementation, or source code beyond what license/permission allows.

Use `references/implementation-transfer.md` to distinguish inspiration, semantic reimplementation, dependency integration, code reuse, and asset reuse.

### 8. For multiple sources, synthesize families before ranking

Do not write N mini-profiles and then average them.

Instead:

1. normalize source instances into mechanism-level candidates;
2. cluster materially equivalent mechanisms into pattern families;
3. preserve variants and contextual differences;
4. separate prevalence from outcome evidence;
5. identify divergence that changes transfer conditions;
6. choose the best destination variant, not the most common source implementation.

Read `references/multi-target-synthesis.md`.

### 9. Prove destination need before adoption

Before `ADOPT` or `EXPERIMENT`, establish destination-side evidence that the underlying problem exists or the current capability is materially deficient.

Check:

- current equivalent capability;
- target user/JTBD fit;
- business-model fit;
- architecture/data/permission constraints;
- team/operational capacity;
- baseline metric or observable failure;
- strategic differentiation or parity rationale.

If destination evidence is unavailable or weak, keep the pattern `CANDIDATE` rather than pretending fit is known.

### 10. Evaluate transferability

Evaluate each surviving candidate against:

Positive dimensions:

- problem fit;
- mechanism fit;
- source evidence strength;
- destination evidence strength;
- implementation feasibility;
- expected upside;
- reversibility;
- maintenance fit;
- strategic fit;
- differentiation.

Penalties/risks:

- dependency risk;
- complexity tax;
- opportunity cost;
- legal/IP risk;
- security/privacy risk;
- measurement risk.

Use qualitative reasoning first. Use `scripts/score_patterns.py` only as a deterministic sorting aid when several candidates need consistent ranking. A score is never evidence and cannot override a blocker or proof-burden rule.

### 11. Map the implementation without transplanting the source

When destination evidence exists, specify:

- affected target surface/module/service;
- existing capability to extend/replace/leave alone;
- transfer mode: inspiration, semantic reimplementation, integration, code reuse, or asset reuse;
- prerequisites, contracts, migrations, permissions, data changes, observability, and rollout needs;
- 1-3 implementation options when architecture is uncertain;
- effort band and uncertainty, not false-precision estimates;
- success metric and baseline;
- rollback/kill criteria;
- unresolved decisions.

Never invent destination file paths. Inspect the destination repo before naming files.

Use `references/implementation-transfer.md` for the transfer packet.

### 12. Red-team the transfer

For each top pattern, test at least:

- cargo-cult adoption;
- source success attribution error;
- hidden scale/data/brand/ecosystem dependency;
- business-model mismatch;
- architecture transplant;
- local optimum mismatch;
- complexity import;
- maintenance/support burden;
- parity trap;
- measurement blindness;
- stale/deprecated source behavior;
- license/IP/trade-dress risk;
- security/privacy regression;
- interaction conflict with another recommended pattern.

A valid teardown may conclude that the most useful lesson is **what not to copy**.

### 13. Resolve pattern interactions

Do not rank patterns as if they were independent when they compete for the same surface, require the same prerequisite, or produce contradictory behavior.

For top patterns, identify:

- enables;
- requires;
- conflicts with;
- substitutes for;
- bundles with.

Sequence only enough to explain the transfer. Hand a full roadmap to `repo-to-roadmap`.

### 14. Assign a verdict under proof burden

Use exactly one:

- `CANDIDATE` - useful source-derived pattern, but destination fit is not sufficiently established.
- `ADOPT` - evidence and destination fit are strong enough for direct implementation, with no unresolved mandatory blocker.
- `EXPERIMENT` - plausible high-value transfer with uncertainty that can be resolved through a reversible product experiment, technical spike, prototype, or shadow implementation.
- `BACKLOG` - useful, but lower leverage now, dependency-bound, poorly timed, or not worth current opportunity cost.
- `REJECT` - poor fit, weak mechanism, duplicate capability, negative economics, or harmful tradeoff.
- `REVIEW_REQUIRED` - unresolved legal/IP/security/privacy or another mandatory constraint blocks a clean recommendation.

Apply `references/proof-burdens.md`. Do not let a numeric score upgrade a pattern past its evidence ceiling.

### 15. Design validation proportional to uncertainty

For `EXPERIMENT`, specify the smallest falsifiable test that can change the decision:

- hypothesis;
- test type: product experiment, prototype, technical spike, shadow mode, benchmark, usability test, or staged rollout;
- primary metric;
- guardrail;
- baseline;
- success threshold or decision rule;
- timebox/sample condition when applicable;
- kill criteria;
- what result changes the verdict.

Do not use an A/B test mechanically when the uncertainty is architectural rather than behavioral.

### 16. Run structural QA before finalizing

When producing or persisting a machine-readable ledger:

1. validate with `scripts/validate_pattern_ledger.py`;
2. score only if ranking is useful with `scripts/score_patterns.py`;
3. ensure any final human verdict that differs from the suggested action explains why;
4. for DEEP mode, run the completion checks in `references/evals.md`.

The validator checks structure and cross-field invariants. It does not certify factual truth.

### 17. Stop and hand off instead of absorbing adjacent workflows

Read `references/composition.md` when the request overlaps adjacent skills.

Key boundaries:

- ongoing competitor change monitoring -> `competitive-intelligence`;
- broad competitor dossier -> `competitor-profiling`;
- external comparison/battlecard -> `competitors`;
- broader claim/evidence investigation -> `evidence-researcher`;
- repo-wide execution sequencing -> `repo-to-roadmap`;
- "what should we do next overall?" -> `product-operator`;
- consequential tradeoff decision or binding risk gate -> `AI Council`;
- production/client readiness after implementation -> `release-readiness`.

Complete the teardown-specific work first and hand off structured evidence rather than duplicating the downstream skill.

## Output requirements

Default human-readable output:

1. Executive verdict.
2. Inspection scope and source/version map.
3. Destination problem/equivalent-capability map when available.
4. Pattern portfolio or pattern-family portfolio.
5. Top implementation transfer packets.
6. Rejected patterns / false friends.
7. Unknowns that could change a verdict.
8. Handoff packet when useful.

Read `references/output-contract.md` for the detailed report and JSON ledger schema.

## Non-negotiable quality rules

- Never state inferred architecture as observed fact.
- Never state causal outcome without outcome evidence.
- Never treat repeated marketing claims as independent confirmation.
- Never recommend source-code reuse before license/provenance review.
- Never recommend `ADOPT` without destination problem evidence.
- Never recommend `ADOPT` when a mandatory legal/IP/security/privacy gate is unresolved.
- Never invent destination paths, metrics, or baselines.
- Never treat multi-source prevalence as proof of effectiveness.
- Never fill a pattern quota with weak observations.
- Never hide high-value `REJECT` findings.
- Prefer a reversible experiment when value is plausible but mechanism/fit remains uncertain.
- Preserve uncertainty explicitly instead of converting it into false precision.
