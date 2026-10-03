# Release Readiness — example-app v2.4.0

## Verdict

GO_WITH_CONTROLS

- Candidate: `example-app` v2.4.0, image digest `sha256:4f1c…9a2e` (build 1187)
- Target environment: production (`app.example.com`)
- Assessment as_of: 2026-09-30T14:10:00+02:00
- Profile / mode / risk tier: `saas_web` / STANDARD / R2
- Readiness score: 86/100
- Evidence coverage: 100% of required gates
- Snapshot hash: `9b41d07e…c3`

Every required gate has candidate-bound evidence and no blocking implementation failure was found. The release changes invoice rendering, so the one residual risk is a PDF regression for very long line items; it is bounded by a feature flag with a named owner and a rollback trigger. Ship behind the flag and keep it off for accounts with more than 200 line items until the watchpoint clears.

## Scope and required-gate completeness

- Audience: external customers
- Commercial model: paid
- Risk flags set to yes: none (`billing_change`, `auth_change` and `data_migration` are all no)
- Unresolved risk flags: none
- Governance surfaces: none required
- Required gates: 9; missing required gates: 0
- Required minimum mode: STANDARD; current mode STANDARD satisfies it

## Binding gates

| Gate | Domain | Status | Evidence | Candidate fit | Why it matters |
| --- | --- | --- | --- | --- | --- |
| `observability` | ops | PASS_WITH_CONTROLS | Dashboard `invoices-render` with p95 and error panels, checked 2026-09-30 | build 1187 | PDF failures must be visible within minutes |
| `release_scope_acceptance` | product | PASS | Acceptance checklist signed for v2.4.0 | build 1187 | Scope matches the release notes |
| `candidate_verification` | qa | PASS | E2E run #5521, 142/142 green | build 1187 | Critical journeys pass on the candidate |
| `security_release` | security | PASS | Dependency scan run #883, no high findings | build 1187 | No known exploitable dependency |
| `release_delivery` | ops | PASS | Staging deploy of the same digest, 2026-09-29 | build 1187 | The artifact deploys cleanly |
| `recovery_strategy` | ops | PASS | Rollback rehearsal log 2026-09-29, 4 min | build 1187 | A bad release can be reverted |
| `operator_docs` | docs | PASS | Runbook section "Invoice PDF" updated in the same PR | build 1187 | On-call knows the flag |
| `support_path` | support | PASS | Support macro "PDF missing" published | build 1187 | Customers have a path |
| `billing_entitlements` | billing | PASS | Plan-to-entitlement mapping verified on staging | build 1187 | Paid access is delivered |

## Release blockers

No blocking implementation failure was found within assessed scope.

## Evidence gaps

- None that change the verdict. Load testing of PDF rendering above 200 line items was not run; the control below bounds it.

## Domain readiness

| Domain | Score | Coverage | Status | Decisive evidence / risk |
| --- | ---: | ---: | --- | --- |
| product | 92 | 100% | PASS | Acceptance checklist |
| qa | 88 | 100% | PASS | E2E run #5521 |
| security | 90 | 100% | PASS | Dependency scan #883 |
| ops | 80 | 100% | PASS_WITH_CONTROLS | Long-invoice rendering bounded by flag |
| docs | 85 | 100% | PASS | Runbook updated |
| billing | 84 | 100% | PASS | Entitlement mapping |
| support | 82 | 100% | PASS | Macro published |

## Controlled risks

- Residual risk: PDF rendering may time out for invoices with more than 200 line items.
- Control: feature flag `invoice_pdf_v2` stays off for those accounts; owner: billing on-call (named in the runbook).
- Due/expiry: 2026-10-14. Invalidated if the flag is removed or the threshold changes.
- Rollout trigger: PDF error rate above 1% for 10 minutes disables the flag.

## Ship / closure plan

1. **Before deploy** — confirm the production digest matches build 1187 and the flag default is off for large accounts.
2. **During rollout** — 10% of accounts for two hours, then 100%.
3. **Watchpoints** — PDF error rate, render p95, support tickets tagged "PDF missing".
4. **Recovery triggers** — PDF error rate above 1% for 10 minutes: billing on-call disables `invoice_pdf_v2`; rollback if the error persists.
5. **First observation window** — first 24 hours after 100% rollout.

## Post-release debt

- MINOR: the invoice preview spinner has no timeout message.

## Scope, confidence, and assurance limits

- Verified on candidate build 1187: E2E suite, dependency scan, staging deploy, rollback rehearsal.
- Inferred from static evidence: flag wiring in the invoice service.
- Not performed: penetration test, legal review (not required for this change).
- Not evidenced: PDF rendering under load above 200 line items.

```json
{
  "id": "release-readiness:ReleaseEnvelope:example-app-v2.4.0",
  "type": "ReleaseEnvelope",
  "producer": "release-readiness",
  "producer_version": "1.4.0",
  "protocol_version": "2.0",
  "subject": "example-app v2.4.0 build 1187",
  "generated_at": "2026-09-30T14:10:00+02:00",
  "as_of": "2026-09-30T14:10:00+02:00",
  "sensitivity": "internal",
  "dependencies": [],
  "payload": {
    "schema": "cometweb.release/v2",
    "release_candidate": "example-app v2.4.0 build 1187",
    "environment": "production",
    "verdict": "GO_WITH_CONTROLS",
    "gates": [
      {"gate_id": "observability", "status": "PASS_WITH_CONTROLS"},
      {"gate_id": "candidate_verification", "status": "PASS"}
    ],
    "blockers": [],
    "controls": ["invoice_pdf_v2 off for accounts above 200 line items"],
    "as_of": "2026-09-30T14:10:00+02:00",
    "manifest_hash": "9b41d07ec3"
  },
  "payload_hash": "pending"
}
```

Decision: GO_WITH_CONTROLS — ship with `invoice_pdf_v2` off for accounts above 200 line items until the 24-hour watchpoint clears.
