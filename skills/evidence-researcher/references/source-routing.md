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

## Source screening

Routing says which kind of source a claim needs. Screening says whether this page is that kind. Open the page before registering it and check:

1. **Publisher.** Who publishes it and how established they are. For an unfamiliar company, check its size and age (About page, funding, staff). An established organization's marketing page is still a marketing page: judge the page and the publisher together.
2. **Author.** Named, and verifiable outside this page through an affiliation, other work, talks, or code. An unsigned page or a byline that leads nowhere counts against the source.
3. **Purpose.** Whether the page exists to sell or to rank: the argument leads to the publisher's own product, demo or trial calls to action sit inline, FAQ blocks are written for search, the title is "What is X", "The complete guide to X", "Best N tools for X" or "X vs Y", or the figures are ones the page itself calls illustrative.
4. **Volume.** Whether the site is a content mill: several long posts a day, near-duplicate posts on one topic, unrelated topics in quick succession, many language versions for no clear audience.
5. **Originality.** Whether the page adds its own data, measurement, or firsthand observation, or restates others. A restatement is a lead: register the origin instead (`source-lineage.md`).

For papers and preprints also check the authors' affiliation and record, whether the paper promotes the authors' own product or company, stated commercial interests or AI-drafting disclosures, and review status (peer reviewed, workshop, preprint only).

Decide, and record the outcome in the source `notes`:

- **Register** a source that passes.
- **Register with a limit**, carried on every edge it supports (`scope_fit`, `notes`): a preprint whose authors have no visible affiliation or record; a single-author paper or small or self-funded sample; a small company reporting real data on its own system; an identifiable but little-known practitioner; a secondary report whose original could not be opened; an undated page; a self-selected vendor survey.
- **Discovery only**, never an evidence edge: sales, glossary, listicle, or comparison pages from publishers that are not well established; posts whose argument leads to the publisher's product and add no data of their own; content mills and automated research notes; restatements of another source, including AI-assisted rewrites; preprints with two or more of the warning signs above; anonymous or unverifiable authors; unreviewed repository content presented as evidence.

A source kept for discovery may be listed as existing coverage or as a lead. It must not support a claim, a definition, a figure, or a framing.

For a quoted passage, confirm it appears on the page as cited, record the locator on the edge, and set `last_verified_at` on the source.

## Vendors and other interested voices

An established vendor's engineering posts, research, documentation, and data are admissible. Two rules apply to every interested source:

- **Record what the publisher sells** in the source `notes`, and let the Evidence Pack say it at the source's first citation. A vendor's preferred design is one implementation, not a definition.
- **Let it support only what its own system or sample shows.** A vendor survey describes its respondents, not the market; record sample size, recruitment, and date. A participant's view is attributed to the participant, never presented as the market's view.

| Voice | May support |
| --- | --- |
| Public body, standards body, regulator | General claims about risk, requirements, practice; the neutral definition of a category |
| Independent analyst | Category definitions, market shape, counts |
| Academic paper or preprint | Conceptual distinctions and measured results, with review status noted |
| Vendor editorial, vendor blog, vendor data | That vendor's own position, product, system, or respondents |
| Practitioner with a public record | Observed practice, stated as that practitioner's experience |
| SEO explainer, content farm, rewrite, social post | Nothing. Discovery only |
