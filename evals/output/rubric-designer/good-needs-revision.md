# Rubric — customer release notes (revision 1)

## Status

- Status: NEEDS_REVISION
- Mode: STANDARD, candidate-blind: yes, frozen before review: no
- Reason: the rubric is valid but not frozen; AG-01 must be settled with the requester before the freeze.

## Rubric identity

- Rubric ID: `rubric-release-notes`
- Revision: 1
- Rubric hash (sha256): 43a348146c4001eb47ee8389a70ad9a00c187db642dea7a1380b92cc0265f0b5 (the hash stays the same when the draft is frozen unchanged)

## Criterion coverage

| ID | Dimension | Pass condition | Fail condition | Floor | Materiality | Blocker |
| --- | --- | --- | --- | --- | --- | --- |
| RC-01 | accuracy | Each entry links a merged change request in the stated release | An entry has no link or links an unmerged change request | A | critical | yes |
| RC-02 | clarity | Each entry states what a customer will notice | An entry describes only internal implementation | C | material | no |

## Blocker criteria

- RC-01 — floor A, critical. One unlinked entry fails the notes.

## Missing dimensions

- none (accuracy and clarity both have a criterion)

## Anti-gaming findings

- AG-01 — open: RC-02 has floor C while its materiality is material; a reviewer's paraphrase would satisfy it. Raise the floor to B or lower the materiality before freezing.

## Next owner

The requester decides AG-01; then this skill freezes revision 2 with a new hash.

```json
{
  "rubric_id": "rubric-release-notes",
  "revision": "1",
  "purpose": "Grade release notes for customer readability",
  "target_type": "release notes",
  "mode": "STANDARD",
  "candidate_blind": true,
  "frozen_before_review": false,
  "required_dimensions": ["accuracy", "clarity"],
  "criteria": [
    {"id": "RC-01", "dimension": "accuracy", "description": "Every change maps to a merged change request", "observable": true, "pass_condition": "Each entry links a merged change request in the stated release", "fail_condition": "An entry has no link or links an unmerged change request", "evidence_floor": "A", "materiality": "critical", "blocker": true},
    {"id": "RC-02", "dimension": "clarity", "description": "Customer impact stated", "observable": true, "pass_condition": "Each entry states what a customer will notice", "fail_condition": "An entry describes only internal implementation", "evidence_floor": "C", "materiality": "material", "blocker": false}
  ],
  "anti_gaming": {"no_hidden_criteria": true, "no_post_hoc_changes": true}
}
```
