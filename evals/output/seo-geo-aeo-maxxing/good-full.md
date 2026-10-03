# SEO + GEO + AEO audit — example.com

## 1. Verdict

Answer extraction is the binding constraint: the pages rank for their topics but bury the answers, so AI surfaces cite competitors for questions example.com already covers.

## 2. Scope and evidence

- Mode: FULL; registry version 3.0.0; scoring profile `default`
- Site archetype: SaaS marketing site (INFERRED from navigation and pricing page)
- Target surfaces: Google Search, Google AI features, ChatGPT Search, Perplexity, Bing/Copilot
- Sampled: 24 URLs across 4 templates (home, product, blog post, docs); critical URL classes: pricing, signup
- Raw vs rendered: 24/24 fetched raw and rendered
- Connected data: Google Search Console (28 days); no analytics connection
- Volatile platform groups refreshed: crawler user agents, AI feature eligibility (2026-09-29)
- Sample limitation: docs subdomain sampled at 6 of roughly 300 pages

## 3. Readiness score

| Pillar | Score | Coverage | Evidence | State |
|---|---:|---:|---|---|
| Foundation | 78 | 100% | A | scored |
| Relevance | 64 | 91% | B | scored |
| Authority | 58 | 80% | B | scored |
| GEO | 55 | 80% | A | scored |
| AEO | 70 | 100% | B | scored |

`MAXX 65/100 - Competent (balanced; 87% coverage; evidence B)`

Active gates: none.

## 4. Observed search / AI visibility

| Outcome signal | Result | Window | Source |
|---|---:|---|---|
| Google Search clicks | 3,120 | 28d | GSC |
| Sampled prompt citation rate | 3/20 | fixed panel | directional sample |

## 6. Findings that matter

### AEO-01 — WEAK

- Evidence: 14 of 18 blog posts open with 120+ words of context before the answer (E2_SITE_DIRECT, rendered DOM).
- Scope: blog template, 18 sampled posts.
- Why it matters: answer extraction favours a direct first sentence; this lowers the chance of being quoted, not a guaranteed ranking effect.
- Next step: rewrite the first paragraph of the top 10 posts by GSC impressions.

### GEO-03 — WEAK

- Evidence: 9 of 12 statistics on product pages have no visible source (E2_SITE_DIRECT).
- Scope: product template.
- Why it matters: unattributed numbers are harder to cite and easier to dispute.
- Next step: add a source line under each statistic.

## 7. Top actions - this week

1. REMEDIATION — AEO-01: answer-first opening on the top 10 posts by impressions. Target evidence: first sentence answers the title question. Impact 4 / Confidence 4 / Ease 4 / ICE 64.
2. REMEDIATION — GEO-03: source lines for product-page statistics. Target evidence: every statistic has a visible source. Impact 3 / Confidence 4 / Ease 5 / ICE 60.
3. MEASUREMENT — connect analytics so AI referral sessions can be counted. Target evidence: referral sessions by source for 28 days. Impact 3 / Confidence 5 / Ease 4 / ICE 60.

## 9. Preserve

- FND-03 canonical tags are consistent across all sampled templates; keep them when rewriting posts.

## 10. Not assessed / scope limits

- AUT-05 external reputation: not tested (no backlink data source connected). Fastest source: a backlink export for the domain.
- Docs subdomain beyond 6 sampled pages: not tested, not "not present".

## 11. Experiments/backlog

- EXPERIMENTAL: a short "key facts" box on product pages to test citation rate on the fixed prompt panel.

## 13. One next step

Rewrite the opening paragraph of the 10 highest-impression posts to answer the title question in the first sentence, then re-run the fixed prompt panel in four weeks.
