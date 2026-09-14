# Validation contract v1

## What the program checks

`ebook_check.py` validates publication record structure, claim/source relationships,
question coverage, source-inspection declarations, countercheck records, evidence freshness
fields, manuscript anchors/footnotes/placeholders, required review records, supporting local
file hashes, actual PDF page count, and per-page inspection records bound to the PDF hash.

It does NOT browse, assess source entailment, identify undisclosed material claims, authenticate
reviewers, detect dishonest records, execute examples, render pages, inspect appearance,
certify accessibility, install a skill, or publish anything. It does not turn a model's
self-review into independent evidence. `RECORDS_COMPLETE` means the required consistent
records exist for this stage, not that the ebook is correct. The publication owner/agent
must still complete the real work and decide `READY_FOR_OWNER_REVIEW` honestly.

## Commands and exit status

Run from the skill directory. Python 3.10+ is needed. Release stage additionally needs
`pypdf`, obtained through the host's approved dependency process; no automatic installation.

```bash
python scripts/ebook_check.py init ../publication
python scripts/ebook_check.py fingerprints ../publication/publication.json
python scripts/ebook_check.py validate ../publication/publication.json --stage research
python scripts/ebook_check.py validate ../publication/publication.json --stage manuscript
python scripts/ebook_check.py validate ../publication/publication.json --stage release
```

`init` requires a new nonexistent directory and never overwrites. The template is incomplete
and must fail validation. `fingerprints` reads current files and prints hashes; it neither
updates the manifest nor marks any review pass. `validate` emits JSON: stage, as_of,
result, blockers, warnings, and fingerprints. Exit 0: records complete; 1: incomplete/failed
records; 2: invalid input/dependency/IO problem. Missing PDF or parser is not success.
`--as-of` explicitly evaluates historical freshness; default is today's date in Europe/Warsaw
when timezone data is available (otherwise system date). The effective date is always reported.
Do not use a historical date to present an old check as a current validation.

## Publication manifest

Use `templates/publication.json` as the exact structural starting point. Arrays contain
objects with stable unique IDs. IDs use letters, digits, underscore, or hyphen. Dates use
YYYY-MM-DD. `publication.edition` is a string and is independent of package VERSION;
`publication.revision` is a nonempty string. The brief is human context, not an automatic gate.

- `scope.questions`: id, question, status (`covered`, `open`, `excluded`), chapter_ids,
  and rationale for exclusions. Open questions block records completion.
- `chapters`: id, title, outcome, question_ids. Coverage is bidirectional.
- `sources`: id, title, source_type (`primary`, `secondary`, `discovery`, `provided`,
  `experiment`), origin, inspected boolean, accessed_on, url; optional published_on,
  version, effective_from, notes. A missing URL requires `artifact` with path/sha256.
  Effective dates/versions are checked semantically in actual source review, not by guessing
  applicability from the newest date. Discovery results cannot support material claims.
- `claims`: id, text, chapter_id, kind (`fact`, `recommendation`, `inference`, `synthetic`),
  materiality (`critical`, `material`, `background`), conclusion, evidence edges, explicit
  time_sensitive boolean, countercheck. Qualified facts require qualification text. Inferences
  require rationale and `inferred`, recommendations rationale and `recommended`, synthetic
  examples `illustrative` plus `display_label`. A fact is `supported` or `qualified`.
- Each evidence edge: source_id, relation (`supports`, `contradicts`, `context`), locator,
  explanation. Non-synthetic critical/material claims require support from inspected
  non-discovery sources. Contradictions need a resolution record in the claim. A field's
  mere existence is not proof that the reasoning resolves a genuine contradiction.
- `countercheck`: performed=true, checked_on, queries (nonempty list), outcome, source_ids.
  Required for critical/material non-synthetic claims, including recommendations/inferences.
  A no-results search can have empty source_ids, but not an empty query or outcome.
- Time-sensitive claims require as_of, review_by, and freshness_rationale. Their record is
  stale after review_by. There is no universal fixed time-to-live or source-count quota.
- `files`: manuscript, pdf, deliverables. Paths are relative to the manifest directory.
  No parent traversal, absolute paths, or symlink escape. Manifest UTF-8 JSON max 4 MiB;
  duplicate keys and non-finite numeric constants are rejected. Manuscript max 16 MiB.
- `checks`: id, status, reviewer, method, checked_on, notes, evidence_file,
  evidence_sha256, fingerprints. Allowed methods: `manual`, `self_review`, `automated`.
  All required checks need status `pass`; skip/blocked/missing is not a pass. For a truly
  absent feature (e.g. no executable code), the reviewer records a scoped inspection and
  explains why there is nothing to execute, instead of fabricating a tool run.
- `visual`: renderer, pdf_sha256, page_count, pages. Each page record has integer page,
  status, reviewer, inspected_on, notes, render_path, render_sha256. Require exactly one
  record per actual PDF page, with real readable rendered images inspected separately.

Core fingerprints are canonical JSON SHA-256 over publication/scope/chapters/sources/claims,
manuscript file SHA-256, and PDF file SHA-256. Required review fingerprints grow by stage.
Research checks bind research; manuscript checks bind research+manuscript; PDF checks bind
all three. Evidence logs and page renders have their own hashes. Altered evidence records,
text, PDF, log files, or rendered images invalidate the corresponding prior review record.
Hashes attest to byte identity only; they do not prove that a file is authentic or true.

## Required checks

| Stage | Added review IDs | What must actually be reviewed |
| --- | --- | --- |
| research | scope_coverage, source_entailment, counterevidence | Questions, source-to-claim fit, meaningful negative-evidence search |
| manuscript | claim_coverage, cross_chapter_consistency, semantic_fidelity, editorial_review, examples_and_numbers | Complete draft against ledger, terminology/logic, post-edit meaning, language, calculations/examples |
| release | visual_design, pdf_structure, links_and_navigation, accessibility_review, asset_rights, package_hygiene | Final design, parser/metadata/text, links/TOC, actual scoped accessibility review, assets permission, safe deliverables |

A research-only run needs no PDF and no PDF checks. REDESIGN of an existing volume must
not falsely certify historical evidence as newly researched. If no validated baseline is
available, deliver the requested visual revision with a visual QA report and explicitly
limited verdict; the full release-stage records check remains incomplete. Do not fabricate
research records merely to satisfy a validator. A partial stage result is a valid handoff.

## Working manuscript markers

Include one `<!-- chapter:ID -->` marker per chapter and at least one `<!-- claim:ID -->`
per recorded claim. Repeated claim references are allowed; unknown markers are not.
Use source footnotes `[^S001]` and exactly one nonempty matching definition. Supporting
sources for material claims must be cited inside the corresponding claim block (up to the
next claim/chapter anchor). Fenced/inline code is excluded from marker/citation checks;
unclosed fences block validation. This is a documented Markdown convention, not a full parser. Footnote-to-sentence entailment and uncaptured
claims require real human/agent review. Template placeholders `[UZUPEŁNIJ ...]`, `[TODO ...]`,
and `[TBD ...]` block manuscript readiness. Other programming template syntax is not banned.

## Failure policy and scope honesty

No averaged quality score and no override flag that turns missing checks green.
Do not weaken tests to make fixtures pass. Reject malformed types without traceback.
Synthetic tests validate program behaviour only; separately run model/host tests and actual
publication acceptance. Keep their counts separate in the report. New files are not proof
of installation; a proposed registry entry is not active routing.
