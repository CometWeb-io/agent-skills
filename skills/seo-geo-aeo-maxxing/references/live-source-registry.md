# Live source registry

Human-readable control plane for volatile platform facts. Machine state lives in
`live-source-registry.json` and is enforced by the scoring script.

Last verified: 2026-08-25. Default TTL: 30 days.

## Refresh protocol

Run `python scripts/check_freshness.py --strict` before relying on volatile platform behavior. If a
required group is stale, refresh official sources and record a live override in the audit rather
than silently using old memory.

Prioritize official product docs, official changelogs/blogs, first-party help centers, then
reproducible first-party product data. Keep secondary research out of platform-control claims.

## Current platform guardrails

### Google generative Search

- AI Overviews and AI Mode remain rooted in Google Search systems and indexed content.
- Google Search does not use `llms.txt` as a special visibility mechanism.
- `Google-Extended` is not the control for Google Search inclusion/ranking.
- No special schema is required for Google generative Search.
- Search Console Generative AI reports began rolling out to a subset of properties in June 2026.
  Current announced dimensions include impressions, pages, countries, devices for Search, and dates;
  do not invent a query dimension that the report does not expose.
- Google confirms query fan-out, but explicitly warns against scaled pages created merely for every
  fan-out variant.
- Preferred Sources can highlight publishers selected by a user in eligible Top Stories, AI Mode,
  and AI Overviews. Publisher buttons/deeplinks are optional audience-distribution mechanisms, not
  a generic ranking requirement.

### OpenAI / ChatGPT Search

- `OAI-SearchBot` is the publisher control relevant to ChatGPT Search summaries/snippets.
- `GPTBot` is separate model-development/training access.
- Robots permission is not enough if host/CDN/WAF blocks the current search path; verify current
  OpenAI network guidance when diagnosing a fetch denial.
- OpenAI notes that a disallowed page URL/title can still be surfaced in Atlas when discovered by
  other signals; do not translate an OAI-SearchBot block into universal URL invisibility.
- Current publisher guidance documents `utm_source=chatgpt.com` for ChatGPT Search referrals.

### Anthropic / Claude

Keep `ClaudeBot` (model development), `Claude-SearchBot` (search), and `Claude-User` (user-directed
retrieval) separate. Their controls are independent.

### Perplexity

`PerplexityBot` is the search/discovery crawler in current first-party docs. `Perplexity-User`
handles user-requested fetches and is documented as generally ignoring robots.txt. WAF/network
controls can still affect actual access.

### Microsoft Bing / Copilot

Bing Webmaster Tools AI Performance exposes AI citation activity across supported Microsoft AI
experiences. By June 2026 Microsoft had also announced Intents, Topics, Citation Share, and Compare.
Use Bing indexing/BWT/sitemaps/IndexNow evidence; do not invent a generic `CopilotBot` requirement.

### Google structured-data support

Feature support changes. FAQ rich results stopped appearing in Google Search in May 2026; HowTo rich
results are deprecated. Check the current Search Gallery before promising a Google rich result.

## Machine registry groups

- `google_ai_search`
- `openai_search`
- `anthropic_crawlers`
- `perplexity_crawlers`
- `microsoft_ai_search`
- `google_structured_data`
- `openai_agent`

Each group stores official URLs, verification date, TTL, and current claims in
`live-source-registry.json`.

## Maintenance rule

When an official source materially changes, update the affected JSON group and this summary. If the
change affects applicability or scoring semantics, update `check-registry.json` and regression tests
in the same change. Do not rewrite unrelated audit logic.
