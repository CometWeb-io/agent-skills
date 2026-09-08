# Pattern transfer model

## Table of contents

1. Pattern taxonomy
2. Abstraction ladder
3. Candidate pattern card
4. Transferability dimensions
5. Negative transfer and false friends
6. Interaction graph
7. Prioritization principles
8. Common transfer traps

## 1. Pattern taxonomy

Use the narrowest useful category:

- `jtbd_workflow` - how a user job is decomposed and completed.
- `information_architecture` - hierarchy, navigation, progressive disclosure.
- `interaction` - state transitions, controls, feedback, recovery, batch actions.
- `activation_onboarding` - path to first value, setup, import, empty states.
- `collaboration_permissions` - sharing, roles, approvals, ownership.
- `monetization` - packaging, limits, upgrade triggers, value metric.
- `data_domain_model` - entities, relationships, state machine, persistence.
- `architecture` - boundaries, orchestration, async work, caching, extensibility.
- `developer_experience` - local setup, APIs, CLI, plugin model, testability.
- `reliability_operations` - observability, retries, recovery, migrations, flags.
- `trust_safety` - permissions, auditability, privacy, security, explainability.
- `growth_distribution` - sharing loops, templates, artifacts, integrations.

Do not invent a new category merely to restate a feature name.

## 2. Abstraction ladder

Translate source detail through four levels:

1. **Instance** - "Product X opens a command palette with Cmd+K."
2. **Behavior** - "Users can invoke navigation/actions from a global keyboard surface."
3. **Mechanism** - "Reduce navigation cost by exposing high-frequency actions through searchable command routing."
4. **Transferable pattern** - "For expert workflows with many routes/actions, provide a global command surface indexed over permitted entities/actions, with context-aware ranking."

Keep level 1 as evidence. Recommend levels 3-4.

## 3. Candidate pattern card

Use:

```text
Pattern ID / name
Family ID when multi-source
Category
Problem
Source observation(s)
Mechanism hypothesis
Source evidence IDs
Destination evidence IDs
Transfer conditions
Existing target capability
Adaptation options
Chosen transfer mode
Implementation path
Interaction dependencies/conflicts
Risks / anti-patterns
Validation plan
Verdict
Confidence decomposition
```

## 4. Transferability dimensions

### Positive dimensions

- `problem_fit` - destination has the same underlying problem.
- `mechanism_fit` - mechanism plausibly addresses that problem under target conditions.
- `source_evidence_strength` - source behavior/implementation is established.
- `destination_evidence_strength` - target problem/current state is established.
- `implementation_feasibility` - target can build and operate it.
- `expected_upside` - material value if the mechanism works.
- `reversibility` - transfer can be contained/rolled back.
- `maintenance_fit` - long-run burden fits team capability.
- `strategic_fit` - supports target strategy rather than distracting from it.
- `differentiation` - improves target value, not only parity.

### Penalties

- `dependency_risk` - hidden data/scale/vendor/org prerequisites.
- `complexity_tax` - cognitive, operational, and architectural burden.
- `opportunity_cost` - displaces higher-value target work.
- `legal_ip_risk` - license, copyright, trademark, trade-dress, contract concerns.
- `security_privacy_risk` - access, data, abuse, or trust surface.
- `measurement_risk` - inability to observe whether transfer helped.

Use `scripts/score_patterns.py` only for deterministic sorting. Never treat its score as factual evidence.

## 5. Negative transfer and false friends

Extract negative knowledge explicitly.

A `REJECT` can be high value when it reveals:

- a source pattern optimized for a different business model;
- architecture that only makes sense at another scale/team topology;
- expensive operational machinery with little target value;
- a feature that duplicates a sufficient target capability;
- a parity feature that weakens differentiation;
- a pattern dependent on proprietary data/network effects;
- a visually attractive flow that creates trust/accessibility/support debt.

Do not hide these under "risks". Put material false friends in the portfolio.

## 6. Interaction graph

For top patterns record only material relationships:

- `requires` - cannot work without another capability/prerequisite;
- `enables` - makes another pattern materially cheaper or more useful;
- `conflicts_with` - creates incompatible behavior/architecture;
- `substitutes_for` - two patterns solve the same problem differently;
- `bundles_with` - value depends on shipping together.

Do not convert this into a full roadmap. Use it to prevent independent ranking errors and hand the graph downstream.

## 7. Prioritization principles

Prefer `ADOPT` when:

- target problem is evidenced;
- source mechanism is sufficiently established;
- existing target capability is insufficient;
- target constraints support the transfer;
- no mandatory blocker exists;
- complexity/opportunity cost is justified.

Prefer `EXPERIMENT` when expected value is meaningful and uncertainty is cheap to resolve.

Prefer `CANDIDATE` when source lesson is useful but target evidence is missing.

Prefer `BACKLOG` when useful but poorly timed or dependency-bound.

Prefer `REJECT` when target problem/mechanism fit is weak or tradeoffs dominate.

Use `REVIEW_REQUIRED` for unresolved mandatory legal/IP/security/privacy constraints.

## 8. Common transfer traps

- **Surface-copy trap** - imitate layout/feature while missing mechanism.
- **Scale mismatch** - source assumes traffic/data/team size target lacks.
- **Business-model mismatch** - source optimizes another revenue/value system.
- **Architecture transplant** - copy boundaries optimized for another runtime/team topology.
- **Parity treadmill** - perpetual catch-up weakens differentiation.
- **Success attribution error** - successful company implies every pattern is successful.
- **Prevalence fallacy** - many products use it, therefore it works.
- **Maintenance blindness** - underprice migrations/support/observability/dependencies.
- **Measurement blindness** - no baseline or success rule.
- **License blindness** - accessible code/assets assumed reusable.
- **Destination amnesia** - source evidence replaces target problem evidence.
