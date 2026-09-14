# Research, evidence, and fact-checking

## Research contract

Record: intended reader and prior knowledge; practical outcome; core question; secondary
questions; exclusions; jurisdiction/locale where material; evidence cut-off; existing
edition; source/reference files; assumptions; tools actually available. Choose a working
length from the content, not a word-count target. Respect user-specified length.

Construct a coverage matrix of reader questions → chapters → material claims → sources.
A search log records query, date, source inspected, finding, and remaining gap. Prefer a
small useful log over a transcript of every click. State inaccessible controlling sources.

## Authority depends on the claim

| Claim | Preferred evidence | Do not substitute |
| --- | --- | --- |
| Standard / normative criterion | Official versioned standard and official explanatory material, with scope distinguished | A checker score or a blog's interpretation |
| Law / obligation | Official current text, effective date, jurisdiction, scope, exemptions; specialist review where needed | Publication date, a summary page, or universal legal guarantees |
| Browser / API / software behaviour | Current official documentation plus versioned source or a reproducible test when needed | Old tutorial or unsupported runtime assumptions |
| Search-engine policy | Current documentation of the relevant engine | Speculation presented as ranking rules |
| Scientific effect / quantitative estimate | Original study, methods, sample, uncertainty, replication where available | A press release standing in for the paper |
| Product capability / price | Current system of record or first-party material, exact plan/version/date | Internal roadmap as shipped functionality |
| Case study | Actual authorized records with measurement method and limitations | A made-up before/after framed as a customer result |

For current/uncertain external claims, browse at execution time. No built-in dates,
versions, thresholds, prices, or legal conclusions in this skill override current evidence.
Respect a user's explicit no-browse request: work from supplied evidence and disclose
currentness gaps instead of inventing revalidation. Search snippets are discovery, not
proof. Open the underlying page. Inspect actual PDF figures/tables; text extraction alone
is inadequate for visual evidence. Do not search public web with private/customer text.

## Claim record

Atomize consequential statements. Avoid combining a testable fact, recommendation,
and promised effect into one claim. Each material statement records:

- exact intended meaning, chapter, kind, materiality, and scope;
- inspected source IDs and claim-specific locator/explanation;
- support, contradiction, and context edges separately;
- source version, access date, effective date where relevant, and an origin group;
- conclusion, qualification, and time-sensitive review-by date with rationale;
- countercheck: falsifier question, searches/checks done, outcome, and sources consulted.

A fact can be supported or qualified; an inference is `inferred`, not `verified`.
Recommendations have a rationale, conditions, trade-offs, and evidence for their premises.
Synthetic examples are `illustrative` and visibly labelled adjacent to the example.
They never become evidence that CometWeb, a customer, or a website achieved a result.
A claim's materiality follows consequences for the reader, not ease of finding a citation.
The validator cannot detect a wrongly downgraded material claim: review this manually.

## Independence, contradictions, and negative findings

Several pages reproducing one study or announcement count as one evidence origin.
Do not demand two independent sources for an official normative definition merely to
reach a quota. For contested empirical effects seek independent work, failures, null
results, and alternative explanations. Do not resolve disagreements by majority vote.

For each critical/material non-illustrative claim, ask what evidence would make it false
or narrower. Log a meaningful attempt. No contradiction found is not proof of absence.
Resolve contradictions by scope, version, methods, source authority, or qualified wording;
preserve dissent that genuinely remains. Critical unresolved contradictions block readiness.
If a claim must be removed, update the manuscript and record why, not just its status.

## Citation integrity

Cite near the statement; bibliography is not a substitute. Distinguish what the source
says from your inference. Check units, denominator, sample, dates, geography, exceptions,
causal direction, and whether the source actually entails the sentence. Read surrounding
context. A working link does not establish truth. Keep direct quotations limited, accurate,
and attributed; do not reproduce full sources or imply permission not granted.

Use stable source IDs in the working manuscript: `[^S001]` with a corresponding footnote
definition. Working-only `<!-- claim:C001 -->` and `<!-- chapter:ch01 -->` anchors link the
ledger to the manuscript. They must not show as literal text in the final PDF. The validator
checks presence and relationships; the editorial reviewer checks actual placement/meaning.
Footnotes referring to sources not in the ledger are not permitted in this v1 template.

## Stop rule and update strategy

Stop when all in-scope reader questions are covered or explicitly narrowed, material
claims have adequate source-specific support and counterchecks, contradictions are
resolved/qualified, and a bounded additional search is unlikely to change the draft.
Do not equate depth with 100 links, 30,000 words, or hours of runtime. If an unresolved
controlling question blocks completion, deliver a labelled research draft and the gap.

Refresh the changed claims and their dependants instead of restarting all research.
A changed source, claim, scope, figure dataset, or as-of date invalidates related checks.
Final release requires a complete review record for the final revision, even where a
reviewer reuses earlier evidence after explicitly checking it is still applicable.
