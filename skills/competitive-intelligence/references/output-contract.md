# Output Contract

## Contents

1. General rules
2. Material delta brief
3. Competitor change report
4. Periodic digest
5. Landscape report
6. Claim-check memo
7. Executive brief
8. Alert contract

## 1. General rules

Every current intelligence output must include:

- `As of` timestamp/date,
- competitors and major sources covered,
- material coverage gaps or stale areas,
- evidence/verification state for material claims,
- clear separation between facts and implications.

Prefer concise event cards/tables over long competitor biographies.

## 2. Material delta brief

Default output for `WATCH` and `REFRESH` when material changes exist:

```markdown
# Competitive Intelligence Delta — <date>

## Executive signal
<1–3 sentences: what materially changed and whether action is needed>

## Material events
| Severity | Competitor | Category | Verified change | Why it matters | Verification | Action |
|---|---|---|---|---|---|---|

## Patterns
<Only evidence-backed cross-event themes>

## Recommended moves
1. <Action or explicit no-action>

## Watch next
- <falsifier / next source / expected confirmation>

## Coverage and blind spots
- <what was scanned, stale, unavailable, or not checked>
```

If there are no material new events, say so and surface only coverage problems or watch items. Do not manufacture insight to fill the report.

## 3. Competitor change report

Use for a single competitor:

```markdown
# <Competitor> — Change Report

**As of:** <timestamp>
**Previous accepted snapshot:** <timestamp/hash>
**Current snapshot:** <timestamp/hash>

## What changed
<ordered event list with before → after>

## What did not materially change
<only when useful to resolve a concern>

## Strategic implications
### Product
### Positioning/GTM
### Pricing/Sales

## Evidence and uncertainty
<source-level summary, contradictions, scope limits>

## Response posture
<IGNORE | WATCH | VERIFY | TEST | RESPOND | ESCALATE>
```

## 4. Periodic digest

Use for weekly/monthly review. Organize by severity first, not competitor alphabetically.

Include:

- top 3–7 material moves,
- newly emerging patterns,
- events that were confirmed/retracted since the prior digest,
- stale or missing coverage,
- decisions/actions opened or closed,
- explicit "nothing material" when appropriate.

## 5. Landscape report

Use for multi-competitor strategic synthesis:

```markdown
# Competitive Landscape Movement — <window>

## Market direction
<what multiple competitors are doing>

## Convergence
<areas where offerings/messaging are becoming similar>

## Divergence
<where distinct strategies are emerging>

## White-space implications
<opportunities that remain under-served>

## Threats to our assumptions
<which beliefs about category/ICP/moat now deserve re-checking>

## Evidence strength
<how many competitors/time points/source classes support each pattern>
```

## 6. Claim-check memo

```markdown
# Claim Check — <claim>

**Verdict:** CONFIRMED | LIKELY | UNVERIFIED | DISPUTED | RETRACTED
**As of:** <timestamp>

## Direct evidence
## Contradictory or limiting evidence
## Scope qualifiers
## Conclusion
## What would change the verdict
```

## 7. Executive brief

Keep to decision-grade information:

- what changed,
- business impact mechanism,
- confidence,
- recommended response,
- cost of no action,
- next check/decision date.

Do not include raw crawl logs, long source summaries, or low-severity changes.

## 8. Alert contract

An alert should be emitted only for a newly accepted event whose severity exceeds the configured threshold or whose category is explicitly watched.

Alert format:

```text
[HIGH] Acme — PRICING_PACKAGING
Change: Pro list price 39 → 49 USD/month.
Verification: CONFIRMED (first-party pricing page; checked 2026-08-25)
Why it matters: Narrows our price premium in the core SMB segment.
Action: VERIFY downstream comparison pages; no product response yet.
Event key: sha256:...
```

Never alert repeatedly for the same event key unless the verification state, materiality, or implication materially changes.
