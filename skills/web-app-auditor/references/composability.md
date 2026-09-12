# Composability and evidence handoff

Web App Auditor owns **user-facing QA evidence**. It does not own whole-project roadmapping, production release authorization, customer-account communication, or strategic decisions.

## Lossless audit handoff

Preserve these fields when exporting findings:

- target URL/route/screens, persona, viewport, environment, and mutation policy;
- capability profile and audit depth;
- release/build/commit identity when actually known;
- finding ID, kind, severity, confidence, expected basis, repro, actual/expected, impact;
- evidence IDs/types/locations and redaction state;
- coverage states (`tested | sampled | policy-blocked | environment-blocked | unreachable | out-of-scope`);
- final verdict and any `incomplete` reason.

Do not convert `needs-repro` into a confirmed defect. Do not convert `sampled` or `unreachable` into `tested`.

## Common downstream consumers

- `release-readiness` — may consume QA/Product/Support evidence only when the audit is tied to the same release candidate/environment. If candidate identity is absent or mismatched, evidence cannot satisfy a candidate-specific binding pass.
- `product-operator` — may consume accepted current findings as product-state evidence and create bounded actions after dependency/state reconciliation.
- `repo-to-roadmap` — may incorporate confirmed user-facing gaps into a whole-project roadmap; the audit itself does not prove repo-wide absence or implementation scope.
- `customer-ops` — may request verification of an original customer-visible symptom during closure. Auditor verifies behavior; Customer Ops owns case/customer resolution state.
- `evidence-researcher` — use when a material external standard/platform claim needs deeper authority/freshness/contradiction work.
- `ai-council` — consume findings only when a consequential decision requires them; do not turn Council deliberation into QA proof.

## Revalidation

If code/build/environment changes after the audit, treat candidate-bound evidence as potentially invalidated. Re-run the affected flows rather than carrying the old `ship` conclusion forward by analogy.
