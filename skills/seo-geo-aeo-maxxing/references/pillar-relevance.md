# Pillar 2 - Relevance

Purpose: determine whether each page clearly satisfies a real user/search task with differentiated,
accurate, discoverable content. Avoid mechanical keyword-count rules.

## REL-01 - Title and main-title clarity

Evaluate whether the `<title>` and visible main title:

- accurately identify the page;
- are unique enough across the sampled site;
- match the page's real purpose and search intent;
- avoid boilerplate that hides the distinguishing topic;
- are concise enough to be useful to humans.

Character counts are heuristics, not pass/fail thresholds. Multiple `H1` elements are not an
automatic Google Search failure. Flag heading structure only when it harms comprehension,
accessibility, or title interpretation.

## REL-02 - Primary intent satisfaction

Identify the dominant task/query class for the page and test whether the page solves it quickly.
Examples:

- commercial/service: what it is, who it is for, proof, constraints, next action;
- product: specifications, price/availability when applicable, comparison, evidence, purchase path;
- informational: direct answer, explanation, examples, edge cases, sources;
- local: service + location relevance, real business information, local proof;
- comparison: criteria, tradeoffs, evidence, explicit conclusion.

Do not score exact-match keyword repetition as intent satisfaction.

## REL-03 - Unique non-commodity value

Look for information that is difficult to replace with a generic summary:

- first-hand experience;
- original data or analysis;
- proprietary process or methodology;
- concrete examples/case studies;
- expert reasoning;
- primary-source facts;
- product/service details only the operator can know.

A long article composed of generic restatements can still `FAIL` this check. Word count is not a
quality target.

## REL-04 - Topical/task completeness

Assess whether the page covers the decisions a serious user needs to make without padding.

Look for material omissions, not arbitrary subheading quotas. Use competitor/SERP evidence when
available to discover missing user questions, but do not copy competitor structure mechanically.

For generative-search query fan-out, cover real adjacent tasks where they belong in the topic/product
journey. Do not manufacture one thin page for every imagined subquery.

## REL-05 - Internal contextual discovery

Check whether important pages receive meaningful internal links from relevant contexts and whether
users can move between related topics naturally.

Prefer descriptive anchor context over sitewide footer spam. A page can be in the sitemap and still
be weakly integrated into the site.

## REL-06 - Duplication/cannibalization control

Look for multiple pages competing for substantially the same intent without a deliberate reason.
Use page content, titles, canonicals, internal links, and connected query data where available.

Do not label every related article as cannibalization. Require real intent overlap or query evidence.

## REL-07 - Accuracy and freshness where material

Freshness is conditional. Score it strongly for topics where facts, prices, regulation, software,
products, statistics, or availability change. Use `N/A` where evergreen content does not need
frequent updates.

Check whether dates reflect substantive updates rather than cosmetic timestamp changes. For content
that teaches search engines, AI platforms, law, standards, software, pricing, or other changing
systems, verify consequential factual claims against current primary sources before calling the page
accurate. A recent `dateModified` does not rescue stale instructions.

## REL-08 - Useful media/data support

Reward images, diagrams, video, tables, calculators, screenshots, datasets, or downloadable
artifacts only when they materially improve the user's task.

Do not recommend video or images as generic GEO theater. The question is whether they add useful,
indexable information and a distinct discovery surface.
