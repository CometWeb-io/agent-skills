# Invoice Portal Billing Module Evidence-Based Roadmap

## 1. Executive state

- Target: INTERNAL_BETA for the billing module only — staff can issue and settle invoices in the sandbox (T-01).
- Demonstrated maturity: issuing and settling are verified by CI and an end-to-end sandbox run (CAP-01, CAP-02).
- Proven blockers: none. Suspected blockers: none inside the focused scope.
- Highest-leverage verified gap: refunds are not part of the beta target; nothing blocks the beta.
- Recommended posture: READY_FOR_NEXT_PHASE

## 2. Assessment pin and confidence

- Mode: FOCUSED (billing module only; this is not a whole-project roadmap)
- Repo: `example-org/invoice-portal` @ `b71c03e`, path `src/billing/`
- Assessment as_of: 2026-10-03T09:30:00+02:00
- Coverage grade: B (focused scope; deployment inspected through the sandbox only)
- Not inspected: everything outside `src/billing/`

## 3. Target State Contract

| Requirement | Domain | Mandatory | Applicability | Source |
|---|---|---:|---|---|
| T-01 | core_flow | yes | APPLIES | user brief |
| T-02 | product | no | APPLIES | user brief |

## 4. Project truth map

| Capability | State | Criticality | Claim refs | Target refs | Confidence |
|---|---|---|---|---|---|
| CAP-01 invoice issuing | VERIFIED_WORKING | high | C-01 | T-01 | high |
| CAP-02 sandbox settlement | VERIFIED_WORKING | high | C-02 | T-01 | high |
| CAP-03 refunds | UNKNOWN | low | C-03 | T-02 | low |

## 5. Critical findings / Evidence Ledger

- C-01 → issuing an invoice is covered by an integration test → Evidence: CI run 901 @ b71c03e → band VERIFIED → none.
- C-02 → a sandbox payment marks the invoice PAID → Evidence: E2E run 77 log and sandbox payment id `pay_example_123` → band VERIFIED → none.
- C-03 → refund code paths were not found in search → Evidence: search of `src/billing/` only, NOT_FOUND_IN_SEARCH, absence protocol not run → band LOW → refunds stay UNKNOWN, not MISSING.

## 6. Roadmap

| ID | Lane | Kind | Outcome | Why now | Claim refs | Acceptance proof | Depends on | Effort | Confidence |
|---|---|---|---|---|---|---|---|---|---|
| R-01 | NEXT | VALIDATE | Learn whether beta staff need refunds | refunds are outside the beta target | C-03 | notes from five staff interviews | — | S | 0.40 |
| R-02 | LATER | BUILD | Partial refunds from the invoice page | only if R-01 shows demand | C-03, T-02 (target) | E2E refund run in the sandbox | R-01 | M | 0.30 |

## 7. Dependency waves and leverage

- Wave 1 — objective: start the internal beta. No roadmap item gates it. Exit: beta opened to staff.
- Wave 2 — objective: decide on refunds. Items R-01 then R-02. Trigger: three or more staff refund requests reopen the order.

## 8. Verify / validate backlog

- VALIDATE: R-01.
- VERIFY: run the absence protocol for refunds before anyone calls them MISSING.

## 9. Defer / do not do yet

- Card vaulting: not needed for an internal beta. Reopen for PAID_PRODUCTION.

## 10. Living-roadmap watch conditions

- Baseline snapshot: `sha256:5e0c4b7a9d2f1e83` (focused scope only)
- Watch C-02: any change to `src/billing/settle.ts` reruns the sandbox E2E.

## 12. Final readiness statement

Roadmap defensible with current evidence for the billing module; it says nothing about the rest of the project.
