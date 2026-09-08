---
name: seo-geo-aeo-maxxing
description: >
  Run evidence-governed, multi-pillar website visibility audits across technical SEO, relevance,
  authority/trust, GEO/AI citation readiness, and AEO/answer extraction. Use when the user explicitly
  asks for SEO+GEO+AEO or "maxxing", a broad end-to-end search/AI visibility audit, cross-pillar
  diagnosis of ranking/AI-visibility problems, same-rubric competitor comparison, or a repeat/delta
  audit. Use PILLAR mode only when this skill is explicitly requested for one pillar. Do not trigger
  for isolated schema, one canonical/meta tag, keyword research, pure content writing, or a narrow
  implementation task better handled by a specialist skill. Diagnosis only; never mutate live sites.
---

# SEO / GEO / AEO Maxxing

Run one auditable diagnostic system across classic search, generative search, answer engines, and
answer extraction. Separate controllable readiness from observed visibility and business outcomes.

## Non-negotiable rules

- Diagnose; do not mutate the live site, CMS, repository, DNS, CDN, robots, analytics, or webmaster tools.
- Never invent rankings, traffic, backlinks, CWV, citations, impressions, crawler access, or conversions.
- Never turn a correlation, practitioner heuristic, or old SEO convention into a platform requirement.
- Never treat training access as search/citation access.
- Never call missing telemetry `0`.
- Never call a text-only fetch proof that JSON-LD is absent.
- Never score by feel when the bundled scoring scripts can run.
- Answer in the user's language while preserving technical identifiers.

## Workflow

1. Frame scope, archetype, business goal, critical URLs, and target surfaces.
2. Pick mode and scoring profile.
3. Check volatile platform-source freshness.
4. Generate a complete audit skeleton.
5. Collect target-specific evidence using a stratified sample.
6. Run active pillar checklists and conditional overlays.
7. Score mechanically.
8. Measure observed search/AI visibility separately.
9. Prioritize by dependency, business exposure, evidence, and effort.
10. For VERSUS/DELTA, run deterministic comparison.
11. Deliver using the output contract.

## Step 0 - Frame the audit without needless interrogation

Read `references/data-collection.md` and `references/site-archetypes.md`.

Capture or conservatively infer:

- site archetype(s);
- primary business goal;
- target market/language;
- target search/AI surfaces;
- critical URL classes and representative templates;
- priority query/task set when supplied or available from connected data;
- recent migrations/events relevant to a delta.

Label inferred context `INFERRED`. Ask only when missing context would materially change scope and
cannot be resolved from available evidence. Otherwise proceed and use `NOT_ASSESSED` for real gaps.

When the user explicitly cares about browser/transaction agents, also read
`references/agent-readiness.md`. Keep that overlay outside MAXX unless the registry is extended.

## Step 1 - Pick mode and profile

| Mode | Use | Scoring semantics |
|---|---|---|
| `RECON` | quick symptom/page check | Focused readiness only |
| `FULL` | broad domain audit | all 5 pillars; eligible for MAXX |
| `PILLAR` | explicit one/few-pillar request | Focused readiness only |
| `VERSUS` | competitor comparison | same registry/profile/scope on both sides |
| `DELTA` | previous audit exists | same registry/profile/scope when possible |

Profiles:

- `balanced` - default broad audit;
- `classic-search` - brief is primarily organic Search;
- `ai-first` - explicit priority is AI discovery/citation readiness.

Do not silently invent custom weights.

A Foundation dependency may matter in PILLAR mode. Either expand the active scope and run the full
Foundation checklist, or report the dependency as a non-scored diagnostic note. Never score one
Foundation check as if it represented the whole Foundation pillar.

## Step 2 - Freshness gate

Read `references/live-source-registry.md` and machine state in
`references/live-source-registry.json`.

Before volatile GEO/AEO claims, run when code is available:

```bash
python scripts/check_freshness.py --strict
```

Volatile topics include crawler names/purposes, robots controls, AI-search eligibility, measurement
products, structured-data feature support, `llms.txt`, agent guidance, and referral conventions.

If a required group is stale, refresh current first-party sources. Platform-specific scoring will
refuse stale bundled facts. It also rejects bundled knowledge verified after a historical audit's
`as_of` date, preventing temporal leakage. Supply an appropriate official-source override, for example:

```json
"freshness_overrides": {
  "openai_search": {
    "verified_at": "2026-08-25",
    "sources": ["https://help.openai.com/en/articles/12627856-publishers-and-developers-faq"]
  }
}
```

If current first-party evidence cannot be obtained, keep the claim narrow and label it `UNVERIFIED`.

## Step 3 - Generate the complete audit skeleton

Use `references/check-registry.json` as the closed registry. Do not omit inconvenient checks.

When code is available, create the skeleton first:

```bash
python scripts/build_audit_template.py --mode FULL --subject https://example.com/ > audit.json
```

Examples:

```bash
python scripts/build_audit_template.py --mode PILLAR --pillars geo --surfaces chatgpt-search,google-ai-search > audit.json
python scripts/build_audit_template.py --mode FULL --profile ai-first --archetypes saas,multilingual > audit.json
```

The generator starts applicable checks as `NOT_ASSESSED` and marks out-of-scope platform checks
`N/A`. Fill the skeleton with evidence; do not rebuild a hand-selected checklist from memory.

## Step 4 - Collect evidence

Read `references/evidence-policy.md`.

Every active check must end as one of:

- `PASS`
- `WEAK`
- `FAIL`
- `N/A`
- `NOT_ASSESSED`

Scored verdicts require target-specific evidence. Generic platform documentation alone cannot prove
the target site passes. Use evidence objects:

```json
{
  "id": "GEO-06",
  "verdict": "PASS",
  "evidence": [
    {
      "class": "E2_SITE_DIRECT",
      "artifact": "robots.txt does not disallow OAI-SearchBot on critical public paths",
      "source": "https://example.com/robots.txt"
    },
    {
      "class": "E1_FIRST_PARTY_LIVE",
      "artifact": "Current OpenAI publisher guidance identifies OAI-SearchBot as the Search control",
      "source": "https://help.openai.com/en/articles/12627856-publishers-and-developers-faq"
    }
  ]
}
```

For conditional `N/A`, supply both a reason and target-specific `applicability_evidence`. If
applicability is merely unknown, use `NOT_ASSESSED`.

For sampled templates, use `distribution` when it preserves more truth than a coarse verdict:

```json
"distribution": {"pass": 7, "weak": 0, "fail": 1}
```

Do not make sitewide claims from a page sample. State sample/template scope.

## Step 5 - Run pillar checklists

Load only what the active scope needs:

| Pillar | Checklist |
|---|---|
| Foundation | `references/pillar-foundation.md` |
| Relevance | `references/pillar-relevance.md` |
| Authority | `references/pillar-authority.md` |
| GEO | `references/pillar-geo.md` |
| AEO | `references/pillar-aeo.md` |

Use `references/schema-library.md` and `references/fix-library.md` only after a concrete finding
needs implementation guidance.

Important schema safeguard: static/text extraction may strip JSON-LD. Before saying `schema absent`,
follow the rendered/validator protocol in `references/data-collection.md`; otherwise use
`NOT_ASSESSED`.

## Step 6 - Score mechanically

Read `references/scoring.md`, then run:

```bash
python scripts/score_maxx.py audit.json > score.json
```

Key semantics:

- MAXX exists only when all five pillars are active.
- Any subset outputs `Focused readiness`, never a whole-site MAXX tier.
- `NOT_ASSESSED` reduces coverage; it is not zero.
- A composite score is withheld when any active pillar has less than 50% weighted evidence coverage;
  50-74.9% remains provisional.
- Conditional `N/A` is evidence-gated; core checks cannot be hidden as N/A.
- Scored verdicts require target-specific E2/E3/E4 evidence.
- Critical gates require direct/reproducible/connected evidence and must agree with related checks.
- Platform checks self-expire when bundled source facts exceed their TTL.
- Evidence grade describes audit support, not ranking/citation probability.

If code execution is unavailable, reproduce registry math exactly, show the arithmetic, enforce the
same N/A/evidence/freshness/gate rules, and label the result `manual registry calculation`.

## Step 7 - Keep observed visibility separate

Read `references/measurement.md`.

Use actual data when available, such as:

- Search Console Generative AI reporting when the property has access;
- Bing Webmaster Tools AI Performance and current AI visibility views;
- analytics referrals and conversions;
- connected third-party longitudinal panels;
- a fixed prompt sample clearly labeled directional.

Do not convert missing measurement into `0 citations` or `0 impressions`.

## Step 8 - Prioritize

Read `references/prioritization.md`.

Resolve gates/prerequisites before downstream optimization. Score Impact x Confidence x Ease, but
include affected template/business scope and cap Confidence by evidence. Label recommendations as
`REMEDIATION`, `MEASUREMENT`, or `EXPERIMENT`.

Return at most 3 actions for this week and 5-7 for this month. Return fewer when evidence does not
justify more. Never pad.

## Step 9 - Compare VERSUS / DELTA deterministically

Score each side separately, preserving registry/profile/pillars/target surfaces, then run:

```bash
python scripts/compare_scores.py before.json after.json --kind delta
python scripts/compare_scores.py site-a.json site-b.json --kind versus
```

If scoring engine, registry, profile/weights, pillar set, or surface scope differs, mark totals
non-comparable. If evidence coverage is materially asymmetric, warn before declaring a winner. Use
output fingerprints for traceability and keep observed-visibility deltas separate from readiness
score deltas.

## Step 10 - Deliver

Read `references/output-contract.md`.

Lead with the decision, gate, or dominant uncertainty. Show scope, coverage, evidence grade, score,
observed visibility, platform controls when relevant, material findings, prioritized actions, and
not-assessed gaps. End with one concrete next step.

## Anti-pattern guardrails

- Title/meta length ranges are heuristics, not ranking pass/fail thresholds.
- Multiple H1s or skipped heading levels are not automatic Google Search failures.
- E-E-A-T is a quality/trust framework, not one Google ranking factor.
- Structured data is not a generic ranking or AI-citation boost.
- Current Google generative Search does not require special AI schema or `llms.txt`.
- Do not confuse `Google-Extended` with Google Search eligibility.
- Do not confuse GPTBot/ClaudeBot training access with search access.
- FAQ/HowTo rich-result advice must reflect current platform support, not historical SEO playbooks.
- Query fan-out supports real task/topic coverage; it is not permission for scaled thin query pages.
- Google Preferred Sources is an optional user-selected publisher distribution feature, not a
  generic ranking hack or score bonus.
- AEO means extraction readiness, not guaranteed snippets/PAA/voice/AI citation.
- Agent interaction readiness is separate from search/citation readiness.

## Bundled modules

```text
references/
  data-collection.md
  evidence-policy.md
  site-archetypes.md
  live-source-registry.md
  live-source-registry.json
  check-registry.json
  pillar-foundation.md
  pillar-relevance.md
  pillar-authority.md
  pillar-geo.md
  pillar-aeo.md
  agent-readiness.md
  measurement.md
  scoring.md
  prioritization.md
  fix-library.md
  schema-library.md
  output-contract.md
scripts/
  build_audit_template.py
  check_freshness.py
  score_maxx.py
  compare_scores.py
evals/
  regression-cases.md
```
