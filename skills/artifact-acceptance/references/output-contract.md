# Output contract

This is the one schema for an acceptance payload and report:
`scripts/kernel.py` reads exactly these fields, and `references/contract.json`
(checked by `tooling/skill_contracts.py`) fails if the two drift. Six fields
(`schema`, `version_or_hash`, `base_candidate_id`, `brief_id`,
`stale_if_changed`, `next_skill`) belong in the report for the reader; the
kernel does not check them.

```text
schema: cometweb.artifact-acceptance/v1
mode?: STANDARD|DEEP|DELTA          # default STANDARD; any other value is DEFER mode:invalid
profile?: CUSTOM|GENERAL|EDITORIAL|RESEARCH|SALES|TECHNICAL_DOCS
                                    # default CUSTOM; a profile predeclares required gate_id values
candidate: {id, version_or_hash?}   # or a top-level candidate_id
base_candidate_id?
contract: {id, brief_id?}           # or a top-level contract_id
as_of?                              # timezone-aware ISO time; waivers expiring by then are expired
policy_lock?: {pack_id, revision, sha256, locked_before_evaluation: true}
expected_policy_hash?               # must equal policy_lock.sha256
minimum_gate_evidence_grade?: A|B|C|D
criteria_ids[]?                     # required in DEEP; then every id needs a traceability row
traceability[]?: {criterion_id, gate_id}   # one row per criterion-to-gate link
gates[]:
  gate_id                           # unique
  required: true|false
  state: PASS|FAIL|UNKNOWN|N/A
  evidence[]: {source, locator, candidate_id, observed_at, contract_id?}
                                    # required PASS: non-empty, same candidate and contract
  evidence_grade?: A|B|C|D          # required on a required PASS when a floor is set
  na_allowed?: true                 # required N/A needs it
  na_rationale?                     # required N/A needs it
findings[]?:
  severity: BLOCKER|MAJOR|MINOR|NOTE    # any other or missing value is DEFER finding[i]:severity
  open?: true|false                 # default true
  blocks_acceptance?: true|false    # default true; open blocking BLOCKER/MAJOR is NOT_READY
controls[]?:
  severity: MINOR|NOTE
  issue
  owner
  revisit_condition
  candidate_id?                     # when present, the evaluated candidate
  required_gate_bypass?             # true is always an error
  waiver?: true|false
  approver                          # approver, approved_at, expires_at: required for a
  approved_at                       # waiver, and for every control in DEEP
  expires_at
verdict: READY|READY_WITH_CONTROLS|NOT_READY|DEFER
stale_if_changed: true
next_skill
```

A waiver is a control with `waiver: true`; there is no separate waiver list.

Each required PASS carries candidate-bound evidence. In DEEP mode material criteria require traceability. Put failed/unknown required gates and blocking findings before the verdict explanation. `READY_WITH_CONTROLS` is not a softer way to ignore a failed required gate. `N/A` needs explicit contract allowance. The deterministic kernel proves rule conformance of supplied states, not substantive truth of the evidence itself.

`python3 scripts/run_evals.py` runs the bundled cases through `kernel.decide`,
which returns `{verdict, errors[], profile, mode}`; `profile` and `mode` are
present only on READY and READY_WITH_CONTROLS.
