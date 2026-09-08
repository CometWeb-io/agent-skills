# MAXX scoring v3

## Contents

1. Core semantics and verdicts
2. Evidence and N/A rules
3. Score, coverage, profiles, gates, tiers
4. Freshness
5. Mechanical workflow


MAXX is an internal audit index. It is not a Google/OpenAI/Microsoft score, ranking factor model, or
industry benchmark. Weights, gates, tiers, and coverage thresholds are explicit audit-design choices
for repeatability.

## Core semantics

- `MAXX`: published only when all five pillars are active.
- `Focused readiness`: used for any subset of pillars (`RECON`/`PILLAR` or scoped work).
- Observed visibility: measured separately in `measurement.md`.
- Registry version: part of score identity. Do not silently compare different versions.

## Verdicts

| Verdict | Base points | Meaning |
|---|---:|---|
| `PASS` | 1.0 | condition satisfied for audited scope |
| `WEAK` | 0.5 | partial/inconsistent/materially compromised |
| `FAIL` | 0.0 | condition clearly not met |
| `N/A` | excluded | genuinely not applicable; registry rules apply |
| `NOT_ASSESSED` | excluded from score | evidence gap; still counts against coverage |

For sampled checks, an optional distribution derives points from observed pass/weak/fail counts:

```text
points = (pass + 0.5 * weak) / (pass + weak + fail)
```

The displayed verdict remains PASS only for all-pass, FAIL only for all-fail, and WEAK for a mixed
sample. This preserves more information than collapsing 7/8 passing pages to a fixed 0.5.

## Evidence requirements

Every scored verdict requires target-specific E2/E3/E4 evidence. Current platform docs may be added
as E1 but cannot substitute for target-site state. Conditional `N/A` requires applicability evidence;
checks marked `never` cannot be N/A. Surface checks may be N/A only when that surface is out of scope.

## Per-check and pillar score

Check weights live in `check-registry.json`.

```text
pillar score = sum(weight * points) / sum(assessed weight) * 100
coverage = assessed applicable weight / (assessed applicable weight + NOT_ASSESSED weight) * 100
```

`N/A` is removed from both numerator and denominator. Coverage below 75% is provisional. If any
active pillar is below 50% weighted coverage, the engine withholds the composite MAXX/Focused
readiness number entirely; it still reports the pillar diagnostic and evidence gap. A provisional
full MAXX may show an `indicative_tier`, but the normal tier is withheld until coverage is adequate.

Evidence quality is a separate grade describing the evidence base, not ranking probability.

## Profiles

| Profile | Foundation | Relevance | Authority | GEO | AEO |
|---|---:|---:|---:|---:|---:|
| balanced | 25 | 25 | 20 | 20 | 10 |
| classic-search | 30 | 30 | 25 | 10 | 5 |
| ai-first | 20 | 20 | 20 | 30 | 10 |

State the profile. Do not invent custom weights silently.

## Critical gates

Gates cap the composite only with direct/reproducible/connected target evidence. Current gate IDs:

- `SITEWIDE_NOINDEX`
- `SITEWIDE_SEARCH_DISALLOW`
- `CRITICAL_PAGES_NOINDEX`
- `CRITICAL_PAGES_NON_200`
- `CONTENT_UNAVAILABLE_TO_SEARCH_FETCH`

A training-bot block is never a MAXX gate by itself.

## Tiers

| Score | Tier |
|---:|---|
| 0-34.9 | Critical |
| 35-54.9 | Fragile |
| 55-69.9 | Competent |
| 70-84.9 | Strong |
| 85-100 | Maxxed |

`Critical` does not mean every low-scoring site is technically blocked; it means the full readiness
index is critically weak. Gate details explain actual blockers.

## Freshness

Platform-specific GEO checks self-expire through `live-source-registry.json`. If a required source
group is older than its TTL, scoring fails until a fresh official-source override is supplied. For
historical `as_of` dates, bundled source knowledge verified after the audit date is also rejected;
provide an official-source override verified on or before that date. This prevents both stale-memory
errors and temporal leakage.

Every score output includes an `audit_fingerprint` (SHA-256 of normalized audit input) plus scoring
engine and registry versions for reproducibility. A changed fingerprint means the scored input changed.

## Mechanical workflow

Prefer:

```bash
python scripts/build_audit_template.py --mode FULL > audit.json
python scripts/check_freshness.py --strict
python scripts/score_maxx.py audit.json > score.json
```

For DELTA/VERSUS:

```bash
python scripts/compare_scores.py before.json after.json --kind delta
python scripts/compare_scores.py site-a.json site-b.json --kind versus
```

If code execution is unavailable, reproduce the registry math exactly, show the arithmetic, enforce
N/A/evidence/freshness/gate rules manually, and label the result `manual registry calculation`.
Never score by feel.
