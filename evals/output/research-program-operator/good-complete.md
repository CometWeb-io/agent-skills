# Research program — activation study

## Program status

- Status: COMPLETE
- Program ID: `program-activation-2026`

## Program contract

- Question: What is the activation effect of the intervention?
- as_of: 2026-10-05
- Stage: manuscript

## Studies

| ID | Name | Status | Estimand |
| --- | --- | --- | --- |
| S1 | Pilot | reported | activation effect |

Estimand: activation effect.

## Stage gates

- G1 — READY: analysis has a declared estimand and falsifier.

## Next studies

- No next study is authorized until the analysis gate is reviewed.

## Governance and unknowns

- Ethics: no ethics gate applies to this synthetic fixture; no real participants.
- Authorship: fixture maintainer only.
- Unknowns: none within the synthetic fixture scope.

## Research handoff

- Status: READY
- Target: longform-publisher
- Handoff: manuscript readiness is bounded to the synthetic fixture, not publication authorization.

```json
{
  "summary": "Reconciled the research program and bounded the next study.",
  "status": "complete",
  "not_verified": [],
  "program": {
    "question": "What should the program do after the pilot?",
    "as_of": "2026-10-05",
    "stage": "manuscript",
    "studies": [
      {
        "id": "S1",
        "name": "Pilot",
        "status": "reported",
        "estimand": "activation effect",
        "evidence": [
          "fixture:pilot-results"
        ]
      }
    ],
    "hypotheses": [
      "The intervention improves activation."
    ],
    "gates": [
      {
        "id": "G1",
        "status": "READY",
        "evidence": [
          "fixture:protocol-review"
        ]
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
    "governance": [],
    "unknowns": []
  },
  "research_handoff": {
    "status": "READY",
    "target": "longform-publisher"
  }
}
```
