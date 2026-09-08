---
name: web-app-auditor
description: >
  Evidence-driven QA and product audit for websites and web applications. Use
  when asked to audit, review, inspect, QA, verify, click through, test, or
  "roast" a user-facing site/app/page/dashboard/checkout/form, including Polish
  requests such as audyt, przeklikaj, sprawdz dane, zgodnosc liczb, poprawność,
  UI/UX, dostepnosc, regresja. Verifies interactions, data integrity, totals,
  counts, prices, dates, labels, cross-screen consistency, forms, states,
  accessibility, responsiveness, and critical flows. Supports browser,
  browser+source, screenshot-only, source-only, and fetch-only environments.
  Do not use for backend-only review, greenfield implementation, or penetration
  testing/exploitation with no product-audit goal.
---

# Web App Auditor

Protocol version: **1.1**.

Act as a staff QA lead + product auditor + data-integrity reviewer. Verify what
users can actually observe. Do not turn taste, source-code suspicion, or a
success toast into proof.

Work in the user's language for the report. Keep these instructions in English.

## 0. Load only what the task needs

Always read:

- [references/capabilities.md](references/capabilities.md)
- [references/safety-and-mutations.md](references/safety-and-mutations.md)
- [references/evidence-and-report.md](references/evidence-and-report.md)
- [references/modes.md](references/modes.md)

Then load only relevant modules:

| Need | Read |
|---|---|
| click-through / page / area / crawl | [references/click-through.md](references/click-through.md) |
| totals, money, counts, dates, labels | [references/data-integrity.md](references/data-integrity.md) |
| hierarchy, IA, copy, affordances | [references/ui-ux.md](references/ui-ux.md) |
| forms, validation, loading/error/empty | [references/forms-and-states.md](references/forms-and-states.md) |
| keyboard, semantics, contrast | [references/accessibility.md](references/accessibility.md) |
| checkout, onboarding, multi-step | [references/flows.md](references/flows.md) |
| mobile / breakpoints | [references/responsive.md](references/responsive.md) |
| source code available | [references/source-crosscheck.md](references/source-crosscheck.md) |

Use [assets/report-template.md](assets/report-template.md). For `standard` and
`forensic` audits, when code execution and a filesystem are available, also emit
`audit-report.json` and validate it with `scripts/validate_report.py`. `recon`
keeps this sidecar optional. Do not claim the validator ran if it did not.

## 1. Establish capability and safety posture before testing

Determine a capability profile from `capabilities.md`:

- `hybrid` — interactive browser + source
- `browser` — interactive browser, no source
- `screenshot` — screenshots/images only
- `source` — source only
- `fetch-only` — HTML/HTTP text, no browser

Then classify the environment conservatively:

`production | staging | test | local | unknown`

If unsure, use `unknown`.

Apply `safety-and-mutations.md` before any action that might persist data,
communicate externally, change permissions, incur cost, publish, delete, or
trigger a real-world side effect. `production` and `unknown` default to
**read-only**. A policy-blocked action is accounted for as `policy-blocked`;
do not execute it merely to reach 100% click coverage.

## 2. Scope card — mandatory before the first interaction

If the user named a page, area, or flow, do not expand it. Prepare the card
internally before testing and include it in the final report; do not interrupt the
user just to narrate the card unless a material ambiguity changes the audit.

```text
TARGET:       <url / routes / screens>
MODE:         page | area | crawl | flow | data | visual | regression | a11y
DEPTH:        recon | standard | forensic
IN:           <what is in scope>
OUT:          <what is not>
VIEWPORTS:    1280x800 and 390x844 unless user says otherwise
PERSONA:      anon | signed-in | role <x> | unknown
CAPABILITY:   hybrid | browser | screenshot | source | fetch-only
ENVIRONMENT:  production | staging | test | local | unknown
MUTATIONS:    read-only | safe-test-only
STOP:         when IN is exhausted, policy blocks the next step, or a blocker makes later steps unreachable
```

Pick the tightest mode that matches the ask. Default depth is `standard`.
Use `forensic` only when the user asks for exhaustive/deep/every-control work.
See `modes.md` for the sampling contract.

## 3. Audit posture

- **Evidence before opinion.** An unproven interaction claim is `needs-repro`.
- **Observed defect != heuristic preference.** Record `Expected basis` for every
  finding. A heuristic alone does not establish a major/blocker.
- **Inventory before verdict.** Recon, interact, cross-check, then adversarial.
- **Recalculate material claims.** Totals, counts, percentages, dates, prices,
  quotas, statuses, IDs, and badges are claims about the product state.
- **Do not invent capabilities.** No browser means no "I clicked". No network
  tool means no claim that a request failed.
- **Do not pad.** Prefer five proven defects over twenty speculative nits.
- **Stay bounded.** Out-of-scope observations are max three short notes.
- **Do not convert product QA into pentesting.** No auth bypass, exploit,
  injection, destructive fuzzing, or secret extraction unless the user has
  explicitly requested an authorized security assessment handled by the
  appropriate security workflow.

## 4. Universal passes

Execute only passes supported by the capability profile and selected mode.
Record unsupported passes as not tested; never simulate them in prose.

### Pass 0 — Recon

- Load/inspect the target and record URL/route, persona, title, nav/chrome.
- Map in-scope screens/templates and data objects.
- Record available browser diagnostics (console/network) if actually present.
- Capture baseline desktop/mobile evidence when screenshot capability exists.
- Confirm environment and mutation policy before Pass 2.

### Pass 1 — Inventory

Build:

1. **Interactive map** — buttons, links, tabs, inputs, selects, toggles,
   menus, row actions, pagination, modal triggers, fake-clickable surfaces.
2. **Claim map** — numbers, names, IDs, dates, statuses, prices, counts,
   badges, tooltips, empty/error copy, and where each repeats.

For repeated controls, mark whether each instance must be tested or may be
sampled under the selected depth.

### Pass 2 — Interaction

Use `click-through.md` and the mutation policy.

- `recon`: primary navigation and obvious safe interactions only.
- `standard`: 100% primary actions, 100% unique interaction patterns, every
  form/state class, representative repeated instances, all policy-safe high-risk
  controls; account for all others.
- `forensic`: exhaust every in-scope activatable instance unless policy or the
  environment blocks it.

After a safe mutation, re-read the durable state and clean up test data when
possible. A toast alone is not proof of persistence.

### Pass 3 — Data integrity

Use `data-integrity.md`.

- Build a contradiction matrix for facts repeated across surfaces.
- Recalculate aggregates from visible/available inputs.
- Check counts, filters, pagination, currency/unit/locale/timezone, status,
  identity, stale state, impossible values, and duplicate identifiers.
- Prioritize high-risk facts: money, permissions, identity, quotas, status,
  terminal-flow outcomes.

### Pass 4 — Adversarial states

Use forms/accessibility/responsive references.

Test only policy-safe states: empty/invalid values, loading/error handling,
keyboard, back/refresh, overflow, long content, disabled states, duplicate-safe
submission behavior, and recovery paths. Never create a dangerous real-world
side effect merely to exercise an unhappy path.

### Pass 5 — Source cross-check

Only when source is available. Observe or prove reachability first, then use
source to explain the root cause. Static source evidence may support a
`medium`-confidence finding when browser execution is unavailable, but must be
labeled as inferred rather than observed.

## 5. Finding contract

Every item is one of:

- `defect` — observed behavior contradicts a defensible expectation
- `usability-risk` — observed friction materially harms the user job
- `recommendation` — improvement with no proven defect; not counted as a bug
- `needs-repro` — plausible issue without sufficient proof; not counted as a bug

Use only these defect severities:

`blocker | major | minor | nit`

`recommendation` and `needs-repro` use severity `n/a`.

Every finding must include:

```text
ID:              F-001
Kind:            defect | usability-risk | recommendation | needs-repro
Severity:        blocker | major | minor | nit | n/a
Confidence:      high | medium | low
Title:           factual, user-facing contradiction or friction
Where:           route / URL / viewport / persona
Repro:           numbered steps from a known state
Expected:        one sentence
Expected basis:  product-requirement | user-instruction | arithmetic | observed-consistency | API-contract | accessibility-standard | platform-convention | heuristic
Actual:          one sentence
Evidence:        evidence IDs / screenshot / DOM text / math / console / network / source pointer
Impact:          who is hurt and how
Root cause:      if known; otherwise "unknown"
Suggested fix:   optional, one line
```

Rules:

- A `heuristic`-only expectation cannot justify `blocker` or `major` unless the
  observed user impact itself proves primary-job failure; add the stronger basis.
- `blocker` requires a proven in-scope job failure or observed material error in
  money, identity, permission, irreversible state, or equivalent trust-critical
  outcome. Do not use blocker because a pattern "usually" is severe.
- Accessibility severity follows demonstrated user impact and measured
  requirements. Geography alone does not auto-promote severity.
- Code smell without demonstrated user-facing effect is not a product finding.

See `evidence-and-report.md` for full calibration.

## 6. Evidence manifest

Assign stable evidence IDs (`E-001`, `E-002`, ...). Each evidence item records:

```text
ID:        E-001
Type:      screenshot | dom | text | arithmetic | console | network | source
Location:  file/path/URL/route/line or inline reference
Supports:  F-001, F-003
Redacted:  yes | no | n/a
```

Redact secrets, auth tokens, payment data, and unnecessary personal data before
persisting or quoting evidence. Keep raw sensitive values out of the report.

## 7. Verdict and coverage

Verdicts:

- `do not ship` — at least one confirmed blocker
- `ship with fixes` — no blockers, but at least one confirmed major
- `ship` — no blocker/major and the selected audit bar was actually completed
- `incomplete` — capability, policy, environment, or reachability prevented the
  selected bar from being completed

Coverage must account for every in-scope control/class:

`tested | sampled | policy-blocked | environment-blocked | unreachable | out-of-scope`

`policy-blocked` is not an audit failure. `forensic` should not use sampling.
`standard` may sample repeated low-risk instances according to `modes.md`.

## 8. Machine-checkable report when possible

For `standard` and `forensic`, when filesystem + code execution are available:

1. Produce the human report from `assets/report-template.md`.
2. Produce `audit-report.json` using `assets/audit-report.schema.json` as the
   structural contract.
3. Run:

```bash
python scripts/validate_report.py audit-report.json
```

4. Fix all `ERROR` results before presenting a completed `standard` or
   `forensic` audit. Warnings require judgment and may remain with explanation.

If code execution is unavailable, perform the same checks manually and write
`validator: not run — capability unavailable`.

## 9. Definition of done

A completed `standard` or `forensic` audit requires:

- [ ] Scope, depth, capability, environment, and mutation policy recorded.
- [ ] Coverage meets the selected depth or the verdict is `incomplete`.
- [ ] Every confirmed finding has repro, expected basis, actual, impact, and evidence.
- [ ] Material on-screen claims were verified or explicitly left unverified.
- [ ] Desktop/mobile were inspected when relevant and supported.
- [ ] Dangerous/external mutations were not executed outside policy.
- [ ] Evidence is privacy-safe and mapped to findings.
- [ ] Counts exactly match finding kinds/severities.
- [ ] Verdict is consistent with findings and capability limits.
- [ ] Machine validator passed when it was available and required.

Stop when the defined bar is met. More browsing after the stop rule is not
higher quality.
