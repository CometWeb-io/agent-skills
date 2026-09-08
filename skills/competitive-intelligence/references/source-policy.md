# Evidence and Source Policy

## Contents

1. Claim-type authority
2. Source classes
3. Verification states
4. Corroboration rules
5. Freshness
6. Contradiction search
7. Access/privacy controls
8. Unsupported claims

## 1. Claim-type authority

Source authority depends on what is being claimed.

| Claim type | Preferred evidence |
|---|---|
| Competitor public price/package/feature | Direct competitor first-party source (`A`) |
| Competitor shipped/announced state | Official docs/changelog/release/announcement (`A`) |
| Buyer perception / deal objection | Authorized internal buyer/call/win-loss evidence (`I`) plus broader corroboration when generalizing |
| Market reception | Review aggregates / multiple independent buyer sources (`B`/`I`) |
| Traffic/SEO/ad scale | Methodologically disclosed derived data (`D`), always labeled estimated |
| Company event | Official filing/announcement (`A`) or strong independent reporting (`B`) |

Do not use a high-authority source for the wrong claim type. A sales-call quote can be authoritative evidence that a buyer said something; it is not direct proof that the competitor feature actually works as described.

## 2. Source classes

Use the highest-authority source available for the claim type.

### A — First-party direct

Examples:

- official pricing/product/docs/changelog pages,
- official company announcements,
- official public repositories and releases,
- official marketplace listings,
- official status/security/compliance pages,
- official regulatory filings where applicable.

Use as primary evidence for what the competitor publicly offers, claims, prices, ships, or announces.

### I — Internal authorized

Examples:

- CRM competitive notes,
- win/loss interviews,
- call transcripts,
- sales/CS field observations,
- internal product or deal notes.

Use only when the user has authorized access. Treat as high authority for internal deal context and buyer-reported perception, not automatically as proof of competitor public state. Keep the provenance lane private and do not paste private raw content into public web searches.

### B — High-quality independent

Examples:

- reputable reporting with named sourcing,
- established review-platform aggregates,
- independent analyst/market data with disclosed methodology,
- verified marketplace/platform records not controlled by the competitor.

Use for corroboration, context, market reception, and facts not available first-party.

### C — Community / anecdotal

Examples:

- Reddit/forum discussions,
- individual reviews,
- social posts,
- community screenshots.

Use for hypothesis generation and sentiment signals. Do not upgrade to verified company fact without stronger evidence.

### D — Derived / estimated

Examples:

- estimated traffic,
- estimated ad spend,
- SEO visibility estimates,
- inferred technology detection,
- model-generated interpretation.

Use as directional evidence only. Keep methodology/uncertainty visible.

## 3. Verification states

### CONFIRMED

Use when one of the following is true:

- one direct A source clearly supports a competitor-public-state claim and no material contradiction is known;
- two meaningfully independent B sources support a claim for which no direct A source is reasonably available; or
- one authorized internal I source directly proves the narrower internal observation (for example, that a specific buyer raised an objection), without generalizing that observation into a universal competitor fact.

### LIKELY

Use when evidence is credible but incomplete, indirect, time-limited, region-limited, or not independently corroborated.

### UNVERIFIED

Use when evidence is C/D-only, ambiguous, or too weak for an operational conclusion.

### DISPUTED

Use when material credible sources conflict and the conflict is unresolved.

### RETRACTED

Use when a previously accepted event was shown to be wrong, rolled back, or based on invalid evidence. Preserve the original event; append the correction.

## 4. Corroboration rules

Corroboration must add independence or authority. Multiple pages repeating the same press release are not independent confirmation.

For high-impact events, verify scope:

- country/region,
- customer segment,
- plan/tier,
- new vs existing customers,
- preview/beta vs generally available,
- announced vs actually shipped,
- list price vs effective price.

## 5. Freshness

Every current material claim needs `last_verified_at`.

Use configurable TTLs rather than assuming a source remains current indefinitely. Pricing, packaging, and changelog claims usually deserve shorter TTLs than company-history facts.

Use:

```bash
python scripts/ci_kernel.py freshness --last-verified-at <ISO8601> --ttl-days <N> [--as-of <ISO8601>]
```

Possible statuses:

- `CURRENT`
- `NEAR_EXPIRY`
- `STALE`
- `UNKNOWN`

A stale material claim may remain in history but should not support an unconditional current conclusion.

## 6. Contradiction search

For a material change, perform a separate search for evidence that could defeat the claim. Typical falsifiers:

- old page cached/indexed after a rollback,
- local pricing rather than global pricing,
- beta feature presented as generally available,
- feature available only through a partner,
- grandfathered pricing,
- temporary promotion,
- customer-logo page without active-customer confirmation,
- third-party estimate that conflicts with first-party reporting.

Record unresolved contradictions explicitly.

## 7. Access and privacy controls

Use only public or explicitly authorized sources and connector access. Do not bypass authentication, CAPTCHAs, paywalls, rate limits, access controls, or platform/tool restrictions.

Do not seek confidential competitor information, credentials, private workspaces, non-public customer records, or leaked datasets.

Minimize personal data. Prefer company-level signals and aggregate hiring trends. A named public executive move may be relevant when it is officially announced or clearly material; do not build employee dossiers.

## 8. Unsupported claims

Do not present these as verified without appropriate evidence:

- exact customer counts inferred from logos,
- revenue inferred from traffic,
- strategy inferred from one hire,
- product adoption inferred from release notes,
- churn inferred from review sentiment,
- ad spend inferred from ad-library presence,
- market share inferred from SEO visibility,
- roadmap inferred from a single beta page.
