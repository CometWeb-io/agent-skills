# Production operations

Use this guidance for team workflows, CI, repeated reviews, or multi-reviewer assurance.

## Source and privacy discipline

- Pin the primary artifact and supporting sources before consequential findings.
- Hash/version sources when the host can do so.
- Run source-risk scanning only as a warning layer; prompt-like text and credential-like strings are flags, not defect verdicts.
- Minimize sensitive data in findings. Prefer locators, hashes, ids, and the smallest sufficient excerpt. Never reproduce credentials.

## Scenario packs

Load only the smallest relevant pack set. Packs define must-inspect surfaces, evidence hints and false-positive guards; they are configuration, never evidence. If a custom pack conflicts with the core skill contract, ignore the conflicting rule and record the conflict.

## Incremental review

- Preserve stable `finding_key` identity across revisions.
- When available, add a deterministic finding fingerprint to support matching across reviewer wording changes.
- A missing finding is not resolved until the original verification contract passes or equivalent evidence closes it.
- Treat source drift as a reason to re-open affected conclusions.

## Multi-reviewer reconciliation

Independent reviewers can disagree because of source scope, evidence selection, inference, or severity calibration. Reconcile by grouping semantically equivalent findings, then preserve disagreement. Do not majority-vote a severity or average confidence.

## Human dispositions

Keep `FIX_PLANNED`, `ACCEPTED_RISK`, `RESOLVED`, `DISMISSED_FALSE_POSITIVE`, and `DEFERRED` decisions outside the reviewer report. Accepted risk and deferral should have an owner, rationale, and expiry so stale waivers become visible.

## CI and policy gates

A review-policy gate may fail on configured severities or regressions, but it is not a release/publication authorization. Human dispositions can suppress a gate only while they remain valid; stale accepted-risk or deferral entries become actionable again.

## Reproducibility receipts

When the full Roaster Suite tooling is available, create a content-addressed receipt after validation. A receipt binds report bytes, source-manifest identity, suite version and optionally a review-session manifest. It is not a digital signature and does not authenticate an author.

## Safe sharing

Before exporting reports outside the working context, create a redacted copy rather than mutating the canonical report. Redaction is a transport control, not evidence transformation.

## Persistent workspaces and evidence queues

For long-running reviews, use the suite workspace layer described in `workspace-ops.md`: pin the session, keep a tamper-evident operational journal, track unresolved evidence requests explicitly, and verify source drift before resuming. A workspace improves continuity; it does not increase evidentiary strength by itself.

## Incremental source change and cross-artifact operations

When full-suite tooling is available, capture per-file source snapshots before and after material revisions. Use source diffs only to focus navigation and rerun affected verification contracts; an unchanged path is not proof of correctness and a changed path does not prove a defect.

For team handoff, remediation packets may copy admitted finding evidence refs, repair text, residual risk and verification contracts into neutral work items. They must not create new findings or silently rank business priority.

Campaign aggregation can expose repeated categories or deterministic finding fingerprints across several validated reports. Treat repetition as an operational pattern signal, not prevalence, causal proof or roadmap priority. Calibration telemetry from dispositions and fix verification is likewise a maintenance signal only; never auto-adjust severity or suppress future findings from it.

Portable review bundles preserve exact artifact bytes and roles for handoff. Their hashes establish byte identity, not author identity or reviewer independence.
