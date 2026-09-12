# Measure visibility without inventing ranking rules

Maintainer review: 2026-09-12. This date does not certify live task inputs.

Separate crawl access, index eligibility, rendering, canonical selection, retrieval,
answer inclusion, citation, click-through, and conversion. A crawl allowance is not an
indexing guarantee; a citation is not a visit; a single manual prompt is not market share.
Use defined prompt/query samples, repetitions, dates, locale, engine/surface, and
account/personalization conditions. Preserve absent data as unknown, not a zero score.

The scoring model is an internal audit heuristic, not a Google or LLM ranking formula.
Do not promise a universal GEO score, prescribed word count, magic schema, or visibility
uplift from adding llms.txt. Google currently says it does not affect Search rankings
or visibility; other consumers must be evaluated separately [google-ai].

Do not promise FAQ rich results in Google: the documented retirement began 2026-05-07
[google-updates]. Useful FAQ content can remain useful without that display feature.
Check active structured-data features, crawler controls, and report dimensions against
current provider documentation and the actual property/API. Existing 2026-08-25 source
group timestamps are retained; this narrower review does not certify every old claim.

The update log also adds fake/incentivized review guidance (2026-07-24) and an interactive
preferred-source button (2026-08-20). Review applicability before recommending either;
a button is not a ranking promise. Keep training crawlers distinct from search and
user-triggered fetchers, and verify names/rules per provider rather than generalizing.

## Evidence that would block acceptance

Stop approval when a decisive claim lacks an inspectable source, a required operation
was not executed, a protected invariant changes, or validation fails. Return the
bounded result and the specific missing evidence; do not fill the gap with confidence.

## Task-time source checks

Open the applicable current primary/system-of-record source before relying on a volatile
claim. Record actual version, effective/observed time, scope, and retrieval limitations.
The shared source-review ledger schedules maintenance; it cannot establish currentness
of every operational claim. Stable methodological guidance above is an editorial
operating policy, not a claim of a new universal standard.

- `google-ai`: https://developers.google.com/search/docs/fundamentals/ai-optimization-guide
- `google-updates`: https://developers.google.com/search/updates
