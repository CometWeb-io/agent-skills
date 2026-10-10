# Output contract

A bounded program state, not publication authorization. The validator checks
reported evidence references; it cannot grant ethics, sponsor or author approval.

Required root fields: non-empty `summary`, `status` (`complete`, `partial`,
`blocked`), `not_verified` (non-empty string entries), `program`, and
`research_handoff`. A complete result cannot contain `not_verified` items.

`program` requires non-empty `question`, ISO `as_of` (date or timezone-aware
timestamp), `stage`, non-empty `studies`, and lists `hypotheses`, `gates`,
`next_studies`, `governance`, `unknowns`. Stages: `question`, `protocol`,
`execution`, `analysis`, `manuscript`, `closed`.

Each study has unique `id`, non-empty `name`, `status`, `estimand`.
`studies.status` is `planned`, `reported`, `executed`, or `failed`.
An estimand cannot be the sentinel unknown, not reported, or TBD.
Complete programs require reported/executed studies with non-empty `evidence`
locators. Negative results remain valid evidence; failures and incomplete
inference stay partial or blocked.

`hypotheses`, `governance`, and `unknowns` contain non-empty strings.
Each `next_studies` object contains non-empty `id`, `estimand`, `falsifier`,
`evidence_requirement`, `stop_rule`, `continue_rule`, and a `dependencies` list
referencing existing studies. Empty objects or prose-only next studies fail.

Each gate has `id` and `gates.status`: `READY`, `BLOCKED`, `UNKNOWN`,
`NOT_REPORTED`. READY gates require non-empty `evidence` locators.
Complete programs require non-empty READY gates and empty `governance` and
`unknowns`; unresolved requirements cannot be hidden by a summary status.

`research_handoff` requires `status` from the gate vocabulary and `target`:
`next-study`, `science-roaster`, or `longform-publisher`. Its
`research_handoff.status` can be READY only for a valid complete program.
READY means prepared for that bounded next step. It never means authorized to
acquire data, submit, publish, contact participants, or approve a manuscript.
Those actions require external authorization and their own acceptance gates.

READY handoffs must match `program.stage`: `longform-publisher` requires
`manuscript` or `closed`; `science-roaster` accepts `protocol`, `execution`,
`analysis`, `manuscript`, or `closed`. `next-study` accepts any valid stage but
requires a non-empty, bounded `next_studies` plan. Non-READY handoffs can name
a later target while reporting the missing readiness evidence. Manuscript
programs may still propose a follow-up study; this grants no publication authority.
