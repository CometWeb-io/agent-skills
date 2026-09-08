# Claim-specific source routing

There is no single global source precedence. Route each material claim by claim type and keep timestamps/freshness.

| Claim | Preferred system of record | Acceptable support | Never treat as proof |
|---|---|---|---|
| Current goal / ICP / JTBD | explicit user directive; canonical product context | current PRD / strategy page | code structure |
| Roadmap / task status | designated Notion/Linear planning system | release/sprint doc | commit existence alone |
| Implementation exists | GitHub default-branch code / merged PR / commit | targeted source inspection | Notion status, README promise |
| Build/test/QA state | CI/workflow/test/audit output | targeted reproducible checks | "looks implemented" |
| Released/shipped | deploy/release/environment evidence | release tag + verified deployment record | merged PR |
| UX/runtime behavior | observed product/browser evidence | specialist QA report | source code alone |
| SEO/GEO/AEO state | specialist evidence + live site/platform evidence | connected search/webmaster data | roadmap statement |
| Adoption / outcome | analytics, customer, revenue, support evidence | explicit user-provided metric | release existence |
| Historical consequential decision | decision log / AI Council memory / ADR | dated strategy doc | current implementation |

## Evidence object

For material evidence preserve:

```json
{
  "source": "github",
  "locator": "owner/repo:path@sha",
  "claim": "Export implementation exists on default branch",
  "claim_type": "implementation",
  "stage": "implemented",
  "authority": "github",
  "observed_at": "2026-08-25T22:03:12+02:00",
  "freshness_status": "CURRENT",
  "required_current": true
}
```

Allowed freshness states:

`CURRENT | NEAR_EXPIRY | STALE | SUPERSEDED | UNKNOWN | NOT_REQUIRED`

Do not invent a generic TTL for all evidence. Use explicit source timestamps and domain-specific validity when
known. The kernel may calculate age only when `max_age_days` is explicitly supplied.

## Authority rules

The evidence source must be authoritative for the stage it proves. A Notion row can be excellent evidence for
`planned` while being zero-strength proof for `implemented`.

If multiple authoritative lanes conflict:
1. preserve both claims and timestamps;
2. identify each claim type;
3. retrieve the current system of record;
4. if unresolved and material, use `VERIFY NOW` and downgrade readiness;
5. never average a fake midpoint.

## GitHub retrieval pattern

Prefer connector-backed current reads:
1. repository metadata/default branch;
2. active release/milestone and recent relevant PR/commit state;
3. CI/workflow/release state when decision-relevant;
4. code search for unresolved implementation claims;
5. exact file fetch for proof/root cause.

Avoid broad file traversal until the critical path requires it. Do not infer current state from a stale branch.

## Notion retrieval pattern

1. Search for named product/roadmap/release/decision.
2. Fetch relevant pages before relying on snippets.
3. Fetch database/data-source schema before querying rows.
4. Query only the current horizon/status/scope.
5. Preserve last-edited/freshness information when available.

Do not hardcode private page/database IDs in a public skill.

## Product context

`.agents/product-marketing.md` can be canonical product/market intent when present. It does not prove product
implementation, runtime behavior, shipping, or outcomes.

README/landing copy may be used only as `INFERRED` context unless explicitly designated canonical.

## Prior snapshots

A Product Operator snapshot is a comparison baseline and retrieval index. It is never an authoritative source
for a current claim. Revalidate material current facts from their original systems of record.

## Unavailable systems

Use `unavailable`/`UNKNOWN`, never fabricated state. Reduced-evidence reports are allowed when scoped. State
what could materially change after the missing source becomes available.
