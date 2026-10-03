# publication-report.json contract

Use protocol `longform-publisher/1`.

Required top-level publication state:

- `protocol_version`, `as_of`, `mode`, `status`, `status_reason`;
- `publication{}` with id/title/type/audience/objective;
- `source_policy{}` and `sources[]`;
- `lifecycle{}` and `current_stage`;
- `canonical_master{path, version, sha256}` once drafting has begun;
- `sections[]`;
- `claim_uses[]`;
- `protected_facts[]`;
- `fidelity{}` and `edit_history[]` when relevant;
- `unresolved_gaps[]`;
- `derived_artifacts[]`;
- `publication_evidence[]`;
- `actions{blockers, verify_now, decision_now, now, next_milestone, delegate, waiting, stop}`.

## Fields the kernel reads

```text
protocol_version: longform-publisher/1
mode: BUILD|SOURCE_BOUND|RESEARCH_EXPAND|REFRESH
status, status_reason, as_of
publication: {id, title, type, audience, objective}
source_policy: {mode, authorized_source_ids[]}
sources[]: {id, system, locator, authorized: true|false, freshness, observed_at}
lifecycle: {brief_complete, sources_admitted, outline_locked, draft_complete,
            claims_reconciled, edited_complete, master_locked, release_ready}
current_stage: BRIEFED|SOURCE_READY|OUTLINE_LOCKED|DRAFTED|CLAIMS_RECONCILED|EDITED|MASTER_LOCKED|FORMAT_READY|RELEASE_READY|PUBLISHED
canonical_master: {path, version, sha256}
sections[]: {id, heading, status}
claim_uses[]                          # fields in claim-use.md
protected_facts[]: {id, value, required: true|false}
fidelity: {required, passed, checked_at}
edit_history[]: {type, status}
unresolved_gaps[]: {id, materiality: CRITICAL|MATERIAL|SUPPORTING, status}
derived_artifacts[]                   # fields in format-lineage.md
scientific_readiness: {status, source, evidence_ref}
publication_evidence[]: {type, locator}
prior_publication_evidence[]: {type, locator}
actions: {blockers[], verify_now[], decision_now[], now[], next_milestone[],
          delegate[], waiting[], stop[]}
```

Each `lifecycle` flag is a boolean that records one finished step, in the
order of `references/state-model.md`. The kernel infers the stage from the
first flag that is not `true` (plus fidelity and derived-format readiness), so a
later flag set while an earlier one is false does not advance the stage, and a
declared `current_stage` past the inferred one is `STAGE_INFLATION`.

An `unresolved_gaps[]` entry with `materiality: CRITICAL` blocks
`RELEASE_READY` until its `status` is `CLOSED`, `RESOLVED` or `SCOPED_OUT`; any
other materiality value returns `FIELD_VALUE_INVALID:unresolved_gaps.materiality`.
An `edit_history[]` entry with `status: COMPLETE` and `type` `AI_HUMANIZE`,
`STRONG_REWRITE`, `DEEP_REWRITE` or `SUBSTANTIAL_REWRITE` requires
`fidelity.required` and `fidelity.passed` to be `true`. A `protected_facts[]`
entry with `required: true` must appear verbatim in the manuscript. An action
item is a string or an object rendered from `action`, `question`, `label` or
`id`, with an optional `done_when`.

The report fields `status`, `status_reason`, `as_of`, `sections[]` and the
evidence `type`/`locator` are carried for the reader; the kernel prints
`status` and `status_reason` in the manifest but does not check them.

## Admission rules

- SOURCE_BOUND may reference only authorized sources.
- Material FACT claims cannot claim reconciliation without support. Every `evidence_ref` must resolve to a registered source; otherwise return `EVIDENCE_REF_UNRESOLVED`.
- Volatile current claims cannot rely only on stale/unknown evidence.
- Declared `current_stage` cannot exceed the stage inferred from gates.
- Critical open gaps block RELEASE_READY.
- `PUBLISHED` requires publication evidence.
- `SCIENTIFIC_MANUSCRIPT`, `ACADEMIC_PAPER`, and `RESEARCH_PAPER` at RELEASE_READY/PUBLISHED require `scientific_readiness.status=PASS`, `source=research-program-operator`, and a resolvable evidence reference; otherwise return `SCIENTIFIC_READINESS_REQUIRED`.
- Substantial rewrite/humanization requires post-edit fidelity before MASTER_LOCKED.
- Derived artifacts must bind to the current master hash and pass format-specific QA/parity.

Run the kernel in this order when applicable:

```bash
python3 scripts/publication_kernel.py validate --report-json publication-report.json
python3 scripts/publication_kernel.py check-manuscript --report-json publication-report.json --manuscript-file manuscript.md
python3 scripts/publication_kernel.py check-derived --report-json publication-report.json
python3 scripts/publication_kernel.py render-manifest --report-json publication-report.json --output publication-brief.md
python3 scripts/publication_kernel.py check-brief --report-json publication-report.json --brief-file publication-brief.md
```
