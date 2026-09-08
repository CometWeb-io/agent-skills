# Data collection protocol

## Contents

1. Context frame
2. Anchor artifacts
3. Stratified sampling
4. Technical evidence
5. Structured-data detection
6. JavaScript/rendering
7. Query/index evidence
8. Connected sources
9. Competitor/delta protocol


Collect enough evidence to answer the requested scope. Do not make a sitewide claim from one page.

## 1. Build the context frame first

Record, or infer and label `INFERRED` when public evidence is sufficient:

- site archetype(s): SaaS/lead-gen, ecommerce, local, publisher, docs, marketplace, YMYL, multilingual;
- business goal: lead, sale, signup, subscription, audience, support, other;
- target market and language;
- target search/AI surfaces;
- critical URL classes and representative templates;
- priority query/task set when supplied or available from connected data;
- recent migration, redesign, domain, CMS, or content events that can explain a delta.

Do not stop the audit merely because a user did not provide every context field. Infer conservatively,
label the inference, and put materially uncertain items under `NOT_ASSESSED`.

## 2. Anchor artifacts

For a domain-level audit, inspect at minimum:

- supplied URL or homepage;
- `/robots.txt`;
- sitemap location(s), discovered from robots/common paths where needed;
- HTTP status and redirect target for critical URLs;
- canonical, meta robots, title, main visible title, navigation, meaningful body content;
- structured data using a method that can actually observe it;
- rendered page/DOM when raw retrieval appears incomplete or client-rendered.

`/llms.txt` is optional discovery evidence, never an automatic finding. Follow the live registry.

## 3. Use stratified page sampling

For `FULL`, default to 10-15 high-signal URLs when available. Sample by both business criticality and
repeated template, not by the first URLs in a sitemap. Include a reasonable mix of homepage,
commercial/product/service, informational, trust/about, contact/local, comparison/case-study,
and representative repeated templates.

For large sites, record directory/template coverage and sample size. A finding observed on 3 of 4
sampled product pages may support a template-level hypothesis; it does not prove all product pages
share the defect until template or crawl evidence closes that gap.

## 4. Technical evidence

Collect when available:

- status/redirect chain;
- `robots.txt` by relevant crawler token;
- `meta robots` and `X-Robots-Tag`;
- canonical and hreflang where applicable;
- sitemap inclusion and trustworthy `lastmod` where useful;
- main content in raw HTML and rendered DOM;
- mobile/responsive behavior;
- server/browser errors relevant to discovery;
- lab speed only when a real lab tool was run;
- field CWV only from CrUX/GSC/RUM or another defensible field source.

Never infer field CWV from framework, page weight, markup, or screenshots.

## 5. Structured-data detection limitation

A text extractor, static fetch, or converted page view can strip `<script>` tags or miss JSON-LD
injected by client-side code. `No JSON-LD visible in this fetch` is not proof that the page has no
structured data.

Before a schema absence becomes `FAIL`, use at least one suitable path:

1. rendered DOM/browser inspection of `script[type="application/ld+json"]`;
2. Google Rich Results Test or another target-platform validator when appropriate;
3. Search Console enhancement data when connected;
4. a JavaScript-rendered crawl/export such as Screaming Frog.

If none is available, use `NOT_ASSESSED` rather than a false negative.

## 6. JavaScript/rendering protocol

When raw HTML lacks critical content:

1. inspect rendered output if available;
2. identify the intended search/index/retrieval path;
3. test that path when possible;
4. name the exact failure mode: raw-content absence, blocked script, WAF challenge, render timeout,
   interaction dependency, authentication, rate limit, or `not tested`.

JavaScript alone is never a `FAIL`. Apply `CONTENT_UNAVAILABLE_TO_SEARCH_FETCH` only after a direct
test demonstrates that critical content cannot be retrieved through the intended path.

## 7. Query and index evidence

Use the user's priority query set, GSC/BWT query data, or a documented research set. Do not invent a
"target keyword" because a phrase appears in the title. Treat `site:` searches, spot SERPs, and
index-count estimates as discovery clues, not authoritative index counts.

## 8. Connected sources

Prefer first-party/connected evidence when available: GSC, BWT, GA4 or equivalent analytics,
CDN/WAF logs, CMS read-only data, and defensible third-party link/rank datasets. Label third-party
estimates as third-party even when connected.

## 9. Competitor and delta modes

Use the same registry, profile, target surfaces, evidence protocol, and comparable page types on both
sides. For `DELTA`, preserve the prior audit's registry/profile when possible. Never declare a winner
from materially asymmetric evidence coverage.

Before scoring, be able to state URLs/templates inspected, raw/rendered coverage, connected sources,
platform sources refreshed, sample limits, and remaining material gaps.
