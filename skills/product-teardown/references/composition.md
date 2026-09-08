# Composition and handoff boundaries

## Table of contents

1. Product Teardown owns
2. Adjacent skills
3. Composition gates
4. Handoff packets
5. Anti-overlap rules

## 1. Product Teardown owns

Product Teardown owns the path from external/reference evidence to a pattern-level transfer recommendation:

- direct inspection of external/reference product(s) or repository/repositories;
- source/version map;
- source and destination evidence ledgers specific to the teardown;
- mechanism-level pattern abstraction;
- multi-source pattern-family synthesis;
- anti-copy/negative-transfer analysis;
- destination problem/equivalent-capability check;
- pattern transferability and implementation alternatives;
- pattern interaction notes;
- pattern-level verdict and validation plan.

It does not own portfolio-level product priority, ongoing monitoring, a broad competitor dossier, or a full repo execution roadmap.

## 2. Adjacent skills

### competitor-profiling

Use when the main deliverable is a broad dossier: company, ICP, positioning, pricing, product surface, strengths/weaknesses, and competitive posture.

Product Teardown should receive a narrow inspection target/question and return mechanisms, not duplicate the dossier.

### competitive-intelligence

Use for repeated observation over time, release/change deltas, monitoring, watchlists, and trend synthesis.

Product Teardown may emit `watch_candidates` for patterns whose version/freshness matters, but should not create an ongoing monitoring loop itself.

### competitors

Use for external-facing comparison/alternative pages, battlecards, and positioning against a competitor.

Product Teardown can provide evidence-backed capability and mechanism inputs, but it should not write the comparison asset unless explicitly handed off.

### evidence-researcher

Use when a decision-critical claim cannot be resolved from direct teardown sources and needs broader primary-source investigation, formal contradiction work, or a claim/evidence ledger beyond the inspected targets.

### repo-to-roadmap

Use after accepted pattern decisions when the user wants repo-wide sequencing, dependencies, milestones, resource allocation, and delivery logic.

Product Teardown should provide pattern interactions and prerequisites, not a full roadmap.

### product-operator

Use when the question becomes "what should we do next overall?" and teardown findings must be weighed against customer evidence, strategy, backlog, metrics, capacity, and current product state.

### release-readiness

Use after implementation when the question is whether the resulting product/repo is production/client ready.

### AI Council

Use when pattern adoption is consequential, options materially conflict, opportunity cost is strategic, or a binding legal/security/privacy/financial/reputation tradeoff requires a decision protocol.

Product Teardown supplies accepted evidence, candidate patterns, uncertainties, and implementation options. AI Council owns the consequential decision process.

## 3. Composition gates

Before absorbing adjacent work, ask:

1. Is this necessary to establish a source pattern or target transfer condition?
2. Will the result change a pattern verdict or implementation option?
3. Is this still pattern-level rather than portfolio/company/roadmap-level?

If answer 1 or 2 is no, do not expand.

If more than roughly one-third of remaining requested work is clearly owned by an adjacent skill, complete the teardown-specific portion and hand off.

## 4. Handoff packets

### evidence-researcher

```text
Claim
Why decision-critical
Known supporting evidence
Known contradiction
Required authority/source type
Freshness/version requirement
What result changes the pattern verdict
```

### repo-to-roadmap

```text
Accepted pattern IDs
Verdicts
Expected outcomes
Target surfaces/modules already evidenced
Prerequisites
Pattern interactions: requires/enables/conflicts/substitutes/bundles
Implementation options
Known risks
Experiments/spikes
Rollback constraints
```

### product-operator

```text
Pattern portfolio
Destination problem evidence
Expected value / opportunity cost notes
Strategic fit notes
Rejected false friends
Unknowns
What decisions remain portfolio-level
```

### AI Council

```text
Decision question
Pattern options
Accepted material evidence
Assumptions/unknowns
Contradictions
Mandatory gate status
Reversibility
Experiment option
What the teardown cannot decide
```

### competitive-intelligence

```text
Watch target
Pattern/family ID
Material version-sensitive claim
Current observed version/date
What change would invalidate transfer reasoning
Suggested monitoring trigger
```

## 5. Anti-overlap rules

- Do not turn a teardown into a company research report.
- Do not create recurring monitoring unless explicitly handed off.
- Do not build a repo-wide roadmap inside Product Teardown.
- Do not rank all product initiatives against each other inside Product Teardown.
- Do not perform consequential governance voting inside Product Teardown.
- Do not duplicate downstream artifacts; provide structured handoff inputs.
