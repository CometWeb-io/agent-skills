# Output contract

Return a repair ledger tied to the original finding IDs. This file is the one
schema for the ledger: `scripts/kernel.py` validates exactly these fields, and
`tooling/tests/test_contract_docs_match_kernels.py` fails if the two drift.
Five fields (`schema`, `base_candidate_id`, `protected_invariants`,
`regressions`, `remaining_open`) belong in the ledger for the reader; the kernel
does not check them.

```text
schema: cometweb.repair-ledger/v1
mode: STANDARD|DEEP                 # DEEP implies strict closure
strict_closure?: true|false         # strict closure without DEEP
portfolio_mode?: true|false         # requires the portfolio fields below
candidate_id                        # every closure evidence item must name it
base_candidate_id?
items[]:
  repair_id
  finding_ids[]                     # non-empty; one active repair per finding
  supersedes_repair_id?             # only way two repairs may share a finding
  repair_class: PATCH|REWRITE|REANALYSIS|REDESIGN|VERIFY_FIRST|ROLLBACK|WONT_FIX
  patch_risk: LOW|MEDIUM|HIGH|CRITICAL      # default LOW
  rollback_plan                     # required when patch_risk is HIGH or CRITICAL
  root_cause                        # required for CLOSED
  done_when                         # required for CLOSED
  depends_on[]                      # repair_ids in this ledger; no cycles
  protected_invariants[]
  protected_invariant_checks[]: {id, state: PASS}   # any non-PASS blocks CLOSED
  verification_plan: {method, checks[]}             # required for CLOSED when strict
  verification_evidence[]: {fresh: true, result: PASS, method, evidence[],
                            candidate_id, observed_at}   # timezone-aware ISO time
  regression_detected: true|false   # true blocks CLOSED
  status: OPEN|PLANNED|IN_PROGRESS|UNVERIFIED|CLOSED|DEFERRED|WONT_FIX|REOPENED
  reopen_of                         # required for REOPENED: an existing repair_id re-opened
  defer_reason                      # required for DEFERRED
  decision_source: {owner, rationale, decided_at, expires_at}
                                    # required for WONT_FIX; expires_at only when strict
  # portfolio_mode only:
  effort_band: XS|S|M|L|XL
  blast_radius: LOCAL|SECTION|CROSS_ARTIFACT|SYSTEM
  reversibility: EASY|MODERATE|HARD|IRREVERSIBLE
  explicit_approval_required: true  # required when reversibility is IRREVERSIBLE
regressions[]
remaining_open[]
```

Closure rules:

- `CLOSED` needs `root_cause`, `done_when`, and non-empty verification evidence
  that is fresh, `PASS`, and bound to `candidate_id`. `VERIFY_FIRST` and
  `WONT_FIX` items can never be `CLOSED`.
- `WONT_FIX` status needs `repair_class: WONT_FIX` and an authorized
  `decision_source`; never infer it.
- `DEFERRED` needs a concrete `defer_reason`.

Lead with blocking OPEN/UNVERIFIED work, then proven closures. Never use "fixed"
for an item whose fresh candidate-bound verification did not run.

To check a ledger, save it as JSON and run `python3 scripts/kernel.py ledger.json`
(or pipe it on stdin). It prints `{status: VALID|INVALID, errors[], closed,
open, strict_closure, portfolio_mode, effort_units}` and exits non-zero when the
ledger is invalid. Every result carries all seven keys, including a ledger that
is not an object (`payload:not-object`) or has no `items` list (`items:not-list`). A `mode` other than `STANDARD` or `DEEP` is an error
(`mode:invalid`), not a silent fallback to standard closure.

The field list above is also declared in `references/contract.json`, which
`tooling/skill_contracts.py` checks against the kernel, this file and the eval
cases.
