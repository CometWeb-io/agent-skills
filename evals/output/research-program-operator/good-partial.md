# Research program — activation study

## Program status

- Status: PARTIAL
- Program ID: `program-activation-2026`

## Program contract

- Question: What is the activation effect of the intervention?
- as_of: 2026-10-05
- Stage: protocol

## Studies

| ID | Name | Status | Estimand |
| --- | --- | --- | --- |
| S1 | Pilot | planned | activation effect |

Estimand: activation effect.

## Stage gates

- G1 — UNKNOWN: protocol approval and preregistration are not reported.

## Next studies

- Define sample and falsifier before execution.

## Governance and unknowns

- Governance: ethics status not reported.
- Unknowns: sample feasibility and external validity.

## Research handoff

- Status: BLOCKED
- Target: evidence-researcher
- Handoff: verify the protocol evidence before execution.

```json
{
  "summary": "Reconciled the research program and bounded the next study.",
  "status": "partial",
  "not_verified": [],
  "program": {
    "question": "What should the program do after the pilot?",
    "as_of": "2026-10-05",
    "stage": "analysis",
    "studies": [
      {
        "id": "S1",
        "name": "Pilot",
        "status": "reported",
        "estimand": "activation effect"
      }
    ],
    "hypotheses": [
      "The intervention improves activation."
    ],
    "gates": [
      {
        "id": "G1",
        "status": "UNKNOWN"
      }
    ],
    "next_studies": [
      {
        "id": "S2",
        "estimand": "activation effect",
        "falsifier": "effect is nonpositive",
        "dependencies": [
          "S1"
        ],
        "evidence_requirement": "powered follow-up observations",
        "stop_rule": "stop at preregistered sample size",
        "continue_rule": "continue after ethics approval"
      }
    ],
    "governance": [
      "Ethics review is not reported."
    ],
    "unknowns": [
      "Long-term effect is unknown."
    ]
  },
  "research_handoff": {
    "status": "UNKNOWN",
    "target": "longform-publisher"
  }
}
```
