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

Screening is a researcher judgment about a source's fitness for a specific claim.
It is instruction policy: the kernel validates declared metadata and admission,
not the truth of a screening decision or free-text `notes`.

For `PUBLIC` web sources, inspect the underlying page or artifact before using
its contents. Check issuer and provenance, relevant author expertise, commercial
interests, publication/review status, original data and method, and whether the
passage supports, contradicts or contextualizes the claim. Apply the same checks
to contrary evidence; a credible falsifier must not be discarded for its conclusion.
Trace copied claims to their origin
(`source-lineage.md`). Titles, CTAs, posting volume and SEO formatting are leads
for inspection, not evidence of invalidity.

Company size, age, funding, author affiliation, a single author, self-funding and
AI-drafting disclosure do not independently or in combination disqualify a source.
Evaluate identifiable methods, data, provenance and claim scope; record missing
information as a limitation. An organization can be the accountable author:
official documentation, policies, standards and advisories need no personal byline.
Small vendors' primary documentation and measurements receive the same claim-fit
assessment as large vendors'. Prestige never substitutes for inspecting evidence.

For `PRIVATE` and `USER_SUPPLIED` sources, use the authorized system of record or
supplied artifact. Check identity, access, version, completeness and scope; do not
require a public author profile, company funding or external search of private facts.
User-supplied content does not become independently verified merely by being supplied.

Record each source/claim decision and reason in source `notes`, with the claim ID;
carry restrictions on the relevant edge in `scope_fit` and `notes`:

- **Register** when the inspected artifact fits the claim's authority and scope.
- **Register with a limit** when it supports a narrower or explicitly provisional
  claim: a preprint with inspectable methods, a self-selected survey, an undated
  page, practitioner experience or a secondary account whose origin is inaccessible.
  State exactly what is supported and what remains unverified; narrow the claim
  before using `ACCEPTED`. Use `CONTEXT_ONLY` when it supplies context without
  satisfying the material claim. A low/unknown-quality edge cannot be promoted by notes.
- **Discovery only** for an uninspected lead or a claim for which the inspected
  artifact supplies no usable support, contradiction or context. An inaccessible
  primary origin limits an inspected secondary account; it does not automatically
  exclude that account. Distinguish its attributed account from a verified original result.
  Keep the reference and reason in the screening log. Do not create an `ACCEPTED`
  or `CONTEXT_ONLY` edge for that claim from an uninspected lead. A `REJECTED` edge
  may record the exclusion for audit; it cannot supply coverage.

One artifact may be admissible for one claim and discovery only for another.
A sales page can support the vendor's stated offer, not independent effectiveness;
a rewrite can lead to the original result and can itself document what its publisher
said, without becoming an independent confirmation of that result. A missing author
record cannot repair missing methods, and a famous author cannot repair them either.

Unreviewed repository content is evidence of the inspected proposed code at the
pinned commit or diff. Record draft/review status; do not infer merge, deployment,
runtime success or production state. A missing review is not a ban on code inspection.

For a quoted passage, confirm it in the inspected artifact, record the locator on
the edge and `last_verified_at` on the source. A supplied snapshot establishes
its captured content only; do not claim a fresh live-page visit from that snapshot.

## Vendors and other interested voices

Record material commercial interests or advocacy roles in source `notes` and
attribute them once at first material citation. An interest affects interpretation;
it does not automatically invalidate primary data or documentation.

A vendor survey describes its respondents, not the market: preserve sample size,
recruitment and date. A benchmark supports the tested configuration and method;
broader generalization requires supporting evidence. Attribute a participant's
position to that participant. Vendor, analyst and academic category definitions
are attributed proposals unless a controlling standard or established usage supports
a broader claim. Independent analysts also need inspectable methods and provenance.

| Voice | Claim-specific use |
| --- | --- |
| Public body, standards body, regulator | Its issued requirements, definitions, guidance or data within its remit and effective version |
| Independent analyst | Definitions attributed to the analyst; market estimates bounded by disclosed method and data |
| Academic paper or preprint | Conceptual proposals and measured results within method, sample and review-status limits |
| Vendor documentation, editorial or data | Its documented interface, offer, position, inspected system or measured sample |
| Practitioner or community account | That participant's experience or statement; no unsupported market generalization |
| SEO explainer, rewrite or content-farm page | Discovery of underlying results; its own inspectable statement only when that statement is the claim |
