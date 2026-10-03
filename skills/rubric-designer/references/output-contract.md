# Output contract

Return status, rubric identity/revision/hash, criterion coverage, blocker criteria, missing dimensions, anti-gaming findings, and next owner.

## Rubric payload

`scripts/kernel.py` validates a rubric with exactly these fields;
`references/contract.json` declares them and `tooling/skill_contracts.py` checks
the kernel, this file and `evals/cases.json` against it.

```text
rubric_id                           # non-empty
revision                            # non-empty; a material edit is a new revision
purpose                             # non-empty
target_type                         # non-empty: the artifact or task class graded
mode: LIGHT|STANDARD|DEEP           # default STANDARD
candidate_blind: true|false         # DEEP requires true
frozen_before_review: true|false    # DEEP requires true; false returns NEEDS_REVISION
required_dimensions[]               # unique non-empty strings; each needs a criterion
criteria[]:                         # non-empty
  id                                # unique non-empty
  dimension                         # non-empty
  description
  observable: true                  # anything else is an error
  pass_condition
  fail_condition                    # must differ from pass_condition (ignoring case and edge whitespace)
  evidence_floor: A|B|C|D
  materiality: critical|material|supporting
  blocker: true|false               # default false; a blocker needs critical or material, floor A or B
  weight?                           # number in [0, 1]; a blocker cannot weigh 0
anti_gaming: {no_hidden_criteria: true, no_post_hoc_changes: true}
```

A dimension declared out of scope before candidate review is left out of
`required_dimensions`; there is no separate out-of-scope field.

The kernel returns `{status, errors[], missing_dimensions[]}` (an empty
`missing_dimensions` for a payload that is not an object, `payload:not-object`) and, when the
rubric is valid, `rubric_hash`, `criteria_count`, `blocker_count` and `frozen`.
`status` is `READY_TO_FREEZE` (valid and `frozen_before_review: true`),
`NEEDS_REVISION` (valid, not yet frozen) or `INVALID`. `rubric_hash` is the
SHA-256 of the canonical JSON of `rubric_id`, `revision`, `purpose`,
`target_type`, `mode`, `required_dimensions`, `criteria` and `anti_gaming`;
`candidate_blind` and `frozen_before_review` are not hashed, so freezing a
draft keeps its hash. An omitted `mode` is hashed as `STANDARD`, its default,
so leaving the default implicit does not change the hash.
