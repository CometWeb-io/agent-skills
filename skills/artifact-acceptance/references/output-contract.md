# Output contract

```text
schema: cometweb.artifact-acceptance/v1
mode: STANDARD|DEEP|DELTA
profile: CUSTOM|GENERAL|EDITORIAL|RESEARCH|SALES|TECHNICAL_DOCS
candidate: {id, version_or_hash?}
base_candidate_id?
contract: {id, brief_id?}
as_of
criteria[]?
traceability[]?: {criterion_id, gate_ids[]}
gates[]
findings[]
controls[]
waivers[]
verdict: READY|READY_WITH_CONTROLS|NOT_READY|DEFER
stale_if_changed: true
next_skill
```

Each required PASS carries candidate-bound evidence. In DEEP mode material criteria require traceability. Put failed/unknown required gates and blocking findings before the verdict explanation. `READY_WITH_CONTROLS` is not a softer way to ignore a failed required gate. `N/A` needs explicit contract allowance. The deterministic kernel proves rule conformance of supplied states, not substantive truth of the evidence itself.
