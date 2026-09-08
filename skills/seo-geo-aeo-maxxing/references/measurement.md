# Observed visibility measurement

MAXX measures controllable readiness/quality. It is not a citation counter. Keep observed outcomes
separate so missing telemetry never becomes `0 visibility`.

## Measurement hierarchy

1. First-party platform reporting.
2. First-party site analytics and conversions.
3. Connected third-party longitudinal monitoring.
4. Controlled prompt samples only when better data is unavailable or explicitly requested.

## Google Search Console

Use the dedicated Generative AI performance report when the property has access. At the bundled
2026-08-25 verification, Google had announced a limited rollout with:

- impressions in generative AI features;
- pages/URLs;
- countries;
- devices for Search;
- date granularity.

Do not invent query-level data in this report. Preserve the date range and note limited rollout.

## Bing Webmaster Tools

Use AI Performance when connected for supported Microsoft AI experiences. Current first-party
announcements include citation totals/trends, cited pages, sampled grounding queries, and expanded
preview views for Intents, Topics, Citation Share, and Compare.

Do not interpret citation count as ranking position, authority score, or answer placement.

## Site analytics

Use GA4 or equivalent for AI referral sessions and conversions. Referral traffic measures clicks,
not all mentions/citations. Current OpenAI publisher guidance documents `utm_source=chatgpt.com` for
ChatGPT Search referral links; re-verify before treating any convention as permanent.

## Controlled prompt panel

If used, define the query/prompt set before checking results, preserve market/language/date, record
mention/link/citation separately, and reuse the same panel for trend comparison. Label it
`sampled prompt visibility`, never platform-wide citation share.

## Readiness x observed-visibility diagnostic

| Readiness | Observed visibility | Interpretation |
|---|---|---|
| High | High | protect winning sources; expand carefully |
| High | Low | investigate authority/distribution/query fit, telemetry lag, or selection competition |
| Low | High | visibility may be fragile; fix blockers without destroying what is already cited |
| Low | Low | fundamentals and differentiated source value come first |

Do not treat the quadrant as causal proof. It is a diagnostic frame.

## Baselines and causal restraint

For before/after analysis, use comparable windows, account for seasonality, campaigns, migrations,
algorithm/product changes, and query mix. A score change followed by visibility change is not causal
proof without stronger design. Use experiments/controls where feasible.

## Metrics worth reporting when actually measured

- generative AI impressions;
- cited pages/URLs and citation trend;
- grounding-query samples or intent/topic groups;
- citation share where the platform provides it;
- AI referral sessions, leads, revenue, or assisted conversions;
- sampled prompt mention/link/citation rates.

No analytics referral does not mean no citation. One successful prompt does not mean strong GEO.
Citation does not imply click; click does not imply conversion.
