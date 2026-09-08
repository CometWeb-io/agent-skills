# Fix library

## Contents

1. Robots and platform-access patterns
2. WAF/CDN, canonical, robots previews
3. Titles, hreflang, answer blocks, tables
4. Optional `llms.txt`, Preferred Sources, IndexNow


Use these as implementation patterns after a finding is proven. Adapt every example to the real
site. Never output unresolved placeholders as if they were production-ready.

## 1. robots.txt - separate search visibility from model training

Absence of a specific `Disallow` normally means a bot is not blocked by robots.txt; explicit
`Allow: /` is mainly useful when repairing a conflicting group or documenting policy.

### ChatGPT Search visibility while opting out of GPTBot training

```text
User-agent: OAI-SearchBot
Allow: /

User-agent: GPTBot
Disallow: /
```

This pattern intentionally separates ChatGPT Search discovery from potential model-training access.
Re-check current OpenAI documentation before deployment.

### Anthropic search/retrieval while opting out of training collection

```text
User-agent: Claude-SearchBot
Allow: /

User-agent: Claude-User
Allow: /

User-agent: ClaudeBot
Disallow: /
```

Use only if this matches the site's policy. Re-check Anthropic's current agent definitions first.

### Perplexity discovery

```text
User-agent: PerplexityBot
Allow: /
```

Current Perplexity documentation says user-requested `Perplexity-User` fetches generally ignore
robots.txt, so do not sell a robots rule as complete control of that path. WAF/network policy may
need separate configuration.

### Google Search vs Google-Extended

Do not add or remove `Google-Extended` to fix AI Overviews/AI Mode visibility. Google currently
states that Google-Extended does not control Search inclusion or ranking.

A publisher may still choose a separate policy for Gemini model-development/grounding uses:

```text
User-agent: Google-Extended
Disallow: /
```

Only recommend this when the business explicitly wants that policy. Do not count it as a Search
visibility fix.

## 2. WAF/CDN bot access

When robots.txt appears permissive but first-party crawlers receive 403/429 or challenge pages:

1. inspect CDN/WAF logs;
2. verify the current first-party user agent and published IP verification method if one exists;
3. allow only the intended crawler traffic;
4. retest the exact page;
5. avoid broad bot bypasses that weaken site security.

Do not hardcode IP ranges in this skill because they can change.

## 3. Canonical

```html
<link rel="canonical" href="https://example.com/preferred-url/">
```

Use only when the preferred URL is genuinely equivalent or canonical for the page. Align internal
links, redirects, sitemap URLs, and hreflang with the canonical strategy.

## 4. Meta robots / preview controls

Normal indexable page:

```html
<meta name="robots" content="index,follow">
```

Explicit `index,follow` is usually redundant; use it only when it clarifies an existing conflicting
setup.

If an intended answer surface is being suppressed, inspect directives such as:

```html
<meta name="robots" content="max-snippet:-1,max-image-preview:large,max-video-preview:-1">
```

Do not override deliberate legal/licensing/privacy preview restrictions.

## 5. Title and meta description

Use page-specific copy, not mechanical length targets.

```html
<title>Primary page promise or subject | Brand</title>
<meta name="description" content="A concise, specific summary that accurately describes the page and gives a searcher a reason to choose it.">
```

Prioritize clarity, distinctiveness, intent fit, and consistency with visible content. Search
engines may rewrite title links or snippets.

## 6. Hreflang

Example for real localized equivalents:

```html
<link rel="alternate" hreflang="en-gb" href="https://example.com/uk/page/">
<link rel="alternate" hreflang="en-us" href="https://example.com/us/page/">
<link rel="alternate" hreflang="x-default" href="https://example.com/page/">
```

Add reciprocal annotations and keep canonical strategy aligned. Do not add hreflang to unrelated
regional pages.

## 7. Answer-first content block

Use when the page genuinely answers a question:

```html
<section aria-labelledby="cost-heading">
  <h2 id="cost-heading">How much does the service cost?</h2>
  <p>The standard plan starts at 199 PLN per month and includes A, B, and C. Final pricing changes with usage and contract scope.</p>
  <p>Explain the variables, evidence, examples, and exceptions here.</p>
</section>
```

The value comes from clarity and completeness, not from a magic sentence length.

## 8. Comparison table

Use only for consistent attributes:

```html
<table>
  <caption>Plan comparison</caption>
  <thead>
    <tr><th scope="col">Plan</th><th scope="col">Best for</th><th scope="col">Key limit</th></tr>
  </thead>
  <tbody>
    <tr><th scope="row">Starter</th><td>Small teams</td><td>5 projects</td></tr>
    <tr><th scope="row">Pro</th><td>Growing teams</td><td>25 projects</td></tr>
  </tbody>
</table>
```

Keep important caveats in nearby text rather than forcing nuance into tiny cells.

## 9. llms.txt - optional experiment, not a Google Search fix

Google currently says Search ignores `llms.txt`. Do not include this in Google Search/GEO scoring.

If the user wants to support another system that explicitly consumes the file, or wants a low-cost
cross-platform experiment, a minimal pattern can be:

```text
# Brand Name
> One-sentence description of what the organization/site is authoritative about.

## Key resources
- https://example.com/product/ - Primary product documentation
- https://example.com/research/ - Original research and methodology
- https://example.com/about/ - Organization and expert information
```

Keep it accurate and maintained. Do not claim it creates citations without platform evidence.

## 10. Google Preferred Sources - optional publisher distribution

Use only for an eligible publisher that wants to encourage existing readers to select it as a
preferred source. This is not a generic ranking fix and does not add MAXX points by itself.

Current official implementation includes a Google-provided button or deeplink. Re-check current
Search Central documentation before deployment because the library/API can change.

Decision test:

1. Is the site an eligible publisher/domain for Preferred Sources?
2. Does it have an audience/newsletter/community likely to opt in?
3. Is there a natural placement that does not degrade UX?
4. Can adoption be measured as a distribution experiment?

If no, skip it. Do not recommend it to every SaaS/service site merely because AI Overviews exist.

## 11. IndexNow - conditional freshness mechanism for Bing-supported discovery

Use when the site changes URLs/content frequently and participating search systems matter. It can
help notify supported engines that content was added, updated, or removed; do not present it as a
universal ranking boost.

Prefer CMS/platform-native integration when reliable. Validate that notifications use canonical
URLs, do not spam unchanged URLs, and complement rather than replace clean sitemaps/internal links.
