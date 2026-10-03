# Changelog

## [2.2.0] - 2026-10-02

### Changed

- Front door cut from 16.3 KB to 13.0 KB. The A–I workflow procedure moved to
  `references/workflow.md`; SKILL.md keeps the stage names and the rules each
  stage must never drop. The case field list, source classes and output fields
  are pointed to rather than repeated.
- `write-authority.md` and `outputs.md` are no longer listed as read-always:
  they load before any write/send/close and before writing the output, which
  is when their rules apply.
- The description sends roadmap prioritization to Product Operator and
  release-candidate verdicts to Release Readiness by name.
- `tests/front-door-rules.json` pins every hard boundary and never-drop rule.

### Fixed

- The owner-class list offered `unknown` and the next sentence said to use
  `unassigned`; the kernel warns on `unknown`. The list now ends in
  `unassigned`.

## [2.1.1] - 2026-10-02

### Changed

- `SKILL.md` sections 6-15 restated per-mode procedures that each already lives
  in a reference (`triage-priority.md`, `incidents.md`, `feedback-churn.md`,
  `commitments-and-handoffs.md`, `metrics-and-sla.md`, `github-loop.md`,
  `outputs.md`). They are now one mode table that names the reference and keeps
  only the rules a mode must never drop. The front door shrank from 19.7 KB to
  16.2 KB; no rule was removed from the package. Composability, output
  discipline and hard boundaries are renumbered 7-9.

## 2.1.0 — 2026-09-12

- Add scoped currentness, evidence, safety and domain acceptance contracts.
- Normalize host metadata and verify standalone package structure.
- Preserve the existing executable decision protocol and its fixtures; skill release version and protocol version remain separate.

## 2.0.0 — 2026-08-25

- Rebuilt Customer Ops around an explicit case graph rather than a flat ticket model.
- Separated operational priority, customer-impact incident severity, evidence grade,
  retention risk, account escalation, and SLA/deadline state.
- Replaced weighted priority/churn outputs with conservative rule-based operational
  fallbacks; retained numeric ranking only as a within-band tie-break aid.
- Reworked SLA handling so provider-native state or authoritative due dates win;
  continuous-clock reconstruction is opt-in and provider policy is never guessed.
- Added source-of-truth, provenance, temporal truth, contradiction, and coverage rules.
- Added customer commitment tracking and explicit handoff acceptance/lifecycle.
- Added incident exposure mapping, recovery/verification separation, and safer incident
  communication rules.
- Strengthened GitHub customer-to-engineering loop with repo reconnaissance, dedupe,
  privacy preflight, issue readiness gates, dependency/sub-issue guidance, and
  fix-to-release-to-customer verification.
- Added explicit write-authority tiers, idempotency/retry controls, bulk mutation
  manifests, post-write read-back, and safe failure handling.
- Expanded modes to include commitment-watch and handoff-watch.
- Expanded specialist-skill handoff contracts and return-to-Customer-Ops contracts.
- Added deterministic kernel commands for priority, retention risk, incident severity,
  deadline state, dedupe candidate review, commitments, state transitions, case gates,
  and privacy preflight.
- Expanded regression/evaluation coverage with adversarial customer-ops scenarios.

## 1.0.0 — 2026-08-25

- Initial Customer Ops operating model.
- Added support/case triage, incident coordination, feedback synthesis, churn-risk watch,
  account 360, GitHub customer-to-engineering loop, ops briefs, and closure verification.
- Added deterministic priority, churn-risk, incident-severity, SLA, and dedupe kernel.
- Added privacy/write-authority guardrails and specialist-skill handoffs.
