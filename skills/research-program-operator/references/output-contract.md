# Output contract

A result is a research-program state and next-study handoff. The validator and
`evals/cases.json` pin the fields below.

| Field | Type | Meaning |
| --- | --- | --- |
| `summary` | non-empty string | What was done, in one or two sentences |
| `status` | `complete`, `partial` or `blocked` | How far the work got |
| `not_verified` | list of strings | What was not checked; empty only when nothing was left |

A `complete` result with a non-empty `not_verified` is contradictory and is
rejected.

`program` is required and contains `question`, `as_of`, `stage`, `studies`,
`hypotheses`, `gates`, `next_studies`, `governance`, and `unknowns`. Stages are
`question`, `protocol`, `execution`, `analysis`, `manuscript`, and `closed`.
Each study has `id`, `name`, `status`, and `estimand`; each gate has status
`planned`, `reported`, `executed`, or `failed`. Gate statuses are `READY`,
`BLOCKED`, `UNKNOWN`, or `NOT_REPORTED`.

`research_handoff` is required and contains a `status` from that same gate
vocabulary and a `target`. A complete result cannot hide unknowns, governance
requirements, unreported results, or missing evidence.

The output does **not** assert anything beyond what was checked. A consumer that
mistakes a heuristic for a verdict is the failure mode worth preventing here.
