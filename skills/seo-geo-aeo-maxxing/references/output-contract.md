# Output contract

## Contents

1. Verdict, scope, readiness score
2. Observed visibility and platform controls
3. Material findings and priorities
4. Gaps, backlog, comparisons, next step
5. Style constraints


Use this structure by default. Compress for RECON/PILLAR; expand for FULL/VERSUS/DELTA.

## 1. Verdict

One direct sentence naming the dominant constraint, advantage, or uncertainty. Do not lead with a
score if a gate or evidence gap changes the decision.

## 2. Scope and evidence

State:

- mode, registry version, scoring profile;
- site archetype(s), including `INFERRED` where applicable;
- target surfaces;
- pages/templates sampled and critical URL classes;
- raw vs rendered coverage;
- connected data sources;
- volatile platform groups refreshed;
- material sample limitations.

## 3. Readiness score

Use a compact table:

| Pillar | Score | Coverage | Evidence | State |
|---|---:|---:|---|---|
| Foundation | 78 | 100% | A | scored |
| Relevance | 64 | 91% | B | scored |
| Authority | 58 | 62% | B | provisional |
| GEO | 55 | 80% | A | scored |
| AEO | 70 | 100% | B | scored |

When all five pillars are active, report:

`MAXX 65/100 - Competent (balanced; 87% coverage; evidence B)`

For any subset of pillars, report:

`Focused readiness 72/100 - not whole-site MAXX`

Do not assign a MAXX tier to a partial audit. If any active pillar has no assessable checks, or has
less than 50% weighted coverage, withhold the composite number and state the evidence requirement.
Coverage from 50% to 74.9% is still provisional. Do not present a normal MAXX tier while the full
score is provisional; an indicative tier may be shown only as explicitly provisional. Show active
gates directly below the score.

## 4. Observed search / AI visibility

Keep outcomes separate from readiness. Include only measured rows, for example:

| Outcome signal | Result | Window | Source |
|---|---:|---|---|
| Google generative AI impressions | 12,400 | 28d | GSC Generative AI |
| Microsoft AI citations | 86 | 28d | BWT AI Performance |
| ChatGPT referral sessions | 214 | 28d | analytics |
| Sampled prompt citation rate | 4/20 | fixed panel | directional sample |

Never substitute zero for unavailable measurement.

## 5. Platform-control matrix

Include only when GEO is in scope or platform access is decision-relevant.

| Surface | State | Target evidence | Current control interpretation |
|---|---|---|---|
| ChatGPT Search | allowed/blocked/unknown | OAI-SearchBot + fetch/WAF | keep GPTBot training separate |
| Claude | allowed/blocked/unknown | Claude-SearchBot/User | keep ClaudeBot training separate |
| Perplexity | allowed/blocked/unknown | PerplexityBot + WAF | user fetch behavior separate |
| Google AI Search | eligible/blocked/unknown | Google Search eligibility | Google-Extended not Search control |
| Bing/Copilot | eligible/blocked/unknown | Bing/BWT evidence | no invented Copilot bot |

Do not add a row that was not assessed unless the unknown itself is decision-relevant.

## 6. Findings that matter

Group only material findings. For each WEAK/FAIL include:

- check ID and verdict;
- exact evidence and evidence class;
- affected scope/sample;
- why it matters, without causal overclaim;
- remediation or next diagnostic step.

For sampled/template checks, report the observed distribution where available.

## 7. Top actions - this week

Return up to 3, ordered by dependency first and then priority.

For each show:

- action type: `REMEDIATION`, `MEASUREMENT`, or `EXPERIMENT`;
- check/finding;
- target evidence;
- affected scope/business path;
- exact next step;
- Impact / Confidence / Ease / ICE;
- owner when obvious.

Add code only when the finding needs code and the user wants implementation detail.

## 8. This month

Return 5-7 concise actions only when enough evidence-backed work exists. Do not pad.

## 9. Preserve

List only evidence-backed strengths that should not be broken by remediation. Skip if none matter.

## 10. Not assessed / scope limits

List every material gap that could change the decision and the fastest defensible source needed to
close it. Distinguish `not tested` from `not present`.

## 11. Experiments/backlog

Keep low-confidence GEO/AEO tactics here and label them `EXPERIMENTAL`. Do not mix them with
confirmed blockers.

## 12. DELTA / VERSUS block

When comparing, run `scripts/compare_scores.py`. Show:

- comparability state and reasons, including engine/registry/profile/weights/scope;
- audit fingerprints and `as_of` dates when traceability matters;
- score and coverage deltas;
- per-pillar deltas;
- check verdict changes;
- gates added/removed;
- freshness-policy changes when the verified platform state changed;
- evidence asymmetry warnings;
- observed visibility delta separately.

Do not declare a winner when registry/profile/pillar/surface scope is materially asymmetric.

## 13. One next step

End with one concrete next step implied by the evidence, not a menu of services.

## Style constraints

Lead with decisions and evidence, not generic SEO education. Use check IDs for traceability. Keep
search, training, indexing, user fetch, grounding, citation, and agent interaction distinct. Cite
current first-party docs for volatile platform claims when citations are supported.
