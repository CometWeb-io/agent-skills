# GitHub issue proposal — plan change drops the stored VAT ID

Repository conventions: checked
Dedupe search: done
Closest related issue: example-org/billing#401 (closed; different tax path)
Engineering readiness: PASS
Privacy preflight: findings-redacted
Write status: draft

## Issue body

**Customer-visible symptom:** after a Starter → Growth upgrade the next invoice applies 0% VAT for an account with a validated VAT ID.
**Linked customer cases:** CASE-2207 (1 account). Account identifiers and invoice numbers are redacted.
**Reproduction:** upgrade a staging account with a VAT ID from Starter to Growth and inspect the draft invoice.
**Expected:** the stored VAT ID and rate carry over to the new plan.

Proposed / needs approval: create this issue in example-org/billing.
