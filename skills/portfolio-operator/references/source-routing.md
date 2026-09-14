# Source routing

Use claim-specific authority. Do not impose one global source order.

| Claim | Preferred authority | Notes |
| --- | --- | --- |
| Current portfolio goal / explicit constraint | user directive or canonical strategy/plan | Latest explicit directive can supersede older planning notes. |
| Hard time commitment | Calendar / official deadline source | A calendar event proves scheduled time, not completion. |
| Client promise / deliverable / commercial deadline | contract, CRM, customer email/thread, approved statement of work | Preserve exact commitment and due date. |
| Planned project/task status | Notion/Linear/project tracker | Planning truth only; not proof of implementation/outcome. |
| Code/implementation/release signal | GitHub/CI/deployment evidence | Retrieve only when it can change portfolio allocation; delegate deep reconciliation to Product Operator. |
| Product-level priority / critical path | current Product Operator output | Treat as specialist handoff, not as a replacement for portfolio allocation. |
| Customer/account risk | CRM/support/customer communication | Delegate operational depth to Customer Ops. |
| Research/submission/funding deadline | official call, conference/journal/grant source, institutional communication | Notion may mirror it but is not automatically authoritative. |
| Revenue/outcome | billing/CRM/analytics/customer evidence | Do not infer from activity or shipped code. |
| Historical decision | decision log / ADR / Council record | Revalidate if facts or scope changed. |
| Prior portfolio snapshot | Portfolio Operator snapshot | Baseline/index only; not current truth. |

## Retrieval rules

1. Start with hard commitments, current goals, and the active horizon.
2. Retrieve only project state capable of changing allocation.
3. When a product requires deep repo/state analysis, create a Product Operator handoff rather than crawling the whole repo here.
4. When a connector is unavailable, mark the lane partial/unavailable and continue if enough evidence remains.
5. Do not silently substitute a weaker source for an unavailable system-of-record.
6. Stop when new retrieval is unlikely to change the human lanes.

## Freshness

For each material evidence object preserve, when available:

```text
source
locator
claim
observed_at / effective_at
authority
freshness: CURRENT | AGING | STALE | SUPERSEDED | UNKNOWN
```

A stale hard-deadline or customer-commitment claim must be revalidated before using it to make a current allocation decision.
