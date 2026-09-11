# Portfolio model

## Domain taxonomy

Use one primary domain per item:

- `CLIENT` — paid/client delivery, migrations, maintenance promises, proposals with commitments;
- `PRODUCT` — owned products, repositories, product GTM tied to a product;
- `RESEARCH` — academic research, papers, conferences, grants, scientific-circle work;
- `GROWTH` — marketing/sales work not already embedded in a product-level control plane;
- `OPS` — recurring operational/system work;
- `ADMIN` — finance, legal, institutional, procurement, compliance;
- `OTHER` — only when none of the above fits.

## Commitment types

- `hard_external` — promise/deadline owed to another party or official external deadline;
- `hard_internal` — binding internal gate/date with real downstream consequence;
- `strategic` — important bet aligned to a goal but not a hard obligation;
- `optional` — useful improvement without current obligation/gate.

Do not promote strategic work to hard commitment merely because it matters.

## Effort classes

When hours are not known, use:

- `XS` — trivial/contained;
- `S` — small;
- `M` — moderate;
- `L` — large;
- `XL` — dominates a meaningful portion of the horizon;
- `UNKNOWN` — insufficient evidence.

Do not convert effort classes into invented hours.

## Portfolio status

Portfolio-level project states:

- `PRIMARY_FOCUS`
- `SECONDARY_FOCUS`
- `MAINTENANCE`
- `WAITING`
- `PAUSED`
- `CLOSED`
- `UNKNOWN`

These describe allocation, not implementation state.

## Evidence-backed item

Recommended item shape:

```json
{
  "id": "client-migration",
  "project": "Client Site",
  "domain": "CLIENT",
  "action": "Complete the client migration commitment",
  "scope_level": "portfolio",
  "commitment_type": "hard_external",
  "deadline": "2026-09-20",
  "evidence_ref": "calendar:event-456",
  "effort_class": "L",
  "goal_alignment": 5,
  "revenue": 4,
  "trust": 5,
  "strategic_value": 2,
  "learning": 1,
  "dependency_leverage": 4,
  "blocks_current_goal": false,
  "future_gate": false,
  "depends_on": [],
  "blocked_by": [],
  "evidence": ["crm:deal-123", "calendar:event-456"],
  "done_when": "Production cutover, redirects, analytics and email/DNS checks verified."
}
```

Unknown fields may remain absent/UNKNOWN. Never backfill them from intuition.

## Precision and delegation fields

Use these fields when relevant:

```text
scope_level: portfolio | specialist
portfolio_outcome: concise user-facing outcome used by the renderer when specialist depth exists
evidence_ref: exact source for a user-facing date/number/target
user_defined: true when the user explicitly supplied or approved the exact value
delegate_to: confirmed specialist/person/agent/system
delegate_evidence_ref: proof an external delegate exists/is available
delegate_candidate: true when an executor is only a candidate
```

Portfolio-facing `MUST DO`/`NOW` items must stay `scope_level=portfolio`. Specialist detail belongs in the handoff, not the portfolio brief.
