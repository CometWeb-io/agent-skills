# Output Contract v2

Use this as the default human-readable structure. Compress for small projects, but do not hide uncertainty.

# [Project] Evidence-Based Roadmap

## 1. Executive state

State:

- target-state profile and concrete end state,
- demonstrated current maturity/readiness,
- proven blockers vs suspected blockers,
- highest-leverage verified gap,
- recommended posture: `EXECUTE | VERIFY_FIRST | VALIDATE_FIRST | NARROW_SCOPE | REARCHITECT | READY_FOR_NEXT_PHASE`.

## 2. Assessment pin and confidence

Include:

- mode (`STANDARD | EXHAUSTIVE | DELTA | FOCUSED`),
- repo(s) and pinned refs when available,
- assessment `as_of`,
- coverage grade/scope claim,
- sampled/unavailable domains,
- file-level exhaustive status,
- important missing sources.

## 3. Target State Contract

Use stable target requirement IDs:

| Requirement | Domain | Mandatory | Applicability | Source |
|---|---|---:|---|---|

## 4. Project truth map

Summarize material capabilities, not every file:

| Capability | State | Criticality | Claim refs | Target refs | Confidence |
|---|---|---|---|---|---|

Include only material topology/dependency observations needed to understand the roadmap.

## 5. Critical findings / Evidence Ledger

For each material finding show:

`Claim ID -> finding -> impact -> strongest evidence -> confidence band -> contradiction/unknown`

Keep proven absence separate from "not found in search".

## 6. Roadmap

Default table:

| ID | Lane | Kind | Outcome | Why now | Claim refs | Acceptance proof | Depends on | Effort | Confidence |
|---|---|---|---|---|---|---|---|---|---|

Do not hide evidence behind a priority score.

## 7. Dependency waves and leverage

For each wave show:

- objective,
- item IDs,
- exit criteria,
- hard prerequisites,
- parallelizable groups when useful,
- critical-chain/leverage notes,
- reprioritization triggers.

Do not invent dates without capacity/deadline evidence.

## 8. Verify / validate backlog

List the smallest evidence actions that could materially change the roadmap. Distinguish technical truth (`VERIFY`) from customer/business truth (`VALIDATE`).

## 9. Defer / do not do yet

List tempting work that is weakly evidenced, low-impact, duplicate, premature, or blocked. Explain what would have to become true to reopen it.

## 10. Living-roadmap watch conditions

Include:

- snapshot hash,
- claims/items requiring watch,
- source/dependency/target triggers that force revalidation,
- whether this is a baseline or delta snapshot.

## 11. Specialist / Council handoffs

Only include material unresolved handoffs.

## 12. Final readiness statement

Use bounded language such as:

- `Roadmap defensible with current evidence.`
- `Roadmap usable but qualified by [coverage/evidence gap].`
- `Whole-project conclusion is not defensible until [missing source/domain] is inspected.`

Never say "everything is correct" from partial evidence.

## Machine-readable payload

When another agent/skill will consume the roadmap, or the user asks to save/update it, also produce a structured payload with:

- `schema_version`,
- `assessment`,
- `target_contract`,
- `coverage`,
- `claims`,
- `capabilities`,
- `items`,
- `watch_dependencies`,
- `snapshot_hash`.

Validate the payload before handoff.
