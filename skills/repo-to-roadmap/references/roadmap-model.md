# Roadmap Model v2

## Item kinds

Use one primary kind:

- `BUILD`
- `FIX`
- `HARDEN`
- `VERIFY`
- `VALIDATE`
- `INSTRUMENT`
- `MIGRATE`
- `RETIRE`
- `DOCUMENT`
- `DECIDE`

Use `VERIFY` to establish technical truth and `VALIDATE` to establish product/business/outcome truth.

## Candidate schema

```json
{
  "id": "R-017",
  "title": "Prove tenant isolation on export flow",
  "kind": "VERIFY",
  "outcome": "Every export is authorized against the active tenant before data leaves the service",
  "problem_claim_refs": ["C-021"],
  "target_requirement_refs": ["T-009"],
  "why_now": "Client-ready tenant boundary is currently unverified",
  "acceptance_criteria": [
    {
      "criterion": "Cross-tenant export attempt is rejected",
      "verify_with": "integration test against production-equivalent authorization path",
      "proof": "passing CI artifact linked to the pinned ref"
    }
  ],
  "success_signal": "Tenant export boundary is directly verified",
  "depends_on": [],
  "effort": "S",
  "impact": 5,
  "urgency": 5,
  "risk_reduction": 5,
  "strategic_alignment": 5,
  "enablement": 4,
  "reach": 4,
  "uncertainty": 2,
  "evidence_confidence": 0.62,
  "mandatory_gate": "privacy",
  "gate_status": "UNVERIFIED",
  "gate_basis": "optional until resolved; when CLEAR/CLEAR_WITH_CONTROLS/BLOCK cite specialist/authority evidence or decision ref",
  "severity": "high",
  "non_goal": "Redesign all tenant administration UI"
}
```

## Acceptance criteria

Every criterion must be observable and include:

- `criterion` - what must become true,
- `verify_with` - how to test/inspect it,
- `proof` - what artifact/state will count as completion evidence.

Avoid "improve architecture", "clean up", "make robust", or "finish backend" without observable proof.

## Gates

Allowed mandatory gates:

- `release`
- `security`
- `privacy`
- `data_integrity`
- `legal`
- `core_flow`

Allowed gate statuses:

- `NOT_REQUIRED`
- `UNVERIFIED`
- `CLEAR`
- `CLEAR_WITH_CONTROLS`
- `BLOCK`

A numeric priority score cannot create or clear a gate.

- `BLOCK` -> `BLOCKER` lane.
- `UNVERIFIED` -> `VERIFY_NOW` lane when the gate is material to the target state.
- `CLEAR` / `CLEAR_WITH_CONTROLS` -> prioritize normally, while preserving controls.

For legal/security/privacy gates, use appropriate specialist/authority evidence where needed. Do not let a general repo review manufacture a definitive gate conclusion outside its competence.

## Target blockers outside gates

A non-gate item may be a `BLOCKER` only when:

- an explicit target requirement cannot be satisfied without it,
- evidence confidence is strong enough for the assertion,
- and the blocking path is stated.

Otherwise use `VERIFY_NOW`, `NOW`, or `VALIDATE` as appropriate.

## Priority dimensions

Score 0..5 as ordinal inputs:

- `impact`
- `urgency`
- `risk_reduction`
- `strategic_alignment`
- `enablement`
- `reach`
- `uncertainty` (5 = most uncertain)

The kernel score is a deterministic tie-breaker, not economic value. Gates, target requirements, and hard dependencies outrank it.

Run:

```bash
python scripts/roadmap_kernel.py priority --item-json '@item.json'
python scripts/roadmap_kernel.py sensitivity --item-json '@item.json'
```

If sensitivity is `FRAGILE`, do not overstate the exact lane/order. Identify the input/evidence that would change the decision.

## Effort bands

Use:

- `XS`
- `S`
- `M`
- `L`
- `XL`

Do not translate into days without team-specific capacity/velocity evidence.

An `XL` item should normally be decomposed before entering an execution wave. If it remains `XL`, add `decomposition_note` explaining why it must stay whole.

## Dependencies

Use `depends_on` only for hard prerequisites. Keep soft ordering in rationale, not the hard graph.

Hard dependency examples:

- schema migration before code that requires the new schema,
- auth boundary before exposing a paid endpoint,
- event contract before downstream consumer rollout.

Do not encode "would be nicer first" as a hard dependency.

The graph must have:

- unique IDs,
- no missing dependency IDs,
- no cycles.

Use graph leverage/critical-chain output to identify foundations that unblock several high-value outcomes. Do not let architecture leverage override a proven user/release blocker.

## Waves

Construct waves only after gate, evidence, and dependency validation.

Typical shape:

- Wave 0 - verify truth / clear binding blockers.
- Wave 1 - make target state safe and real.
- Wave 2 - complete the promised product outcome.
- Wave 3 - operationalize / scale / optimize only where evidence supports it.
- Later/Park - optional, speculative, duplicate, or dependency-blocked work.

Use outcome milestones, not invented dates, when capacity is unknown.

## Capacity

If the user supplies team capacity, deadlines, or velocity, use them as explicit constraints. Otherwise report parallelizable groups and hard ordering without fabricating a calendar.

## Root-cause clustering

Before creating many items, group symptoms that share a root cause. Prefer one enabling item when it resolves several verified gaps with one acceptance boundary. Split an item when components can ship independently or have different proof requirements.
