---
name: longform-publisher
description: Use when ChatGPT must build, refresh, reconcile, or release a long-form publication such as an ebook, report, playbook, white paper, guide, handbook, or research-backed article across manuscript and derived document formats.
---

# Longform Publisher

Protocol version: **longform-publisher/1**. Skill release: **1.0.0**.

Operate as a publication control plane. Own the canonical manuscript, source policy, claim-use traceability, editorial gates, version lineage, derived-artifact readiness, and publication state. Do not become a duplicate research, rewriting, DOCX, PDF, or marketing-copy specialist.

## 0. Load the control plane

Always read:

- [references/state-model.md](references/state-model.md)
- [references/source-policy.md](references/source-policy.md)
- [references/claim-use.md](references/claim-use.md)
- [references/fidelity-gate.md](references/fidelity-gate.md)
- [references/format-lineage.md](references/format-lineage.md)
- [references/report-contract.md](references/report-contract.md)
- [references/output-contract.md](references/output-contract.md)

Read when relevant:

- [references/delegation.md](references/delegation.md) before specialist handoff;
- [references/evaluation.md](references/evaluation.md) when testing or modifying this skill.

When code execution is available, use `scripts/publication_kernel.py` for deterministic admission and artifact checks. Use `scripts/run_evals.py` when modifying the skill. Never claim either ran when it did not.

## 1. Establish the publication contract

Resolve before drafting:

```text
MODE:              BUILD | SOURCE_BOUND | RESEARCH_EXPAND | REFRESH
PUBLICATION:       <title/type or UNKNOWN>
AUDIENCE:          <reader>
OBJECTIVE:         <reader outcome>
SOURCE POLICY:     <authorized materials / research permission>
CANONICAL MASTER:  manuscript.md
OUTPUT FORMATS:    <MD/DOCX/PDF/HTML/etc.>
VOICE / STYLE:     <constraints>
CURRENT STAGE:     <canonical stage>
PRIOR VERSION:     <available | unavailable>
MUTATIONS:         <read-only unless explicitly authorized>
AS OF:             <offset-aware timestamp>
```

Do not invent current facts, citations, proof, customer outcomes, statistics, quotes, or publication status.

## 2. Use the canonical lifecycle

Use [references/state-model.md](references/state-model.md).

`BRIEFED -> SOURCE_READY -> OUTLINE_LOCKED -> DRAFTED -> CLAIMS_RECONCILED -> EDITED -> MASTER_LOCKED -> FORMAT_READY -> RELEASE_READY -> PUBLISHED`

Side states: `NEEDS_RESEARCH / NEEDS_AUTHOR_INPUT / BLOCKED / SUPERSEDED / ARCHIVED`.

Preserve these non-equivalences:

- discovered link != admitted evidence;
- Evidence Pack != manuscript;
- outline != draft;
- draft != fact/claim-reconciled manuscript;
- AI Humanize output != semantically verified master;
- valid Markdown != valid DOCX/PDF;
- generated DOCX/PDF != FORMAT_READY;
- generated file != PUBLISHED;
- PUBLISHED != current/fresh.

Use the earliest defensible stage.

## 3. Keep `manuscript.md` canonical

Treat `manuscript.md` as the editorial source of truth. DOCX, PDF, HTML, EPUB, and other formats are derived artifacts.

Apply material content changes to the canonical master first. Regenerate and revalidate derived artifacts afterward. Never treat a direct material edit to a PDF/DOCX as a canonical manuscript update.

Record master version and SHA-256 in `publication-report.json` and bind every derived artifact to that hash.

## 4. Enforce source policy and claim use

Use [references/source-policy.md](references/source-policy.md) and [references/claim-use.md](references/claim-use.md).

- `SOURCE_BOUND`: use only explicitly authorized sources. Do not silently browse, use model memory, or import adjacent files as factual support.
- `RESEARCH_EXPAND`: route consequential external verification to `evidence-researcher` and consume its admitted evidence.
- `REFRESH`: re-open only stale/changed claims and affected sections where possible.
- Material factual claims require support or an explicit unresolved state.
- Volatile current claims require current/near-expiry evidence; stale-only support reopens the source gate.

Keep claims, evidence, citations, and prose separate. A citation-looking string is not evidence admission.

## 5. Draft and reconcile before style polishing

Lock the outline before full drafting when structure materially affects coverage. Draft from admitted sources and section contracts.

Before `CLAIMS_RECONCILED`, check:

- every critical/material claim has an allowed evidence state;
- citations/attribution match the claim actually made;
- uncertainty, scope, time window, and causal direction are preserved;
- unresolved research gaps are explicit;
- protected facts are registered.

Do not use style editing to hide unresolved evidence gaps.

## 6. Require a post-edit fidelity gate

Use [references/fidelity-gate.md](references/fidelity-gate.md).

After AI Humanize, strong/deep rewrite, or another substantial re-expression, do **not** promote directly to `MASTER_LOCKED`. Run a **post-edit fidelity gate** against the pre-edit claim/invariant state.

At minimum verify protected names, numbers, dates, units, URLs, citations, identifiers, quotes, modal/negation/scope-sensitive phrases, and user-designated wording.

If AI Humanize changes `may` to `will`, drops `37%`, changes a date, or removes a required citation, fail the gate until reconciled.

## 7. Delegate specialist depth

Use [references/delegation.md](references/delegation.md).

Route:

- consequential research/fact verification -> `evidence-researcher`;
- scientific program/manuscript readiness -> `research-program-operator`;
- natural-language editing -> `ai-humanize`;
- marketing-page conversion copy -> `copywriting`;
- DOCX generation/render QA -> `docx`;
- PDF generation/render QA -> `pdfs`;
- publication graphics -> `image`;
- content portfolio/topic planning -> `content-strategy`.

Re-enter Longform Publisher after a specialist result changes source readiness, manuscript fidelity, format readiness, or release state.

## 8. Gate derived artifacts

Use [references/format-lineage.md](references/format-lineage.md).

A derived artifact can be `FORMAT_READY` only when it:

- references the current `canonical_master.sha256`;
- finished generation;
- passed required QA;
- passed material content parity;
- contains no direct material edit that bypassed the master.

DOCX and PDF require the visual render/inspection gate demanded by the respective `docx` and `pdfs` skills. File existence alone is not QA.

## 9. Gate release and publication

`RELEASE_READY` requires a locked current master, resolved critical gaps, required derived formats ready, release metadata complete, and no unresolved placeholder/draft marker.

`PUBLISHED` requires publication evidence such as a live URL, repository release, platform record, uploaded-artifact confirmation, or explicit user-confirmed publication event. A local file alone is insufficient.

A historically published artifact may remain `PUBLISHED` while a new refresh is `BLOCKED` or `NEEDS_RESEARCH`; publication history and current freshness are different dimensions.

## 10. Produce and admit the sidecar

Use [references/report-contract.md](references/report-contract.md). Create `publication-report.json`.

When execution is available, run:

```bash
python3 scripts/publication_kernel.py validate --report-json publication-report.json
python3 scripts/publication_kernel.py check-manuscript --report-json publication-report.json --manuscript-file manuscript.md
python3 scripts/publication_kernel.py check-derived --report-json publication-report.json
python3 scripts/publication_kernel.py render-manifest --report-json publication-report.json --output publication-brief.md
python3 scripts/publication_kernel.py check-brief --report-json publication-report.json --brief-file publication-brief.md
```

The deterministic gate is **validate -> check-manuscript -> check-derived -> render-manifest -> check-brief** when those stages/artifacts exist.

Structural PASS does not prove external facts are true; it proves the report obeys this protocol.

## 11. Return the right primary output

Use [references/output-contract.md](references/output-contract.md).

When the user asks for the publication itself, the finished manuscript or requested derived artifact is primary. Do not replace it with a control brief.

When the user asks for status/readiness/refresh planning, use:

`Stan -> PUBLICATION SUMMARY -> CURRENT STAGE -> BLOCKER -> VERIFY NOW -> DECISION NOW -> NOW -> NEXT MILESTONE -> DELEGATE -> WAITING -> STOP`

Omit empty lanes. Keep actions atomic and executable.

## Definition of done

A publication run is complete when:

- mode, audience, objective, source policy, and requested formats are explicit;
- `manuscript.md` is the canonical source of truth;
- every material claim is supported, intentionally scoped/attributed, or explicitly unresolved;
- SOURCE_BOUND has no unauthorized factual source;
- substantial rewriting passed the post-edit fidelity gate;
- protected invariants survived or were explicitly reconciled;
- derived artifacts point to the current master and passed required QA/parity;
- critical placeholders/gaps do not leak into release-ready output;
- PUBLISHED is backed by publication evidence;
- specialist depth is delegated rather than duplicated;
- deterministic gates pass when execution is available.
