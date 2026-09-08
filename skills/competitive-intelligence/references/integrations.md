# Integrations and Routing

## Contents

1. Context sources
2. Public research sources
3. GitHub
4. Notion and knowledge bases
5. Scheduling
6. Compatibility with competitor-profiling
7. Cross-skill handoffs
8. Tool failure behavior

## 1. Context sources

Before interpreting competitor changes, load the user's own product context when available:

- product/marketing context file,
- roadmap/product docs when the user has authorized access,
- pricing/packaging context,
- ICP and positioning,
- active strategic decisions.

Competitive significance is relative. The same competitor move can be critical for one product and irrelevant for another.

## 2. Public research sources

Use web/search/browser tooling for public sources. Prefer direct pages for current competitor claims. Use secondary discovery sources to find evidence, then open the strongest source.

Do not hardcode vendor-specific search/scraping tools as mandatory. When specialist tools such as Firecrawl, DataForSEO, Similarweb, ad libraries, or review platforms are available, use them according to their own policies and label estimated/derived metrics appropriately.

## 3. GitHub

For competitors with public repositories, monitor only public or authorized repositories.

High-value signals include:

- releases/tags,
- changelog/release notes,
- public docs changes,
- newly public integrations/examples,
- deprecations,
- issue/release patterns when they directly support a product claim.

Do not interpret raw commit volume as product velocity without context.

## 4. Notion and knowledge bases

Use Notion/Drive/internal docs as a human-facing intelligence layer when requested. Keep machine-comparable snapshot/event state in a deterministic file or structured database when possible.

Recommended split:

- repository/filesystem: canonical snapshots, hashes, event log,
- Notion: watchlist dashboard, briefs, decisions, owners, human notes.

Never embed private Notion IDs, tokens, or workspace secrets in the public skill bundle.

## 5. Scheduling

This skill executes one cycle. For recurring monitoring:

- use a scheduler/automation when available,
- use `marketing-loops` when the user wants a repeatable marketing workflow around the intelligence,
- use a condition watch for high-impact alerts when supported,
- use scheduled digests for routine summaries.

Persist state before scheduling so each future run can compute a real delta.

## 6. Compatibility with competitor-profiling

If an existing `competitor-profiles/` tree is present, reuse it as baseline evidence rather than redoing expensive research.

Typical existing layout:

```text
competitor-profiles/
├── raw/<competitor-slug>/<YYYY-MM-DD>/...
├── <competitor-slug>.md
└── _summary.md
```

Import rules:

- Treat dated raw folders and source references as provenance inputs.
- Treat the synthesized Markdown profile as a convenient extraction source, not immutable machine truth.
- Normalize factual fields into `.competitive-intelligence/snapshots/...` before computing deltas.
- Keep qualitative `Strengths`, `Weaknesses`, `Opportunities`, and `Threats` as implications/hypotheses unless separately evidenced.
- Do not rewrite or delete the legacy `competitor-profiles/` data.
- Record the legacy profile/raw path in evidence notes when it materially supports the baseline.

Suggested mapping:

| competitor-profiling section | CI snapshot area |
|---|---|
| Positioning & Messaging | `state.positioning` |
| Product & Features | `state.product` |
| Pricing | `state.pricing` |
| Customers & Social Proof | `state.proof` |
| SEO & Content Strategy | `state.discovery` |
| Company facts from At a Glance/About | `state.company` |
| Strengths/Weaknesses/Implications | analytical layer, not direct normalized fact |

## 7. Cross-skill handoffs

Route by job-to-be-done:

| Trigger from CI | Handoff |
|---|---|
| Need initial deep baseline | `competitor-profiling` |
| Need public comparison/alternative page | `competitors` |
| Need sales battlecard/objection response | `sales-enablement` |
| Competitor price move may require our pricing change | `pricing` |
| New positioning/category threat | `product-marketing` / `copywriting` |
| Ads/creative shift | `ads` / `ad-creative` |
| SEO/content movement | `seo-audit`, `ai-seo`, `seo-geo-aeo-maxxing` |
| Review or win/loss pattern | `customer-research` |
| Material strategic response | `ai-council` |
| Recurring operational workflow | `marketing-loops` / scheduler |

Pass only accepted facts, timestamps, source references, and clearly labeled hypotheses into the next skill.

## 8. Tool failure behavior

If a source/tool is unavailable:

1. Do not silently substitute a weaker source as equivalent.
2. Mark coverage as missing or degraded.
3. Continue with unaffected sources when useful.
4. Downgrade verification state/confidence where necessary.
5. Avoid updating `current.json` for fields whose new state is unknown merely because collection failed.
