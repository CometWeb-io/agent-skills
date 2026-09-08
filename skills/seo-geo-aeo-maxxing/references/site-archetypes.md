# Site archetype overlays

Use archetypes to decide applicability, sampling, critical URLs, and likely owners. Do not add hidden
score weights. A site may have multiple overlays.

## SaaS / lead generation

Prioritize homepage, solution/use-case pages, pricing when public, integration/comparison pages,
proof/case studies, docs/help, and conversion paths. Verify product claims and differentiation rather
than forcing blog volume.

## Ecommerce

Prioritize category, product, variant, availability/price facts, merchant policies, faceting,
canonicalization, product structured data where eligible, image discovery, and freshness. Use
Merchant Center/BWT/GSC when connected. Never invent price, stock, ratings, shipping, or returns.

## Local business

Prioritize real business identity, service/location intent, contact/hours/address facts, local proof,
and profiles such as Google Business Profile or Bing Places when connected. Do not demand
character-for-character NAP formatting when the facts clearly match.

## Publisher / editorial

Prioritize authorship/editorial provenance, dates/corrections, source quality, article templates,
news/video surfaces where relevant, and audience distribution. Google Preferred Sources can be an
optional publisher tactic for eligible domains; it is not a general ranking requirement and is not a
MAXX scoring bonus by itself.

## Developer docs / technical documentation

Prioritize version clarity, stable canonical current docs, old-version handling, changelogs,
searchable navigation, copyable code, exact errors/constraints, stable anchors, and rendering.
`llms.txt` is optional and platform-specific; do not score it as Google visibility.

## Marketplace / directory

Prioritize crawl control for faceting/parameters, thin template prevention, entity uniqueness,
internal discovery, stale inventory, pagination, and canonical intent. Sample by template and
inventory segment rather than a few handpicked records.

## YMYL / high-stakes

Apply `AUT-07`. Prioritize provenance, expert review where appropriate, primary sources, update
policy, limitations, safety/legal/financial/medical clarity, and trustworthy ownership. Do not infer
expertise from schema alone.

## Multilingual / multi-regional

Apply `FND-09`. Prioritize language/region URL strategy, canonical/hreflang consistency, fully useful
localized content, local market intent, and index evidence. Do not add hreflang if there are no
separate localized URLs.

## Choosing overlays

Infer only from public/site evidence when obvious and label it `INFERRED`; otherwise record the
uncertainty. Archetypes affect what should be checked, not the underlying platform rules.
