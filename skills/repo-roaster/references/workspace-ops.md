# Workspace operations

Use this file when a review spans multiple sources, people, revisions, CI runs, or evidence-acquisition cycles.

## Persistent workspace

Prefer a workspace over chat-only state when review continuity matters. A workspace should pin:

- the review session and source fingerprints;
- an append-only review journal;
- the evidence-request queue;
- generated reports and which report is active;
- downstream dispositions kept outside the reviewer report.

The workspace is an operational record, not authority to release, publish, deploy, treat, purchase, or otherwise approve a downstream action.

## Journal discipline

Record material workflow transitions such as scope creation, source drift, review start, evidence request, report attachment, re-review, disposition handoff, and closure. The journal hash chain is tamper-evident within the file; it is not an author signature or identity proof.

Do not place private chain-of-thought, hidden reasoning, credentials, unnecessary personal data, or full sensitive source excerpts in journal payloads. Record bounded operational facts and stable references.

## Evidence-request queue

Use explicit evidence requests when a material conclusion cannot be safely admitted from the current sources. A request should state:

- the exact question that remains unanswered;
- why it changes a finding, claim, or review outcome;
- priority (`LOW`, `MEDIUM`, `HIGH`, `BLOCKING`);
- linked finding keys when applicable;
- owner when one exists;
- resolution reference or bounded waiver/unavailability note.

An open evidence request is not automatically a defect. A `BLOCKING` request means the configured review policy may choose to stop or fail the review gate until the gap is resolved.

## Large-source sampling

For large source trees, a deterministic sampling plan may prioritize candidate files or documents. Treat it only as a navigation proposal. It does not make unselected material clean, reviewed, irrelevant, or unreachable.

Expand the sample when dependency paths, citations, changed files, call graphs, contradictory evidence, or reviewer findings point outside the initial selection.

## Fix verification

A previous finding is not resolved merely because it disappeared from a later report. Resolution requires the old verification contract to pass or equivalent evidence to close it. Preserve these distinctions:

- `RESOLVED`
- `PARTIAL`
- `OPEN`
- `REGRESSED`
- `NOT_ASSESSABLE`
- `UNVERIFIED_DISAPPEARANCE`

Do not convert a human `FIX_PLANNED` or `ACCEPTED_RISK` disposition into reviewer evidence that the defect is fixed.

## Policy gates

Use named review policies for repeatable team/CI behavior. A policy may define:

- finding-severity threshold;
- whether stale accepted-risk/deferral records fail;
- whether blocking evidence requests fail;
- the allowed count of unresolved high-priority evidence requests.

These are review-policy controls only. They do not replace `release-readiness`, publication authorization, legal review, security testing, or other downstream specialist decisions.

## Model-level evaluation

When comparing skill versions, separate deterministic contract tests from actual model-level evaluations. A model benchmark needs real run outputs for the same cases, comparable source access, and independent grading for semantic assertions. Do not infer model quality from repository test count or validator coverage alone.

## Incremental re-review state

If source snapshots are available, preserve them as workspace artifacts. A source diff may nominate changed files and prior findings for recheck, but closure still requires the old verification contract or equivalent evidence. Record the resulting fix-verification artifact rather than editing history.

If the workspace participates in a larger review campaign, keep campaign aggregation outside the canonical report. Cross-artifact counts and calibration statistics are operational metadata, not evidence for the current finding.
