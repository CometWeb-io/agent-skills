# Source Authority Routing

## Principle

Authority is claim-specific. Start from the proposition, not from a favorite publisher or generic source score.

| Claim type | Preferred authority | Useful secondary evidence | Typical failure |
| --- | --- | --- | --- |
| law/regulation | official statute/gazette/regulator/court | qualified legal commentary | article substituted for current legal text |
| regulatory guidance | regulator/authority guidance | counsel analysis | commentary treated as controlling guidance |
| security advisory | vendor/maintainer, official advisory, CISA KEV/CVE/NVD where applicable | reputable security research | generic guidance used as proof of a specific vulnerability |
| vendor policy/terms | current first-party policy/terms/docs | archive/context | blog summary or old screenshot treated as current |
| competitor pricing | official pricing/checkout/terms | reseller/context | search snippet or pricing aggregator |
| official technical docs | versioned vendor docs/release notes/maintainer repo | respected analysis | version mixing or stale forum answer |
| repository behavior | source/tests/commit/release | issue/PR discussion | README inference substituted for code truth |
| internal metric | current analytics/DB/CRM/finance system of record | generated report | old slide or memory used as current truth |
| internal process state | tracker/deployment/support system of record | meeting note | narrative summary treated as live state |
| company announcement | first-party filing/release/status page | high-quality wire | derivative article without origin |
| market metric | original dataset/provider/official statistics | credible analysis | unattributed chart or rewritten statistic |
| academic finding | primary study/dataset | systematic review/meta-analysis for synthesis | press coverage used for the finding |
| qualitative experience | direct interview/review/community observation | cross-source synthesis | anecdote universalized |
| doctrine/framework | versioned original work | high-quality synthesis | doctrine treated as current fact |

## Primary-source rule

For a critical/material claim, prefer an accessible primary/official/system-of-record artifact when one exists. Secondary material is valid for discovery, context, critique, translation, synthesis, or genuine primary-source unavailability. Record why a secondary source remains material.

## Internal routing

Choose the system of record before retrieval:

- code truth -> repository/tests,
- deployment/runtime -> deployment/observability,
- roadmap/task state -> project/issue tracker,
- customer/account state -> CRM/support,
- document/policy state -> canonical document store,
- financial state -> finance/accounting,
- product/event metrics -> analytics/data warehouse.

Do not public-search a private fact because public search is easier.

## Discovery only

Search snippets, source registries, bibliography lists, knowledge panels, another model's answer, and social reposts are discovery artifacts unless the underlying source cannot be obtained and the limitation is explicit.
