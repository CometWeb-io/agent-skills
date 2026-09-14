---
name: ebook-publisher
description: Create, research, validate, edit, redesign, and prepare evidence-backed ebooks, white papers, and practical PDF workbooks, especially the CometWeb ebook series. Use for requests such as zrob ebook, napisz poradnik PDF, deep research do ebooka, zweryfikuj ebook, popraw okladke, or prepare a publication from research through reviewed PDF. Own publication scope, research coverage, claim-to-source mapping, editorial structure, meaning-preserving Polish/English editing, series design, revision-aware QA, and publication handoff. Reuse evidence-researcher and ai-humanize when available. Do not trigger for a standalone blog post, a generic website audit, simple PDF extraction, or merely a request to install a skill. Research-only and redesign-only requests must stay within their requested scope. Never imply that automated checks prove factual accuracy or that a created file is installed or publicly published.
---

# Ebook Publisher

Produce a useful, evidence-backed publication, not an unnecessarily long research report
or a decorative PDF. Default to the user's language. CometWeb deliverables are Polish
unless the user specifies otherwise. Package version is in `VERSION`; it is independent
of the edition of any ebook.

## 1. Route and scope

| Mode | Trigger | Deliverable and limit |
| --- | --- | --- |
| RESEARCH | Research before writing an ebook | Research brief, evidence ledger, gaps, proposed outline; no unsolicited full ebook. |
| CREATE | Create an ebook / workbook / white paper | Research through editable manuscript, rendered PDF, and QA record. |
| UPDATE | Refresh facts or expand an existing volume | Source delta, revised content, relevant downstream checks. |
| REDESIGN | Improve cover, typography, tables, or icons | Preserve content and edition; visual revision and PDF checks. Flag discovered factual issues rather than silently rewriting them. |
| REVIEW | Audit/validate an existing ebook | Findings with locations, evidence, severity, repair steps; no unsolicited replacement. |
| RESUME | Continue a saved publication | Verify checkpoint fingerprints, invalidate stale checks, resume the earliest affected stage. |

Do not run the full workflow for an isolated stage. Generic blog writing, website audits,
PDF extraction, and decisions about whether to install skills belong elsewhere.

Use context already supplied. Recover missing reference files through the available
file/repository tools. Do not repeatedly ask for known audience, language, edition, or
branding. For reversible gaps, proceed with labelled assumptions. Missing evidence,
logo, font, or a reference PDF must be disclosed; it is not permission to invent one.

## 2. Load only the next stage

| Stage | Read from this package |
| --- | --- |
| Brief, research, fact-check | [Research and evidence](references/research.md) |
| Outline, draft, substantive editing | [Editorial standard](references/editorial.md) |
| CometWeb cover, interior, visual components | [CometWeb design](references/cometweb-design.md) |
| Render, inspect, accessibility, final files | [PDF production](references/pdf-production.md) |
| Gates, manifests, repeat checks | [Validation contract](references/validation.md) |
| Existing skills, fallback, repository integration | [Integration](references/integration.md) |
| Behaviour evaluation / maintenance | [Evaluation cases](evaluation/cases.json) |

Use [brief](templates/brief.md), [manuscript](templates/manuscript.md),
[publication manifest](templates/publication.json), and [QA report](templates/qa-report.md)
as starting points, not material to paste into the reader's ebook.
[Design tokens](assets/cometweb-tokens.json) and [print CSS](assets/cometweb-print.css)
implement a baseline; they do not replace inspection of a real rendered document.

## 3. Confirm capability and authority

Read relevant repository instructions before repository writes. Use authorized connectors
for private material, current primary sources for external factual claims, and host PDF
instructions for PDF work. A tool being named in these instructions does not mean it is
available. Do not invent web visits, experiments, subagents, or visual inspections.

When available, load and actually execute `evidence-researcher` for evidence work and
`ai-humanize` for substantial natural-language rewriting. Preserve their contracts.
Use `skill-orchestrator` only for explicit broader orchestration or genuine multi-skill
coordination; do not recurse back into this skill. `ai-council` is not a routine ebook gate.
If a dependency is unavailable, follow this package's explicit fallback and record that
fact. Never report that the absent skill was executed.

Choose one production route supported by the host: long-form DOCX to PDF, structured
HTML/CSS to PDF, or justified programmatic composition. Do not rasterize whole pages
as the publication. Inspect the requested reference; its facts do not become new evidence.

## 4. Execute with gates

### A. Brief and research

State audience, reader outcome, prior knowledge, scope, exclusions, geography where
relevant, language, evidence cut-off, format, edition, and supplied references.
Derive chapter questions from reader tasks. Plan depth by risk and gaps, not quotas
for words, citations, tools, agents, or elapsed time.

Build the evidence ledger before drafting strong conclusions. Inspect underlying sources;
log claim-specific support, limitations, dates, versions, and meaningful falsifier searches.
Separate facts, reasoned recommendations, inferences, and synthetic examples. Unresolved
critical contradictions block a publication-ready verdict. Keep a research log sufficient
to reproduce searches without dumping irrelevant browsing history into the ebook.

### B. Outline and write

Map every in-scope question to a chapter. Give each chapter a concrete reader outcome.
Teach a usable procedure or decision where appropriate: prerequisites, steps, example,
acceptance criterion, evidence to save, and limits. Do not force every chapter into identical
boxes. Remove redundant coverage. Cite material factual claims near the claim; place
bibliographic detail in sources, not only at the end of a disconnected research report.

### C. Validate content, then edit, then validate the changes

Inspect source entailment, date/version fit, units, denominators, normative scope,
contradictions, code examples, quotations, chapter consistency, and illustration labels.
Review citations against the actual draft, not merely the ledger.

Edit Polish/English naturally without generic filler, fake personal experience, invented
results, synonym churn, or marketing hype. Preserve names, numerical values, uncertainty,
negation, causality, conditions, thresholds, normative verbs, and attribution. A mechanical
rewrite guard is supplementary: it does not prove semantic equivalence.

After editing, compare the changed claims with the evidence. New or strengthened claims
return to research. Keep footnotes, code, URLs, identifiers, and protected quotations intact.
Run a separate sceptical review pass. A second pass by the same model is a self-review,
not independent expert verification. Resolve material findings before finalising.

### D. Design and produce

Use the CometWeb profile when this is a CometWeb volume. For another brand, use its
approved profile instead; never silently apply CometWeb branding to an unrelated client.
CometWeb defaults: genuine logo, Nunito Sans, dark cover, one meaningful mint accent,
light interior, functional line icons, rounded semantic status pills, no generated photos,
no ornamental side strips, and no fabricated dashboards or product outcomes.

A confirmed defect before repair is red. A verified successful retest is green. A change
without verification stays neutral/amber/awaiting retest. A neutral baseline is not a defect.
One subdued topic-related background icon is acceptable when it supports the composition;
it must not replace the logo or compete with the title.

Keep an existing ebook's edition, including `1.0`, unless explicitly instructed otherwise.
For a new unspecified volume use edition `1.0` as a declared default. Track design/content
revisions separately. Date of evidence is not the last access date or the design revision.

### E. Inspect and hand off

Render the actual final PDF. Inspect every page, then close-ups of the cover, statuses,
dense tables, diagrams, and before/after comparisons. Check fonts, Polish characters,
links, TOC/page numbers, bookmarks, actual page count, reading order, and clipping.
Record page-specific notes. Geometry checks and contact sheets alone are not complete
visual inspection. Any post-review change invalidates the affected checks.

Deliver the requested file plus editable source, evidence ledger, concise QA report, and
useful previews. Reader-facing content comes first. Keep internal research logs separate.
Do not distribute standalone font files, private evidence, credentials, or unapproved
customer assets. Publish externally or modify a live site only on explicit authorization.

## 5. Use the local checks honestly

Python 3.10+; release-stage PDF page checks additionally require `pypdf`.
Run from the skill root, replacing paths with the actual workspace:

```bash
python scripts/ebook_check.py init /path/to/new-publication
python scripts/ebook_check.py fingerprints /path/to/publication/publication.json
python scripts/ebook_check.py validate /path/to/publication/publication.json --stage research
python scripts/ebook_check.py validate /path/to/publication/publication.json --stage manuscript
python scripts/ebook_check.py validate /path/to/publication/publication.json --stage release
python -m unittest discover -s tests -v
```

The validator is read-only except for explicit `init`. `fingerprints` never marks reviews
complete. Supply `--as-of YYYY-MM-DD` only for deliberate, disclosed historical evaluation.
Its success result is **RECORDS_COMPLETE**, not verified truth, independent review, legal
compliance, PDF/UA conformance, or authorization to publish. It checks records and bytes;
the agent must still perform the research, editorial, visual, and domain-specific reviews.

## 6. Final verdict

Use `DRAFT`, `REVIEW_REQUIRED`, or `READY_FOR_OWNER_REVIEW`. State remaining blockers
precisely. Never label an unrendered PDF ready, a missing review passed, or a historical
claim revalidated solely because its citation still opens. Missing critical evidence means
research/partial output, not invented certainty; preserve useful completed work.

Final response: actual artifacts, what changed, what was checked, and meaningful limits.
A file created in a sandbox is not automatically installed, committed, merged, deployed,
or publicly published. Confirm each state through the relevant tool before claiming it.
