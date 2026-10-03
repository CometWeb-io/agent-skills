# Content review — "Exporting reports to CSV" (doc-csv-export@r5)

## Review status

- Review status: REVIEWED
- Mode: STANDARD
- Candidate: `doc-csv-export@r5` against brief `brief-csv-export` v1
- Summary: no BLOCKER or MAJOR finding; two small improvements below. This is a review, not an acceptance verdict.

## Findings

### CR-004 — MINOR — The delimiter setting is named two ways

- Axis: consistency
- Finding status: CARRIED
- Revalidated: yes, against r5 (the second name still appears in step 6)
- Locator: steps 2 and 6
- Observation: step 2 says "separator", step 6 says "delimiter" for the same field.
- Evidence: OBSERVATION — doc r5, steps 2 and 6.
- Repair direction: use the UI label "Delimiter" in both places.
- Blocks acceptance: no

### CR-005 — NOTE — A worked example would help first-time readers

- Axis: actionability
- Finding status: NEW
- Locator: end of section "Choosing columns"
- Observation: the section lists options but shows no exported row.
- Evidence: OBSERVATION — doc r5, section "Choosing columns".
- Repair direction: add one example row from the sample workspace at example.com/demo.
- Blocks acceptance: no

## Verify

- none

## Handoff

- Recommended next skill: `content-writer` for the two optional edits; `artifact-acceptance` if the owner wants a release gate.

```json
{
  "schema": "cometweb.content-review/v1",
  "mode": "STANDARD",
  "candidate_id": "doc-csv-export@r5",
  "base_candidate_id": "doc-csv-export@r4",
  "status": "REVIEWED",
  "findings": [
    {"finding_id": "CR-004", "finding_status": "CARRIED", "revalidated": true, "axis": "consistency", "severity": "MINOR",
     "locator": "steps 2 and 6", "observation": "Two names for the delimiter field",
     "evidence": [{"kind": "OBSERVATION", "source": "doc r5", "locator": "steps 2 and 6", "candidate_id": "doc-csv-export@r5"}],
     "repair_direction": "Use the UI label in both places", "style_preference": false, "brief_violation": false, "blocks_acceptance": false},
    {"finding_id": "CR-005", "finding_status": "NEW", "axis": "actionability", "severity": "NOTE",
     "locator": "section Choosing columns", "observation": "No exported example row",
     "evidence": [{"kind": "OBSERVATION", "source": "doc r5", "locator": "section Choosing columns", "candidate_id": "doc-csv-export@r5"}],
     "repair_direction": "Add one example row", "style_preference": false, "brief_violation": false, "blocks_acceptance": false}
  ],
  "verify": [],
  "recommended_next_skill": "content-writer"
}
```
