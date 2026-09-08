# Pillar 4 - GEO / AI citation readiness

Purpose: evaluate controllable readiness for AI-mediated search/retrieval and source selection.
Observed citations/outcomes belong in `measurement.md`.

## Keep this chain separate

1. `ACCESS`: can the relevant path fetch the page?
2. `INDEX/RETRIEVAL`: can it obtain a useful representation?
3. `SELECTION`: does the source contain relevant, differentiated, trustworthy information?
4. `CITATION`: was it actually referenced?
5. `OUTCOME`: did visibility influence useful behavior?

MAXX scores mainly 1-3. Never infer 4-5 from readiness.

## Platform control model

Re-check the live registry before current claims.

- ChatGPT Search: evaluate `OAI-SearchBot` plus demonstrated host/CDN/WAF access. Keep `GPTBot`
  training preference separate.
- Claude: distinguish `Claude-SearchBot`, `Claude-User`, and training-oriented `ClaudeBot`.
- Perplexity: evaluate `PerplexityBot` and actual network access; user-requested fetch behavior is a
  separate path.
- Google AI Overviews/AI Mode: evaluate Google Search eligibility/indexability. Do not award points
  for `Google-Extended`, special AI schema, or `llms.txt` as Search requirements.
- Bing/Copilot: use Bing indexing/BWT evidence, sitemaps/IndexNow where relevant, and current
  first-party guidance. Do not invent a generic Copilot crawler.

## GEO-01 - Public/indexable source availability

Check important pages for public access and index eligibility where the target system depends on a
search index. Separate deliberate preview/licensing restrictions from accidental blocks.

## GEO-02 - Citation-worthy original information

Look for primary facts, first-hand experience, original data/research, methodology, defensible
expert interpretation, useful comparison criteria, concrete examples, or current product/service
facts. Generic commodity summaries are weak even if perfectly formatted.

## GEO-03 - Attributable claims and source clarity

Check whether important claims can be verified and attributed: named sources, dates/versions,
methodology/definitions, primary-source links when appropriate, and a clear distinction between the
site's own finding and third-party facts.

## GEO-04 - Entity disambiguation

Check organization/product/person naming, stable URLs, about/product context, real external identity
links, and structured data that agrees with visible content. Do not equate `Person`/`Organization`
schema with authority by itself.

## GEO-05 - Freshness of material facts

Apply where facts change. Verify substantive update state and distinguish historical from current
facts. Use N/A with applicability evidence for genuinely timeless material.

## GEO-06 - ChatGPT Search discovery

Score target-specific `OAI-SearchBot`/fetch accessibility. A blocked `GPTBot` alone must not reduce
this check. If robots permits search but the CDN returns 403/429/challenge to the current verified
path, score the demonstrated access problem. Do not call the URL universally invisible: current
OpenAI guidance allows limited link/title surfacing in Atlas from other discovery signals.

## GEO-07 - Claude search/retrieval

Score current `Claude-SearchBot` and relevant user-directed retrieval accessibility. Keep
`ClaudeBot` training policy out of the visibility verdict.

## GEO-08 - Perplexity discovery/retrieval

Score `PerplexityBot` and demonstrated network accessibility. Do not claim robots gives complete
control over user-requested retrieval when first-party documentation says otherwise.

## GEO-09 - Google generative Search eligibility

Score Google Search discovery/index eligibility and relevant Search Console evidence. No bonus for
`llms.txt` or Google-Extended.

Google confirms query fan-out in generative Search. Use it to think in real user tasks and topic
coverage, but do not create scaled thin pages for every imagined fan-out query. Strengthen genuine
coverage under REL-04 instead.

Google Preferred Sources is an optional publisher-distribution opportunity for eligible domains and
users who choose that publisher. It is not a generic ranking requirement or a MAXX bonus.

## GEO-10 - Bing/Copilot discovery eligibility

Score Bing discovery/indexing using Bing/BWT evidence. IndexNow may be useful for freshness where
appropriate; do not present it as a universal ranking boost.

## Optional agent overlay

If the user cares about browser/transaction agents, load `agent-readiness.md`. Report it separately
from GEO/MAXX unless the registry is explicitly extended.
