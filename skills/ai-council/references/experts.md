# Role registry v4

## Role classes

### Advisers

Głosują nad atrakcyjnością decyzji:

- `strategy` — strategic choice, moat, optionality, allocation.
- `product_customer` — problem, JTBD, adoption, product evidence.
- `operator` — feasibility, sequencing, capacity, execution risk.
- `marketing` — positioning, category, messaging, demand.
- `sales` — buying process, pipeline, objections, commercial motion.
- `offer_pricing` — value, packaging, pricing, monetization.
- `growth` — acquisition, activation, retention, referral, loops.

### Specialists

Uruchamiaj warunkowo:

- `finance` — capital allocation, unit economics, runway, opportunity cost, VOI.
- `m_and_a` — acquisition logic, due diligence, integration economics.
- `localization` — market-entry/local adaptation.
- `technical` — architecture, integration, migration, maintainability, scalability.
- `data` — measurement validity, causality, power, bias, instrumentation.
- `people` — org design, talent, incentives, hiring.
- `partnerships` — channels, ecosystems, partner economics.
- `change_management` — rollout, adoption, migration, training.

### Gatekeepers

Nie są zwykłymi głosami:

- `legal` — jurisdiction-aware legal/regulatory constraints.
- `security` — threat surface and security acceptance.
- `privacy` — personal-data constraints and privacy controls.
- `financial_risk` — downside/capital exposure and risk tolerance.
- `responsible_ai` — material harms not reducible to pure legality.
- `reputation` — stakeholder/reputational downside.

### Auditors

- `red_team` — strongest credible failure/contrarian case.
- `evidence_judge` — claim/evidence/framework admissibility.
- `minority_sentinel` — protect material independent dissent.
- `process_auditor` — detect routing/process failures and unnecessary deliberation.

### Authority

- `chairman` — synthesize accepted material only and respect binding gates.

## Routing rules

- Wybieraj role wg Decision Contract i risk surfaces.
- Nie uruchamiaj pełnego registry.
- Nie licz gatekeepera jako dodatkowego niezależnego głosu.
- Nie myl `finance` (opportunity/capital allocation) z `financial_risk` (downside gate).
- Nie myl `technical`, `security` i `privacy`.
- Po routingu wykonaj missing-perspective check.
- Jeśli kolejny specjalista nie wnosi nowego materialnego claimu, assumption, evidence gap, constraint ani testu, użyj stop rule zamiast dodawać role.
