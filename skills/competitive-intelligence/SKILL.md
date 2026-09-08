---
name: competitive-intelligence
description: Continuous competitive intelligence and competitor change detection. Use when the user asks to monitor competitors over time, refresh existing competitor profiles, detect what changed since a prior scan, track pricing/product/positioning/SEO/ads/reviews/company changes, maintain a competitor watchlist, produce recurring competitor digests, verify competitor claims, analyze cross-competitor trends, or turn observed deltas into product/GTM/sales implications. Prefer competitor-profiling for a one-time initial deep profile; use this skill when temporal state, snapshots, deltas, alerts, freshness, evidence provenance, or recurring intelligence operations matter.
---

# Competitive Intelligence

Operate a living competitive-intelligence system. Treat competitor knowledge as versioned state plus evidence-backed events, not a static dossier.

## Core contract

Always separate four layers:

1. **Observation** — what a source actually shows.
2. **Normalized state** — the comparable field stored in the competitor snapshot.
3. **Delta/event** — what changed relative to the previous admissible snapshot.
4. **Implication** — what the change may mean for product, GTM, sales, pricing, or strategy.

Never collapse an implication into a fact. Never infer a strategic move from a cosmetic page edit without corroboration.

## Boundaries with related skills

Use this skill as the temporal intelligence layer.

- Use `competitor-profiling` for a one-time baseline or deep profile. If no baseline exists, prefer invoking it first when available, then import its structured findings into the snapshot model.
- Use `competitors` for public comparison/alternative pages and battle-card-style competitor content.
- Use `sales-enablement` for sales battlecards, objection handling, and deal collateral.
- Use `pricing` for pricing decisions after a competitor pricing delta is verified.
- Use `ads` / `ad-creative` for channel-specific paid-ad analysis.
- Use `customer-research` for deep review mining, win/loss, or voice-of-customer analysis.
- Use `seo-audit`, `ai-seo`, or `seo-geo-aeo-maxxing` for specialist search-visibility diagnosis.
- Use `product-marketing` for the user's product/ICP/positioning context.
- Use `ai-council` when a material competitor event requires a consequential strategic decision.
- Use `marketing-loops` or a scheduler/automation for recurring execution. This skill itself performs one intelligence iteration per run; it does not claim to run continuously in the background.

Do not duplicate specialist work when a handoff gives a higher-quality answer.

## Resolve context before research

Read available product/marketing context before asking questions, including `.agents/product-marketing.md`, `.claude/product-marketing.md`, or equivalent project context.

Then load any existing competitive-intelligence state. Default project-relative root:

```text
.competitive-intelligence/
```

If the workspace does not exist and persistence is useful, initialize it with:

```bash
python scripts/ci_kernel.py init-workspace --root .competitive-intelligence [--subject-product "<name>"]
```

Read `references/data-model.md` before creating or modifying persisted state.

Only ask for missing information that blocks execution. If the user names competitors or prior snapshots, proceed with what is available.

## Choose an operating mode

Select exactly one primary mode per run:

- `BOOTSTRAP` — create the first canonical baseline and watch configuration.
- `REFRESH` — collect current evidence and update one or more competitor snapshots.
- `DELTA` — compare two known snapshots without broad new research.
- `WATCH` — execute one scheduled-monitoring iteration and emit only material new events.
- `DEEP_DIVE` — investigate one material event or hypothesis with contradiction search.
- `LANDSCAPE` — synthesize patterns across multiple competitors and time windows.
- `CLAIM_CHECK` — verify a specific competitor claim.
- `EXEC_BRIEF` — turn accepted events into a concise decision-ready summary.

If the user says "monitor continuously", "weekly", "every month", or equivalent, run the current iteration and, when scheduling tools exist, configure or suggest the recurring execution separately.

## Workflow

### 1. Define or load the watchlist

For each competitor maintain:

- stable `competitor_id` and canonical name,
- domains and important URLs,
- public repositories when relevant,
- competitor tier (`1` direct/strategic, `2` adjacent, `3` emerging/watch),
- focus areas,
- source set,
- requested cadence,
- optional hypotheses to watch.

Do not use employee-level personal surveillance as a source strategy. Hiring signals must be aggregated to role/category level unless a named executive move is materially relevant and publicly announced.

### 2. Establish the baseline

If no accepted snapshot exists:

1. Prefer a `competitor-profiling` baseline if that skill is available.
2. Otherwise collect a minimal baseline from primary public sources.
3. Normalize it into the schema from `references/data-model.md`.
4. Validate it with:

```bash
python scripts/ci_kernel.py validate-snapshot --snapshot <snapshot.json>
```

5. Compute its immutable snapshot/state hashes:

```bash
python scripts/ci_kernel.py hash --snapshot <snapshot.json>
```

6. Accept and archive it without overwriting historical snapshots:

```bash
python scripts/ci_kernel.py accept-snapshot --root .competitive-intelligence --snapshot <snapshot.json>
```

A bootstrap run does not invent a delta.

### 3. Collect current evidence

Prioritize sources according to `references/source-policy.md`.

For material current claims, prefer direct first-party evidence such as:

- pricing and packaging pages,
- product docs and changelogs,
- official announcements and newsroom posts,
- official public repositories/releases,
- app/integration marketplace listings,
- status/security/compliance pages when relevant.

Use high-quality secondary sources to corroborate, add context, or discover signals. Treat SEO/traffic estimates, social chatter, review anecdotes, and scraped summaries as lower-authority evidence unless triangulated.

Record source URL/identifier, source class, observed timestamp, verification timestamp, and whether the source directly supports the normalized field. For recurring watches, track source health separately from competitor state using `references/monitoring-policy.md`.

### 4. Normalize before diffing

Never use raw HTML/text diff as the final truth layer. Convert evidence into stable fields first.

Normalize at minimum:

- positioning and messaging,
- target segments/use cases,
- product capabilities and integrations,
- pricing/packaging/value metric/trial,
- customer proof and reviews,
- content/search/distribution signals,
- company and hiring signals,
- technology/trust/compliance signals,
- source metadata and freshness.

Strip scan metadata and obvious volatile noise from comparisons. See `references/data-model.md`.

### 5. Compute deterministic delta

Run:

```bash
python scripts/ci_kernel.py diff --old <previous.json> --new <current.json>
```

The kernel produces field-level changes, event keys, and a preliminary category. Treat this deterministic diff as the starting set, not the final intelligence feed.

For each change:

1. Remove cosmetic/irrelevant noise.
2. Verify that the new state is supported by evidence.
3. Check whether the old state was itself admissible and comparable.
4. Distinguish `ADDED`, `REMOVED`, and `MODIFIED`.
5. Mark silent changes separately from announced launches.
6. Detect reversals when a previously observed state is restored.

### 6. Classify the event

Use `references/event-taxonomy.md`.

Every accepted event must have:

- competitor,
- category,
- concise factual change statement,
- before/after where meaningful,
- first observed time,
- last verified time,
- verification state,
- materiality,
- evidence links/identifiers,
- implication hypothesis,
- recommended disposition.

Allowed verification states:

- `CONFIRMED`
- `LIKELY`
- `UNVERIFIED`
- `DISPUTED`
- `RETRACTED`

Do not label a change `CONFIRMED` from community chatter, SEO estimates, or a single weak secondary source.

### 7. Score materiality, then apply judgment

Use 0–1 inputs for relevance, magnitude, confidence, novelty, and persistence, then run:

```bash
python scripts/ci_kernel.py score --event-json '<json>'
```

The kernel returns a 0–100 score and severity bucket. Read `references/event-taxonomy.md` for scoring anchors.

Treat the score as a triage aid, not truth. Override only with an explicit rationale.

Default dispositions:

- `CRITICAL` — immediate deep dive; escalate strategic response.
- `HIGH` — include in current brief; assign a follow-up.
- `MEDIUM` — include in digest/watchlist unless strategically important.
- `LOW` — store but suppress from executive output.
- `NOISE` — do not promote to an intelligence event.

### 8. Run contradiction and significance checks

For every `CRITICAL` or `HIGH` event, and for any claim likely to change a product/GTM decision:

1. Search for confirming evidence.
2. Search separately for contradiction, rollback, regional limitation, grandfathering, beta/preview status, or qualification language.
3. Distinguish global availability from segment/plan/region-specific availability.
4. Distinguish announced intent from shipped capability.
5. Distinguish list price from effective customer economics.
6. Distinguish hiring intent from realized strategic execution.

If material ambiguity remains, keep the event `LIKELY`, `UNVERIFIED`, or `DISPUTED` and state the unresolved crux.

### 9. Deduplicate and detect patterns

Use the event key from the kernel to avoid repeated alerts for the same field transition.

Promote repeated related events into a pattern only when multiple independent observations support a coherent theme. Examples:

- enterprise upmarket motion,
- aggressive packaging expansion,
- AI feature convergence,
- ecosystem/integration land-grab,
- geographic expansion,
- retrenchment or product sunset,
- category repositioning.

A pattern is an analytical construct. Label its confidence separately from the underlying events.

### 10. Translate events into action

For each material event answer:

- **What changed?** Factual delta.
- **Why could it matter?** Mechanism, not generic fear.
- **What does it affect?** Product, positioning, pricing, sales, acquisition, retention, partnerships, trust, or none.
- **What is the response posture?** `IGNORE`, `WATCH`, `VERIFY`, `TEST`, `RESPOND`, or `ESCALATE`.
- **What would change the recommendation?** Falsifier or missing evidence.

Do not recommend copying a competitor by default. Include a no-action option when reacting would create roadmap thrash or weaken differentiation.

### 11. Persist state

Persist only accepted normalized state and evidence references. Keep snapshots immutable.

After evidence/significance checks, promote the accepted snapshot with:

```bash
python scripts/ci_kernel.py accept-snapshot --root .competitive-intelligence --snapshot <snapshot.json>
```

Append accepted events with deduplication:

```bash
python scripts/ci_kernel.py append-event --root .competitive-intelligence --event-json '@<event.json>'
```

An identical event revision is suppressed. A material revision such as `CONFIRMED → RETRACTED` is appended as a revision instead of rewriting history.

Recommended layout:

```text
.competitive-intelligence/
├── config.json
├── competitors/<competitor-id>/current.json
├── snapshots/<competitor-id>/<timestamp>.json
├── events/<YYYY-MM>.jsonl
├── reports/
└── raw/<competitor-id>/<timestamp>/   # optional when local raw capture is allowed
```

Never overwrite a historical snapshot. `current.json` may be replaced only after the new snapshot passes validation and evidence checks.

### 12. Produce the right output

Read `references/output-contract.md` and choose the smallest useful output:

- material delta brief,
- competitor-specific change report,
- weekly/monthly intelligence digest,
- cross-competitor pattern report,
- claim-check memo,
- executive brief.

Always include `as_of`, coverage, and known blind spots for reports containing current claims.

## Continuous monitoring semantics

A skill run is not a daemon. "Continuous" means a repeatable intelligence loop with persisted state plus an external scheduler.

For a recurring watch:

1. Save the watch configuration and baseline.
2. Define cadence by competitor tier and signal volatility.
3. Execute this skill in `WATCH` mode on each run.
4. Alert only on newly accepted material events.
5. Emit a digest on a lower-frequency cadence even when there are no critical alerts.
6. Periodically re-baseline fields whose source structure changed.

Prefer condition-based notification for high-severity events and time-based digests for routine intelligence.

## Failure modes to actively prevent

- Alerting on cookie banners, dates, counters, A/B copy, tracking parameters, or layout-only changes.
- Treating an SEO/traffic estimate as a verified business fact.
- Equating a feature page with actual feature availability.
- Treating one social post or review as representative market evidence.
- Mixing observations from different regions, plans, or dates.
- Replacing historical snapshots instead of appending a new version.
- Generating repeated alerts for the same transition.
- Hiding missing coverage behind confident prose.
- Turning every competitor move into a roadmap recommendation.
- Claiming background monitoring when no scheduler exists.

## Source, access, and privacy controls

Use only public or explicitly authorized sources and connector access. Do not bypass authentication, access controls, paywalls, CAPTCHAs, rate limits, or tool restrictions. Do not attempt to obtain confidential competitor information.

Minimize personal data. Prefer company-level and role-level signals. If public executive/personnel information is materially relevant, record only what is necessary for the competitive conclusion and preserve the public source.

## Quality gate before finalizing

A report is ready only when:

- every material event maps to at least one evidence item,
- current claims have verification timestamps,
- high/critical events have contradiction checks,
- cosmetic noise is suppressed,
- duplicate events are suppressed,
- fact and implication are clearly separated,
- uncertainty is visible,
- coverage gaps are disclosed,
- recommended action is proportional to evidence strength,
- persisted snapshots validate successfully when files are being maintained.

## Bundled resources

- `scripts/ci_kernel.py` — deterministic snapshot validation, hashing, delta detection, event classification, materiality scoring, freshness, and event keys.
- `references/data-model.md` — canonical storage and snapshot/event schema.
- `references/source-policy.md` — source authority, corroboration, freshness, and access rules.
- `references/event-taxonomy.md` — event categories, scoring anchors, and response thresholds.
- `references/monitoring-policy.md` — watch cadence, source health, removal confirmation, alerting, and re-baselining.
- `references/output-contract.md` — report formats and alert contract.
- `references/integrations.md` — tool/connector and cross-skill routing.
- `evals/evals.json` — behavioral eval cases for regression testing.
