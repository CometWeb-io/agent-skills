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

## Kernel fields

`scripts/portfolio_kernel.py` reads these item keys; `references/contract.json` is the
machine-checked copy. Keys it does not read are carried along and ignored.

```text
id                      item identifier
project                 groups items for the hard-load conflict; falls back to domain, then id
domain                  CLIENT, PRODUCT, RESEARCH, GROWTH, OPS, ADMIN, OTHER; either case; PRODUCT routes product reconciliation
commitment_type         hard_external, hard_internal, strategic, optional; any other value is an error
effort_class            XS, S, M, L, XL, UNKNOWN; any other value is an error (default UNKNOWN)
days_to_deadline        integer days left; the only deadline input to ranking urgency
deadline                ISO date; used for same-day conflicts and the provenance gate, not for ranking
goal_alignment          0..5
revenue                 0..5
trust                   0..5
dependency_leverage     0..5
learning                0..5
blocks_current_goal     true moves the item to MUST DO and above other gates
future_gate             true without blocks_current_goal means WAITING
current_horizon         default true; false keeps a hard commitment out of MUST DO and the load check
pause                   true, or drop or stop, means PAUSE_DROP
drop
stop
depth_required          product, release, support, customer-ops, evidence, strategic-decision, portfolio-decision, orchestration; any other value is an error
needs_product_reconciliation  with domain PRODUCT, routes to product-operator
release_verdict_required      routes to release-readiness
customer_incident             routes to customer-ops
claim_verification_required   routes to evidence-researcher
decision_required             routes to ai-council
multi_skill_execution         routes to skill-orchestrator
delegated_to            explicit executor; same as delegate_to
scope_level             portfolio, specialist; any other value is an error
action                  user-facing text
portfolio_outcome       user-facing text that replaces action
condition               user-facing text
question                user-facing text; required in delegate[]
reason                  user-facing text
return_contract         required in delegate[]
done_when               required in must_do[] and now[]
evidence                required in must_do[] and now[]
evidence_ref            provenance for user-facing numbers and dates
user_defined            provenance when the user supplied the value
delegate_to
delegate_evidence_ref
delegate_candidate
```

`strategic_value`, `depends_on` and `blocked_by` in the example above are not read by the
kernel: record them for the reader, and express ordering through `blocks_current_goal` and
`future_gate`. The kernel also rejects the specialist detail keys `substeps`,
`internal_steps`, `implementation_steps`, `component_tasks` and `technical_details` on a
delegated must_do or now item.

The report passed to `validate` and `render` is the machine sidecar in `output-contract.md`.
The kernel reads `capacity` (`source`, `hours`), `readiness` (`status`, `reason`) and the
lanes `must_do`, `capacity_conflicts`, `now`, `delegate`, `delegate_candidate`,
`waiting`, `pause_drop`, `next` and `decision_now`; it does not read `protocol_version`,
`as_of`, `horizon`, `primary_goal`, `portfolio_scope`, `constraints`, `coverage`,
`portfolio_items` or `unknowns`. `readiness.status` is printed as is (READY, PROVISIONAL,
BLOCKED; default PROVISIONAL) and not checked. `rank` adds `priority_score` and `gate_rank`;
`conflicts` returns rows with `type` (HARD_COMMITMENT_OVERLAP, PORTFOLIO_HARD_LOAD) and
`item_ids`; `validate` returns `valid` and `errors`.
