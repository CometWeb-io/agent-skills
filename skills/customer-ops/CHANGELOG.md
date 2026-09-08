# Changelog

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
