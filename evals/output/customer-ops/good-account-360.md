# Account 360: Contoso Example GmbH — 2026-10-02T11:00+02:00

**As of:** 2026-10-02T11:00+02:00
**Coverage:** PARTIAL (billing provider export unavailable)
**Operational question:** is anything blocking the 2026-11-01 renewal?

## Current operational status

- Risk MEDIUM; owner account manager; next action: confirm the VAT fix date with engineering.

## Commercial context

- Growth plan since 2026-09-12, 12 seats [CRM | company acct-1190 | 2026-10-02T10:40Z].
- Renewal 2026-11-01 [CRM | contract C-1190 | 2026-10-02T10:41Z].

## Open cases

- CASE-2207 — wrong VAT rate after plan change (P1, engineering).

## Incident exposure

- None: the account is on the US cluster and was outside INC-31.

## Usage / product health evidence

- Weekly active users steady at 10 of 12 seats over the last four weeks.

## Retention-risk evidence

- No exit intent stated; finance cannot book one invoice until CASE-2207 is fixed.

## GitHub / engineering dependencies

- example-org/billing#418 (open) for CASE-2207.

## Commitments

- CM-1: status update due 2026-10-03T12:00+02:00 (open).

## Handoffs

- HO-11: support → engineering, accepted 2026-10-01, blocked on the billing provider export.

## Recent customer feedback / trust signals

- Finance contact asked twice for an ETA; tone polite but pressed.

## Recommended operational action

- Send the CM-1 update with a realistic fix window. Owner: support.
- Ask engineering for a dated fix plan before 2026-10-09. Owner: account manager.

## Conflicts / stale / missing sources

- Plan name differs between the CRM (Growth) and the helpdesk form (Starter); the newer CRM record is used.
- Billing provider export unavailable, so invoice state is not read directly.
