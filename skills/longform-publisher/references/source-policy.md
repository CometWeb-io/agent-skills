# Source policy

Choose one publication mode:

- `BUILD`: create from authorized inputs; external research only when the user request/source policy permits it.
- `SOURCE_BOUND`: factual support may come only from explicitly authorized sources. Treat model knowledge as non-admissible factual support. Do not silently browse or pull adjacent files.
- `RESEARCH_EXPAND`: external verification/expansion is permitted; use `evidence-researcher` when claim verification is consequential, broad, disputed, current, or reusable downstream.
- `REFRESH`: compare an existing publication with current evidence and reopen only affected claims/sections when possible.

Each source record needs `id`, `system`, `locator`, `authorized`, `freshness`, and `observed_at` when relevant.

Freshness values: `CURRENT | NEAR_EXPIRY | STALE | SUPERSEDED | UNKNOWN | NOT_REQUIRED`.

For volatile current claims, stale-only/unknown evidence is not enough for release-ready current wording. Either refresh the evidence, weaken/time-bound the claim, or scope it out.

Search snippets, bibliography entries, AI answers, and citations without inspected source content are discovery pointers, not automatically admitted evidence.
