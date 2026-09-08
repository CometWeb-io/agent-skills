# Evidence, finding calibration, and report

## 1. Evidence standard

A confirmed finding needs reproducible evidence appropriate to the claim:

- screenshot/render showing the visible state
- exact on-screen/DOM text
- arithmetic derived from visible/authorized inputs
- observed console error or failed network request
- source pointer that deterministically explains an observed/static fact
- before/after durable state for a policy-safe mutation

A screenshot proves only what is visible. A toast proves only that a toast was
shown. Source proves implementation facts, not an executed browser outcome.

Use stable evidence IDs (`E-001`...) and map them to finding IDs.

## 2. Expected basis — mandatory

Every finding states why `Expected` is defensible. Use one or more:

- `product-requirement` — explicit spec/design/acceptance criterion
- `user-instruction` — explicit requirement from the user for this audit
- `arithmetic` — mathematical/logical invariant
- `observed-consistency` — same entity/fact behaves differently elsewhere
- `API-contract` — documented response/schema/behavior contract
- `accessibility-standard` — measured applicable criterion/pattern
- `platform-convention` — strong platform/web semantic convention
- `heuristic` — UX best practice/opinionated pattern

Do not present a heuristic as a product requirement. A heuristic-only item is
normally a `recommendation`, `nit`, or `usability-risk` backed by demonstrated
friction. It does not become `major` because the auditor strongly prefers it.

## 3. Finding kinds

### `defect`

Observed behavior contradicts a defensible expectation or invariant.

### `usability-risk`

Observed design/interaction materially impairs comprehension, discoverability,
error recovery, accessibility, or completion, even if no explicit spec is
available. State the demonstrated user effect.

### `recommendation`

Improvement opportunity without a proven defect. Severity is `n/a` and it is
not counted as a bug.

### `needs-repro`

Evidence is insufficient or capability is too weak. Severity is `n/a` and it
is not counted as a bug.

## 4. Confidence

- `high` — directly observed/measured in the relevant execution surface
- `medium` — deterministic static/source evidence; interaction not fully run
- `low` — incomplete hypothesis; use `needs-repro`

Do not inflate confidence because multiple weak clues point in the same
direction.

## 5. Severity calibration

Severity is user impact, not emotional intensity.

### `blocker`

Use when a confirmed issue prevents the in-scope primary job for affected users,
or produces an observed trust-critical error with comparable consequence, such
as wrong charged amount, wrong identity/recipient, wrong permission/access, or
irreversible destructive state.

### `major`

Primary job remains possible only with a meaningful workaround, a large share
of users is materially impaired, important data/state is misleading, or a
recoverable flow can cause material loss/confusion.

### `minor`

Real contained defect with a limited workaround/impact. Does not materially
block the primary job.

### `nit`

Confirmed polish/consistency/copy defect with low user impact.

Pattern tables elsewhere are hints only. Final severity must follow this
section. Geography, technology choice, or "destructive control" alone does not
automatically produce a blocker.

When uncertain between two severities, choose the lower one and explain the
impact unless direct evidence supports escalation.

## 6. Evidence privacy

Before persisting evidence:

- redact tokens, credentials, secrets, card data, private keys
- minimize personal data and crop irrelevant user records
- avoid secret values in filenames/titles
- never move private raw data to public search just to corroborate a finding

Record `redacted: yes | no | n/a` in the evidence manifest.

## 7. Verdict

Use exactly:

- **do not ship** — at least one confirmed blocker
- **ship with fixes** — no blocker, at least one confirmed major
- **ship** — no blocker/major and the selected audit bar is complete
- **incomplete** — capability/policy/environment/reachability prevented the bar

Do not average severities. `needs-repro` does not force `do not ship`; it may
force `incomplete` when it concerns a terminal requirement that must be proven.

## 8. Coverage honesty

Account for in-scope interactions with:

- `tested` — executed and result recorded
- `sampled` — representative repeated instance under `standard`/`recon`
- `policy-blocked` — unsafe/disallowed to execute under mutation policy
- `environment-blocked` — captcha/paywall/missing account/tool constraint
- `unreachable` — product defect/route failure prevented access
- `out-of-scope` — discovered but intentionally outside IN

Never classify `policy-blocked` as a product defect. If a terminal outcome is
essential but cannot be tested safely, verdict is `incomplete`.

## 9. Counts

Report counts must be exact:

`blocker | major | minor | nit | needs-repro | recommendations`

Only confirmed `defect`/`usability-risk` items contribute to the first four.
`needs-repro` and `recommendation` have severity `n/a`.

## 10. Machine validation

For `standard` and `forensic`, when code execution + filesystem are available,
produce `audit-report.json` and run. For `recon`, the JSON sidecar is optional:

```bash
python scripts/validate_report.py audit-report.json
```

The validator checks IDs, allowed values, count arithmetic, verdict coherence,
coverage arithmetic, capability/verdict conflicts, forensic sampling, unsafe
environment mutation policy, finding-kind/severity combinations, evidence
references, and heuristic-only severity escalation.

`ERROR` must be fixed before a completed `standard`/`forensic` report.
`WARNING` is a judgment prompt; explain any warning you intentionally keep.

If the validator cannot run, say so. Never fabricate a pass.

## 11. Tone

Neutral, specific, concise. No praise padding, humiliation, or invented user
sentiment. A hard audit can be direct without being theatrical.
