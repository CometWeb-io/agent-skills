# Evidence model

## Table of contents

1. Evidence subjects and lanes
2. Claim states
3. Source authority
4. Evidence item schema
5. Triangulation and contradiction
6. Freshness and versioning
7. Confidence and independence
8. Destination evidence discipline
9. Licensing and provenance

## 1. Evidence subjects and lanes

Every evidence item has a `subject` and `claim_lane`.

### Source lanes

- `source_behavior` - visible product/app/API behavior or documented behavior.
- `source_implementation` - code, tests, config, runtime/deployment implementation evidence.
- `source_rationale` - explicit first-party explanation of why a pattern exists.
- `source_outcome` - evidence of measured effect, adoption, reliability, conversion, performance, or another outcome.

### Destination lanes

- `destination_problem` - evidence the underlying problem exists in the target.
- `destination_existing_capability` - what the target already does and whether it is sufficient.
- `destination_constraint` - architecture, data, permission, business-model, team, policy, or operational constraints.
- `destination_baseline` - current measurable outcome or observable failure state used to evaluate transfer.

Do not use source evidence as a substitute for destination evidence.

## 2. Claim states

Use exactly:

- `OBSERVED` - directly supported by inspectable evidence.
- `INFERRED` - interpretation derived from observed evidence.
- `HYPOTHESIS` - proposed mechanism, rationale, expected effect, or transfer claim requiring validation.
- `UNKNOWN` - material point not established by available evidence.

Examples:

- UI shows an undo toast -> `source_behavior / OBSERVED`.
- This probably reduces destructive-action anxiety -> `source_rationale / HYPOTHESIS` unless the source states it.
- Code routes jobs through a durable queue -> `source_implementation / OBSERVED` if traced in code/config.
- Queue architecture caused better reliability -> `source_outcome / HYPOTHESIS` without outcome evidence.
- Destination users repeatedly fail at recovery -> `destination_problem / OBSERVED` if analytics/support/research supports it.

## 3. Source authority

Prefer evidence closest to the claim.

### Behavior

Strongest examples:

1. directly inspected live behavior/state;
2. user-provided screenshot/video tied to known state/version;
3. official product documentation;
4. first-party demo/changelog;
5. third-party report.

### Implementation

Strongest examples:

1. source code at known commit plus traced execution path/tests/config;
2. official architecture/runtime documentation;
3. maintainer explanation tied to a version;
4. README/marketing architecture claim;
5. third-party speculation.

### Outcome

Strongest examples:

1. destination/source experiment or measured telemetry with method/context;
2. first-party case study with clear method and scope;
3. customer/user research with relevant sampling caveats;
4. anecdotal report;
5. popularity/prevalence alone.

### Destination problem

Prefer:

1. product analytics/experiments;
2. direct customer research/support evidence;
3. reproducible product failure/friction;
4. roadmap/issue evidence corroborated by current product state;
5. stakeholder assertion without supporting evidence.

## 4. Evidence item schema

Capture at minimum:

```text
Evidence ID
Subject: source | destination
Target ID
Source / locator
Source type
Claim lane
Claim state
Observed at / version / commit
Evidence note
Confidence
Independence group when relevant
Contradiction note when relevant
```

A locator must be precise enough to re-check the claim.

For repos, prefer path plus line/range, symbol, commit, test, config, issue/PR, or trace.

For live products, prefer URL plus route/state/plan/platform and screenshot/state identifier when available.

## 5. Triangulation and contradiction

Triangulate claim lanes, not just source count.

Useful combinations:

- live behavior + official docs;
- code path + test + runtime/config evidence;
- destination analytics + customer/support evidence;
- source behavior + source rationale + destination problem evidence.

Two pages repeating the same marketing claim are not independent confirmation.

For top patterns:

- search for confirming evidence;
- search for evidence that contradicts the mechanism or transfer assumption;
- preserve version/plan/platform differences;
- downgrade confidence or verdict when contradiction remains unresolved.

Do not force a single truth across materially different variants.

## 6. Freshness and versioning

Record `observed_at`, commit, tag, release, document date, or plan/platform when the claim can change.

Treat evidence as stale or uncertain when:

- current behavior differs from docs;
- code comes from a branch/release not tied to the inspected product;
- feature is deprecated, hidden behind a flag, or removed;
- issue/PR describes planned work rather than shipped behavior;
- pricing/limits/policies vary by geography, account, cohort, or time.

For "current" material claims, use current evidence and state the `as_of` date/time or version.

## 7. Confidence and independence

Confidence is claim-specific. It is not confidence that the source company is successful.

Suggested interpretation:

- `0.90-1.00` - direct, specific, reproducible, no material contradiction;
- `0.70-0.89` - strong evidence with limited inference/version uncertainty;
- `0.50-0.69` - plausible but incomplete or materially inferred;
- `<0.50` - weak support; do not present as established fact.

Use `UNKNOWN` when evidence is absent.

Use `independence_group` when several sources share the same origin, codebase, library default, announcement, or copied claim. Multi-source prevalence is only as independent as its evidence origins.

## 8. Destination evidence discipline

An attractive source pattern is not a target requirement.

Before `ADOPT` or `EXPERIMENT`, seek destination evidence for:

- problem existence/severity;
- current workaround/equivalent capability;
- affected user/JTBD;
- baseline or observable failure;
- architecture/data/permission constraints;
- team/operational capacity;
- strategic objective.

If this evidence is unavailable, emit `CANDIDATE` and list the minimum destination discovery needed.

Do not manufacture target metrics or file paths to make a transfer look complete.

## 9. Licensing and provenance

Distinguish:

- learn from a pattern;
- semantically reimplement a mechanism;
- integrate a dependency;
- reuse source code;
- reuse copy/assets/branding.

Before recommending code reuse, inspect repository license and relevant notices. Before asset/copy reuse, require explicit rights/permission evidence.

Public accessibility is not permission to copy.
