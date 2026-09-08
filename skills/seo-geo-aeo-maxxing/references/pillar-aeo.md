# Pillar 5 - AEO / answer extraction readiness

Purpose: evaluate whether useful information can be extracted accurately into answer-like surfaces.
AEO is not a guarantee of snippets, PAA, voice answers, or AI citation.

## AEO-01 - Answer-first clarity

For pages that answer a question/task, check whether the relevant section gives the answer promptly
and then expands with evidence/context. Do not enforce magic fixed-length answer blocks or a rigid first-sentence length.

## AEO-02 - Section discoverability where natural

Use headings that accurately name the section. Question-form headings help when they reflect real
questions; do not rewrite every heading into a question. Heading order is mainly structure and
accessibility, not a standalone Google ranking requirement.

## AEO-03 - Lists/tables/steps when the information calls for them

Use ordered lists for sequences, bullets for unordered options, tables for consistent comparable
attributes, and prose for nuance. Do not convert content into tables merely for AI extraction if
important caveats disappear.

## AEO-04 - Definitions/comparisons are concise and complete

Make the decisive relationship explicit. State units, dates, assumptions, eligibility conditions,
and exceptions where material. A complete 90-word explanation can be better than an incomplete
50-word answer.

## AEO-05 - Useful visible FAQ/Q&A where warranted

Use FAQ only for real recurring questions that do not fit the main flow. Do not add FAQ sections for
SEO theater. Current Google FAQ rich-result support must be checked in the live registry and should
not be assumed from old guidance.

## AEO-06 - Supported structured data when eligible

Use structured data only when it matches real visible/entity facts and the consumer/platform
supports a useful interpretation. Absence cannot be proven from a text-only/static fetch that may
strip JSON-LD. Follow `data-collection.md` before issuing a schema FAIL.

Google does not require special schema for generative AI Search. Do not sell schema as a generic
citation boost.

## AEO-07 - Snippet/preview controls

Inspect `nosnippet`, `max-snippet`, `data-nosnippet`, and related controls when answer visibility is
a goal. Restrictions can be deliberate licensing/privacy choices; call them a defect only after the
business objective is clear.

## Extraction quality test

For a priority question, try extracting the minimum self-contained answer from the page and verify:

1. subject/entity is unambiguous;
2. qualifiers survive extraction;
3. numbers keep units/date/source;
4. comparisons preserve criteria;
5. steps preserve prerequisites/order;
6. no key caveat lives only in surrounding prose or an inaccessible visual.

This is a reproducible content-quality test, not proof that a platform will select the passage.
