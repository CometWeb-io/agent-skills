# Pillar 1 - Foundation

Purpose: determine whether important content can be discovered, fetched, indexed, consolidated, and
served reliably. Use exact check IDs from `check-registry.json`.

## FND-01 - Critical-page index eligibility

Inspect representative critical pages for noindex in meta/X-Robots, search-crawler blocks,
auth/access barriers, and connected index evidence where available. Sitemap absence is not noindex.
Use critical gates only with direct/reproducible/connected target evidence.

## FND-02 - HTTP status and redirect integrity

Check intended live URLs for usable final status, chains/loops, soft-404 behavior, 4xx/5xx, and
redirect/canonical conflicts. Do not gate intentionally removed URLs.

## FND-03 - Canonical consistency

Evaluate whether canonical signals point to the intended equivalent version and agree with redirects,
internal links, sitemap URLs, hreflang, and page content. Self-referencing canonical is not a magic
requirement on every page; consistency/risk is what matters.

## FND-04 - Robots and crawl directives

Evaluate by function, not the word `bot`. General Google/Bing Search access belongs here. Platform-
specific GEO agents belong in GEO checks. Deliberately blocking training crawlers while allowing
search must not cause a Foundation fail.

## FND-05 - Sitemap and discovery hygiene

Check reachability, parseability, intended canonical/indexable URLs, sensible splitting, and honest
`lastmod` where used. Robots sitemap pointers are useful but not required for sitemap validity. A tiny
well-linked site without XML sitemap may be WEAK rather than FAIL.

## FND-06 - Critical content retrievability/rendering

Ask whether the intended search/index path can obtain critical content. Compare raw and rendered
content when needed and diagnose the exact failure: interaction dependency, blocked script, WAF,
auth, consent wall, rate limit, render timeout, or not tested. JavaScript alone is never FAIL.

Apply `CONTENT_UNAVAILABLE_TO_SEARCH_FETCH` only after a direct/reproducible test demonstrates the
problem on critical content.

## FND-07 - Mobile/responsive baseline

Check viewport, critical content/function parity, accidental mobile hiding, overlays, and basic
usability. Do not infer mobile performance metrics from screenshots.

## FND-08 - Performance evidence and CWV health

Use CrUX/GSC/RUM for field claims and Lighthouse/PageSpeed only for lab diagnostics. If defensible
data is absent, use NOT_ASSESSED. Never estimate LCP/INP/CLS/TTFB from markup or framework choice.

## FND-09 - Internationalization/hreflang

Conditional. For separate localized URLs, check valid language/region codes, reciprocity, canonical
alignment, return links, and x-default where useful. A single-language/single-market site may use N/A
only with applicability evidence. Do not recommend hreflang without localized URL variants.

## Structured-data caveat

Schema absence is not a Foundation finding from a text-only fetch. Static extraction can strip
JSON-LD. Use the rendered/validator protocol in `data-collection.md`.

## Sitewide language rule

Do not turn a sampled page defect into a sitewide gate. Sitewide claims require crawl/template/
connected evidence proportionate to the claim.
