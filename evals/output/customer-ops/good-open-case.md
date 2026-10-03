# Case: CASE-2207 / invoices show the wrong VAT rate after plan change

**As of:** 2026-10-02T14:05:00+02:00
**Coverage:** PARTIAL (billing provider export unavailable; helpdesk, CRM and GitHub checked 2026-10-02T13:50+02:00)
**State:** ENGINEERING
**Account:** Contoso Example GmbH (acct-1190)
**Type:** billing bug
**Evidence grade:** MEDIUM
**Operational priority:** P1
**Account escalation:** EXPEDITED
**Retention risk:** MEDIUM
**Native SLA/deadline:** UNKNOWN (provider SLA state not readable; not rebuilt from timestamps)
**Owner:** engineering

## Customer-visible problem

**Symptom:** after upgrading from Starter to Growth, the next invoice applied 0% VAT instead of the customer's 19%.
**Desired outcome / expected:** a corrected invoice with the right VAT rate.
**Confirmed impact:** one invoice for one account; finance cannot book it.

## Evidence

### Confirmed / observed

- [Helpdesk | ticket 2207 | 2026-09-30T08:41Z] customer report with the invoice number.
- [CRM | company acct-1190 | 2026-10-02T13:48Z] VAT ID present and validated.

### Reported

- The customer believes all upgraded accounts are affected; not checked.

### Unknowns / contradictions

- The billing provider export was unavailable, so we cannot see the tax calculation record; decisions about other accounts are blocked until it is read.

### Hypotheses

- H1: the plan-change path drops the stored tax ID before the invoice is generated — next test: replay a Starter → Growth upgrade on a staging account with a VAT ID and inspect the draft invoice.
- H2: the VAT ID was revalidated and failed during the upgrade — next test: read the provider's tax ID validation log for acct-1190 once the export is available.

## Linked work

- Cluster: none yet (one account)
- Incident: none
- GitHub issue/PR/release: example-org/billing#418 (open)
- Handoff: support → engineering, ACCEPTED 2026-10-01, IN_PROGRESS

## Commitments

- CM-1: send the customer a status update — Owner: support — Due: 2026-10-03T12:00+02:00 — OPEN (promised in [Helpdesk | ticket 2207 | 2026-09-30T10:02Z])

## Next action

**Owner:** engineering
**Action:** run the H1 replay; support sends the CM-1 update whatever the result.
**Checkpoint/deadline:** CM-1 due 2026-10-03T12:00+02:00

## Customer communication

**Status:** draft
Draft status update prepared for CM-1; needs approval before sending.

## Verification / closure

**Verification criterion:** a corrected invoice for acct-1190 shows 19% VAT and the customer's finance team confirms it can be booked.
**Current:** still open
