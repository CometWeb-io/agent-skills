# Repository severity calibration

Severity measures credible engineering impact on a reachable path or invariant, not code ugliness.

## CRITICAL

Admit only when a high-impact invariant, critical path, or critical surface is credibly threatened and the path is established. Require:

- evidence strength STRONG or MODERATE;
- scope sensitivity LOW or MEDIUM;
- reachability PROVEN or PLAUSIBLE;
- a non-empty execution path;
- non-low confidence;
- known blast-radius class;
- a link to a critical invariant, declared critical path, or critical surface;
- a surviving Challenger -> Defender -> Arbiter pass.

Static presence of dangerous-looking code is not enough.

Examples: a reachable cross-tenant authorization gap on a production request path; non-idempotent external settlement with a credible retry path and high-value side effect; destructive migration behavior on the deployed migration path with no containment.

## MAJOR

Use when the defect can materially affect correctness, reliability, data integrity, security posture, deployability, or operability but does not meet CRITICAL admission.

Examples: a plausible retry/data-integrity defect with bounded blast radius; an untested high-risk state transition; a release path that can silently publish stale assets; missing failure containment on a meaningful background-job path.

## MINOR

Use for local maintainability, DX, test clarity, observability, or correctness friction with bounded impact.

Examples: duplicated configuration, weak local error context, brittle test setup, dead-looking code whose reachability is not established.

## Downgrade tests

Downgrade when:

- the suspect symbol has no established caller or deployment path;
- middleware, wrapper, database constraint, provider guarantee, or runtime guard neutralizes the path;
- the evidence proves only presence, not behavior;
- the alleged absence is based on an incomplete search;
- the blast radius is materially smaller than initially assumed.

## Stop condition

If the review cannot establish the relevant topology, ref, execution path, or required runtime behavior, record a verification gap or `INSUFFICIENT_EVIDENCE`. Do not promote static suspicion into proven exploitability or production impact.
