---
name: competitive-intelligence
description: >-
  Continuous competitive intelligence and competitor change detection. Use when the user asks to monitor competitors over time, refresh existing competitor profiles, detect what changed since a prior scan, track pricing/product/positioning/SEO/ads/reviews/company changes, maintain a competitor watchlist, produce recurring competitor digests, verify competitor claims, analyze cross-competitor trends, or turn observed deltas into product/GTM/sales implications. Use it when temporal state, snapshots, deltas, alerts, freshness, evidence provenance, or recurring intelligence operations matter. Do not use for a one-time initial deep profile with no monitoring intent (prefer a dedicated competitor-profiling skill when one is installed), for extracting a competitor's mechanisms to adapt into your own product (use product-teardown), for writing comparison pages or sales battlecards, for setting your own prices, or for a full search-visibility audit (use seo-geo-aeo-maxxing).
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

This skill performs one intelligence iteration per run; it does not claim to run continuously in the background. "Continuous" means persisted state plus an external scheduler — read `references/monitoring-policy.md` when the user asks for recurring monitoring.

## References — when to read

| Trigger | Read |
|---|---|
| before creating or modifying persisted state, snapshots, or events | `references/data-model.md` |
| before collecting evidence or assigning a verification state | `references/source-policy.md` |
| when classifying or scoring an event | `references/event-taxonomy.md` |
| when designing a watch, cadence, alerting, or re-baselining | `references/monitoring-policy.md` |
| before writing any report or alert | `references/output-contract.md` |
| when a connector, scheduler, or adjacent skill may be needed | `references/integrations.md` |

`scripts/ci_kernel.py` does deterministic snapshot validation, hashing, delta detection, event classification, materiality scoring, freshness, and event keys. `evals/evals.json` holds behavioral regression cases.

## Resolve context before research

Read available product context first (for example `.agents/product-marketing.md`), then load existing state from `.competitive-intelligence/`. If the workspace does not exist and persistence is useful:

```bash
python scripts/ci_kernel.py init-workspace --root .competitive-intelligence [--subject-product "<name>"]
```

Only ask for missing information that blocks execution. If the user names competitors or prior snapshots, proceed with what is available.

## Operating mode

Select exactly one primary mode per run: `BOOTSTRAP` (first baseline and watch configuration), `REFRESH` (update snapshots from current evidence), `DELTA` (compare two known snapshots without broad research), `WATCH` (one scheduled iteration; emit only material new events), `DEEP_DIVE` (one event or hypothesis with contradiction search), `LANDSCAPE` (patterns across competitors and time), `CLAIM_CHECK` (verify a specific claim), `EXEC_BRIEF` (accepted events to a decision-ready summary).

If the user asks for continuous, weekly, or monthly monitoring, run the current iteration and configure or suggest the recurring execution separately when scheduling tools exist.

## Workflow

1. **Watchlist.** Stable `competitor_id`, domains/URLs, repos when relevant, tier (`1` direct, `2` adjacent, `3` emerging), focus areas, sources, cadence. Do not use employee-level personal surveillance as a source strategy; aggregate hiring to role/category level unless a named executive move is materially relevant and publicly announced.
2. **Baseline.** If no accepted snapshot exists, prefer a competitor-profiling baseline when such a skill is installed, otherwise collect a minimal baseline from primary public sources; normalize, then `validate-snapshot`, `hash`, and `accept-snapshot`. A bootstrap run does not invent a delta.
3. **Collect.** Prefer direct first-party evidence (pricing pages, docs, changelogs, announcements, repos, marketplace listings, status/trust pages). Treat SEO/traffic estimates, social chatter, review anecdotes, and scraped summaries as lower-authority evidence unless triangulated. Record source, class, observed and verified timestamps, and whether it directly supports the field.
4. **Normalize before diffing.** Never use raw HTML/text diff as the final truth layer. Convert evidence into stable fields first and strip scan metadata and volatile noise.
5. **Deterministic delta.** `python scripts/ci_kernel.py diff --old <previous.json> --new <current.json>`. Treat the diff as the starting set, not the final feed: remove cosmetic noise, verify the new state, check the old state was admissible and comparable, separate silent changes from announced launches, detect reversals.
6. **Classify.** Every accepted event carries competitor, category, factual change, before/after, first observed, last verified, verification state, materiality, evidence, implication hypothesis, disposition. Verification states: `CONFIRMED`, `LIKELY`, `UNVERIFIED`, `DISPUTED`, `RETRACTED`. Do not label a change `CONFIRMED` from community chatter, SEO estimates, or a single weak secondary source.
7. **Materiality.** `python scripts/ci_kernel.py score --event-json '<json>'` returns 0–100 and a bucket (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `NOISE`). Treat the score as a triage aid, not truth. Override only with an explicit rationale. `NOISE` is never promoted to an event.
8. **Contradiction checks.** For every `CRITICAL` or `HIGH` event, and any claim likely to change a product/GTM decision, run the separate contradiction search in `references/source-policy.md` §6. If material ambiguity remains, keep the event `LIKELY`, `UNVERIFIED`, or `DISPUTED` and state the crux.
9. **Dedupe and patterns.** Use the kernel event key to avoid repeated alerts. Promote related events to a pattern only when multiple independent observations support a coherent theme; label pattern confidence separately from the events.
10. **Action.** For each material event: what changed, why it could matter (mechanism, not generic fear), what it affects, response posture (`IGNORE`, `WATCH`, `VERIFY`, `TEST`, `RESPOND`, `ESCALATE`), and what would change the recommendation. Do not recommend copying a competitor by default. Include a no-action option when reacting would create roadmap thrash or weaken differentiation.
11. **Persist.** Persist only accepted normalized state and evidence references with `accept-snapshot` and `append-event`. Never overwrite a historical snapshot; `current.json` may be replaced only after the new snapshot passes validation and evidence checks. A material revision such as `CONFIRMED → RETRACTED` is appended as a revision instead of rewriting history.
12. **Output.** Choose the smallest useful format from `references/output-contract.md` and pass its quality gate (§9) before finalizing. Always include `as_of`, coverage, and known blind spots for reports containing current claims.

## Source, access, and privacy controls

Use only public or explicitly authorized sources and connector access. Do not bypass authentication, access controls, paywalls, CAPTCHAs, rate limits, or tool restrictions. Do not attempt to obtain confidential competitor information.

Minimize personal data. Prefer company-level and role-level signals. If public executive/personnel information is materially relevant, record only what is necessary for the competitive conclusion and preserve the public source.

## Boundaries

Hand off rather than duplicate specialist work: consequential strategic responses to `ai-council`, search-visibility diagnosis to `seo-geo-aeo-maxxing`, mechanisms worth adapting to `product-teardown`. Comparison pages, battlecards, pricing decisions, ads, and review mining go to a dedicated skill only when the host has one installed; the routing table is in `references/integrations.md`. Pass only accepted facts, timestamps, source references, and clearly labeled hypotheses.
