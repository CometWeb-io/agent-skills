# Output contract

Return an improvement backlog, not an autonomous self-modification log.

Input to `scripts/kernel.py` (`kernel.integrate`):

```text
records[]:
  pattern                           # records are grouped by this exact string
  severity?: NOTE|MINOR|MAJOR|BLOCKER       # default NOTE
  root_layer?: ROUTING|INSTRUCTION|REFERENCE|KERNEL|EVAL|HOST|PROCESS
  outcome?: CONFIRMED|FALSE_POSITIVE|RESOLVED|UNKNOWN   # default CONFIRMED
  observed_at?                      # timezone-aware ISO time; outside the window it retires
  context_id                        # independence counts distinct context_id values
  run_id
  systemic?: true                   # with BLOCKER severity and evidence, one context is enough
  evidence[]
  regression_test?: {id, assertion}
  test_gap?: {assertion, owner}     # one of regression_test or test_gap is required
  proposed_change?: {change, expected_effect, evaluation_plan}   # required under strict
min_count?                          # positive integer, default 2
as_of?                              # timezone-aware ISO time
window_days?                        # positive integer; needs as_of
strict?: true|false                 # default false
```

Output:

```text
status: NO_SIGNAL|WATCH|PROPOSED|RETIRED|INVALID
proposal_count
watch_count
retired_count
invalid_count
proposals[]: {pattern, independence_count, run_count, severity, root_layers[], root_layer,
              false_positive_count, resolved_count}
watch[]                             # same shape plus reason
retired[]                           # same shape plus reason, or {pattern, context_id, reason}
invalid[]: {index?, reason}
```

`reason` is one of `false-positive-dominant`, `resolved-no-current-recurrence`,
`root-cause-ambiguous`, `insufficient-independent-contexts`,
`regression-test-or-test-gap-required`,
`proposed-change-with-evaluation-plan-required` or `outside-learning-window`.
Champion/challenger promotion has its own payload; see
`references/champion-challenger.md`.

Each proposal preserves pattern, independence count, severity, root layer, causal hypothesis/evidence, affected skills, smallest reversible change, expected effect, blast radius, compatibility risk, and regression test or owned test gap. When a real failure is reproducible, preserve the minimized regression fixture and minimization trace; when a regression appeared across versions, preserve the stable comparison fingerprint and bisection boundary if one can be established.

Do not let stale or false-positive-dominant observations become policy. Do not put candidate-exposed minimized failures directly into a clean holdout. Separate `PROPOSED` from `IMPLEMENTED_UNVERIFIED` and `VERIFIED` in any persistent changelog.
