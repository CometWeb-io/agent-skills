# CometWeb publication design profile

## Provenance and precedence

Baseline read for this package: the public `MaciejZet/agent-skills` repository.

- `docs/EDITORIAL_VISUAL_STANDARD.md`, blob `edf2d2f44c8ef66848c4b35e100688c9a0cada79`.
- `docs/COMETWEB-EBOOK-DESIGN-RULES.md`, blob `3219bcfb917fceeb8436c87429714afc3df65a01`.
- User decisions in the ebook series: 12 September 2026.

Inside the repository, read current AGENTS/README and both current design documents.
This file is a portable profile, not a new independent global source of truth. Current
explicit user instructions take precedence. The two baseline documents contain slightly
different token variants: this package uses the EDITORIAL_VISUAL_STANDARD status palette,
with the blocked state from EBOOK-DESIGN-RULES. This choice is explicit, not a claim that
the original files were already consolidated. If the current canonical rules conflict in
meaning, resolve that conflict visibly before asserting series conformity.

Reference: the actual approved SEO/GEO/AEO 2026 ebook, edition 1.0, Nunito Sans, without
side strips. Retrieve and inspect the real PDF when making an ebook; a filename or a
memory of the cover is not visual inspection. If unavailable, use this baseline but
report that reference matching remains unverified. The reference contributes design,
not facts or permission to reuse its images. Do not copy its defects.

## Identity and typography

Use the genuine approved vector logo and correct wordmark, with documented origin.
No generated comet, traced imitation, low-resolution favicon, or invented logo. Preserve
proportions and a suitable light/dark variant. No white plate on a dark cover unless the
approved identity requires it. Missing assets: draft with an explicit empty reserved area,
not a fake substitute; final identity review remains incomplete.

Nunito Sans, distinct real weights, Polish glyphs. Embed appropriate font subsets in the
PDF according to permitted use. Never distribute font binaries separately. Verify the
actual embedded font and appearance: calling a style "Bold" is not evidence of bold glyphs.
Readable body type is more important than squeezing a table onto one page. Start around
10.5–11.5 pt for A4 body text; tune in a real-size render, not as a universal fixed rule.

Brand: Night Black #18181B; Energy Mint #05F29B; Trust Green #04C27C;
Depth Green #034C32; White #FFFFFF. Mint is an accent on dark backgrounds, not small
body text on white. Token values live in `assets/cometweb-tokens.json`.

## Cover

Dark field, genuine logo, restrained category label, strong title hierarchy, one meaningful
mint highlight, short substantiated outcome, edition, and evidence date. Separate title
and subtitle rather than equal-weight blocks. A small thematic column may show year and
areas with icons. A bottom strip may show chapter/card counts only after verifying them.

Prefer typography and space over decoration. A large subdued line icon related to the
topic can sit in the background without reducing contrast. No photos generated for filler,
random orbits/circles/lines, decorative side strips, or fictitious product panels. Do not
pretend a synthesized dashboard is a captured product state. Keep edition 1.0 unchanged
unless the user authorizes an edition change; use separate design revision metadata.

## Interior and components

Light pages, dark text, deep-green subheadings, restrained chapter numbers, functional
category icons. Use one 24×24 line-icon family, similar stroke weight and rounded caps.
Do not mix emojis, filled pictograms, and multicolour illustrations as status icons.
Icons support text; they do not replace labels, units, criteria, or identifiers.

Cards/callouts have mild fills, subtle outlines, approximately 12–14 px corner radius,
and consistent whitespace. Types: action, evidence, example, limit, warning. No green
success tick for future work. Avoid tall empty blocks or a card around every paragraph.

Status pill = icon + readable text + semantic light fill + outline, fit to text, not the
entire row. Typical compact A4 status text: 8.5–9.5 pt, height 19–22 pt. Do not split
a pill across lines/pages or shrink it to illegibility. Explain extra states in a legend.

| State | Icon | Text | Fill | Border |
| --- | --- | --- | --- | --- |
| Confirmed pass / repair | check-circle | #034C32 | #E8FBF2 | #B6E5D0 |
| Defect / fail | x-circle | #991B1B | #FEF2F2 | #F5C3C3 |
| Caution / partial / unresolved | alert-triangle | #92400E | #FFFBEB | #F0D9A0 |
| Not tested / no data | circle-question | #4B5563 | #F1F4F3 | #D6DFDC |
| Not applicable | circle-minus | #4B5563 | #F1F4F3 | #D6DFDC |
| Awaiting retest / in progress | clock | #1E40AF | #EFF6FF | #BFDBFE |
| Blocked | lock | #6941A5 | #F5F1FA | #D7C6ED |

Confirmed defect before repair: red label/icon and gentle red panel. Verified successful
retest: green. Unverified change: neutral/amber or awaiting-retest blue. "Before migration"
is not automatically a failure. Preserve state semantics within mixed results; not every
"after" value passes. Priority, defect state, repair state, test verdict, and accepted
exception are distinct. Accepting an exception never turns a failed test into a pass.
A deliberate appropriate HTTP error response may show correct behaviour, not a defect.

Keep screenshots unaltered as evidence. Add labels/frames outside them. A correct failure
message after fixing error handling can have a green external frame without recolouring
the screenshot itself. Colour is never the only way to express meaning.

## Tables, diagrams, and charts

Repeat table headers, right-size columns, use light separators and mild row fills.
Preserve data as selectable text. Keep short test cards together; deliberately split
long material instead of making the type tiny. Avoid orphan headings and almost-empty
pages caused by mechanical chapter breaks. A chapter need not always start a new page.

Every chart answers a question and identifies measurement, unit, scale, values, denominator,
source, and limits. Label synthetic data at the chart. Keep comparable scales aligned;
do not invent data to fill space or add overlapping categories. Rounded bar ends must
not shift the apparent value. Diagrams need legible labels and arrows that avoid text.

Inspect contrast and a grayscale view. Practical visual targets: 4.5:1 for ordinary text
and 3:1 for large text, consistent with the baseline series rules; this is not a claim
of conformance for the whole PDF. Check current official accessibility guidance when
making a normative claim in a publication. See also PDF production and release review.
