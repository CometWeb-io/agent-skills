# Integration and capability fallbacks

## Skill boundaries

`ebook-publisher` owns the publication lifecycle and its scoped final verdict.
`evidence-researcher` owns auditable evidence construction; load its actual current SKILL.md
and relevant references. Preserve its IDs and source provenance; the publication ledger
is a small publication-facing view, not a replacement or undocumented incompatible schema.
Keep the full evidence pack as an additional source when supplied.

`ai-humanize` owns natural-language rewriting with fidelity controls, not fact discovery.
Read its contract and actually run its tools when applicable. `cometweb-context` is useful
only when public product claims need a fresh multi-source internal context, not for every
generic educational ebook. SEO, accessibility, security, or other specialist skills can
supply domain checks when present; their conclusions still need scope and evidence.
Do not run a live website audit merely because the ebook teaches auditing.

`skill-orchestrator` can call this skill as a publication step. Avoid recursive delegation.
Use `ai-council` only when explicitly requested for a consequential decision. Do not use
application release-readiness machinery as if it certified ebook quality or legal correctness.

## Missing capabilities

| Missing capability | Safe usable fallback | Cannot claim |
| --- | --- | --- |
| Evidence Researcher | Follow research.md and maintain traceable ledger using available tools | That Evidence Researcher executed |
| AI Humanize | Protected baseline + editorial rewrite + explicit semantic diff review | That its scripts passed |
| Web access / source access | Supplied-source or historical draft, precise gaps | Current claims independently revalidated |
| Approved logo/font/reference PDF | Continue content, reserve blank asset area in draft, flag design gap | Approved branding/reference match |
| Renderer | Deliver editable source and label PDF production blocked | Rendered/visually reviewed PDF |
| Independent reviewer | Separate self-review pass with labelled limitations | Independent expert validation |
| `pypdf` for validator | Earlier stages; release records remain blocked until dependency available | PDF page-count validation |

Use host tools with the permissions they actually provide. No credential hunting,
permission expansion, safety-check bypass, background-work promises, or invented installations.

## Private repository integration

Baseline for this package: `MaciejZet/agent-skills` at
`2b644780b999df1eb24d4942abba6155ab09c485`. Existing AGENTS/README state that Actions/public
mirror are paused and an unrelated overlay integration is pending. This new skill must
not overwrite that work, PR #5, retired writer decisions, or workflow settings.

`integration/registry-entry.json` is a proposed registry object matching the observed
shape; do not treat this file as a second active routing registry. Merge it only into
`registry/skills.json` in a trusted current checkout. Keep the declared schema and existing
objects, detect duplicate IDs, use the repository's actual adapter generator, and run current
local integration/routing checks. Do not hand-edit generated adapters. Preserve unrelated
changes. Any host compatibility declaration describes intended shape, not a tested host.

A scoped package addition can be reviewed separately without pretending that the earlier
137-file overlay was integrated. Report package unit tests separately from monorepo tests,
routing evaluation, actual model behavioural runs, and completed-ebook acceptance tests.
No Actions execution, public publication, paid dependency, or permission changes are authorized
by merely creating this skill. Confirm a remote commit/branch by reading it after a write.
A ZIP, Git tree, commit object, branch update, PR, merge, host installation, and published
publication are distinct states; never conflate them.

## Format provenance

Agent Skills specification checked 2026-09-14:
https://agentskills.io/specification

This package uses portable `name`/`description` frontmatter, a description below 1024
characters, a main instruction file below 500 lines, and staged local references. No global
installation, host invocation, or model behaviour follows solely from format compliance.
