# Event Taxonomy and Materiality

## Contents

1. Categories
2. Change types
3. Materiality inputs
4. Score interpretation
5. Response posture
6. Pattern rules

## 1. Categories

Use one primary category and optional secondary tags.

| Category | Typical signals |
|---|---|
| `PRODUCT_CAPABILITY` | New/removed feature, workflow, platform, API, integration, model support |
| `PRICING_PACKAGING` | Price, tier, value metric, limits, free plan, trial, contract structure |
| `POSITIONING_MESSAGING` | Headline, category framing, ICP, use-case emphasis, differentiation claims |
| `CUSTOMER_PROOF` | Named customers, case studies, reviews, ratings, proof themes |
| `DISCOVERY_GTM` | SEO/content, paid-media signals, partnerships, distribution, channel expansion |
| `COMPANY_ORG` | Funding, M&A, leadership, hiring patterns, geographic expansion |
| `TECH_TRUST` | Stack signals, security/compliance claims, status/reliability, certifications |
| `SALES_MOTION` | Enterprise motion, procurement signals, partner/reseller motion, sales packaging |
| `MARKET_SIGNAL` | Category-level or multi-competitor movement not owned by one competitor |
| `OTHER` | Material change that does not fit above |

## 2. Change types

- `ADDED`
- `REMOVED`
- `MODIFIED`
- `REVERSED`
- `ANNOUNCED`
- `SHIPPED`
- `SUNSET`

Use `ANNOUNCED` and `SHIPPED` only when lifecycle evidence supports the distinction.

## 3. Materiality inputs

Score each 0–1 using explicit anchors.

### Relevance — 30%

- `0.0`: unrelated to our ICP, product, or GTM.
- `0.5`: adjacent; may matter to a secondary segment or future roadmap.
- `1.0`: directly affects a core buying criterion, strategic segment, moat, or major acquisition channel.

### Magnitude — 25%

- `0.0`: cosmetic or negligible.
- `0.5`: meaningful but localized change.
- `1.0`: major launch, pricing model shift, category repositioning, acquisition, broad platform change, or similar structural move.

### Evidence confidence — 20%

- `0.2`: weak/derived only.
- `0.5`: credible secondary or incomplete first-party evidence.
- `0.8`: strong direct evidence.
- `1.0`: direct evidence plus meaningful corroboration for a material claim.

### Novelty — 15%

- `0.0`: already known/repeated alert.
- `0.5`: incremental development.
- `1.0`: genuinely new information or first evidence of a new direction.

### Persistence — 10%

- `0.2`: single transient observation.
- `0.5`: repeated/lasting for at least one refresh cycle.
- `1.0`: persistent or independently repeated over time.

Competitor tier multiplies the score:

- Tier 1: `1.00`
- Tier 2: `0.85`
- Tier 3: `0.70`

The deterministic kernel implements these weights.

## 4. Score interpretation

| Score | Severity | Default behavior |
|---:|---|---|
| 80–100 | `CRITICAL` | Immediate deep dive / strategic escalation |
| 65–79 | `HIGH` | Include in current brief and assign follow-up |
| 45–64 | `MEDIUM` | Digest/watchlist unless context raises priority |
| 25–44 | `LOW` | Store, usually suppress from exec output |
| 0–24 | `NOISE` | Do not promote to intelligence event |

Do not force a high score because the change sounds dramatic. Separate evidence confidence from business relevance.

## 5. Response posture

Choose one:

- `IGNORE` — no meaningful action.
- `WATCH` — monitor for persistence/corroboration.
- `VERIFY` — evidence insufficient.
- `TEST` — run a reversible experiment rather than copy/react.
- `RESPOND` — update roadmap, messaging, pricing, sales enablement, or channel execution.
- `ESCALATE` — send to AI Council or a human decision owner because the implication is consequential.

A recommended response must name the mechanism. "Competitor launched X, therefore build X" is not sufficient.

## 6. Pattern rules

Promote events into a pattern only if at least two meaningful observations support the same hypothesis, preferably across different source types or time points.

For every pattern record:

- supporting event keys,
- hypothesis,
- confidence,
- time window,
- strongest falsifier,
- affected strategic assumptions.

Patterns never upgrade the verification state of weak underlying facts by themselves.
