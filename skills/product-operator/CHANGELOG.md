# Changelog

## [2.3.1] - 2026-09-25

- Hold actions with missing prerequisites, including downstream dependents;
  a missing dependency is not evidence of completed work.
- Exercise plan readiness, STOP/LATER exclusions, dependency cycles, immediate
  and next limits, malformed records, and snapshot integrity in golden evals.
- Preserve DECISION NOW in the report, snapshot and bilingual brief, including
  unresolved options and delegation. Preselected decisions fail validation.
- Accept the kernel's inferred action types without crashing the brief bridge;
  include missing prerequisites in the rendered diagnostics.

## [2.3.0] - 2026-09-18

### Changed

- The golden suite went from 14 cases to 27 because it asserted four of the
  twelve contradiction codes `reconcile_item` can raise. `STATUS_CONTRADICTION`
  -- shipped state with no implementation evidence, the only `critical` code in
  the file -- was among the eight nothing pinned: deleting the check left every
  case green. Each code now has a case, and every guard in `reconcile_item`
  fails the suite when removed.
- `run_evals.py` accepts `expect_absent` on a `reconcile_code` case. `expect`
  alone only proves a code fires; a guard whose removal swapped one code for
  another still passed. Two cases use it: an absent stage owes no evidence, and
  missing evidence is not the same finding as wrong authority.

### Fixed

- `evidence_freshness` clamped a negative age to zero, so an observation dated
  after `as_of` — a skewed clock or a fabricated record — was reported as
  `CURRENT`, making the least trustworthy timestamp read as the freshest
  evidence available. A future observation is now `UNKNOWN`, matching
  release-readiness, which already flags a future `as_of` as a release-identity
  gap. The CURRENT / NEAR_EXPIRY / STALE bands are unchanged.

## 2.2.0 - 2026-09-09

- Make `BLOCKER` goal-relative: a condition is a blocker only when it prevents the current goal or a current critical-path action.
- Add `blocks_current_goal`, `blocked_item`, and `why_blocking` to blocker evidence in protocol 2.2 sidecars.
- Route non-blocking future gates such as Paid Beta prerequisites to `LATER/WATCH`, not the current sprint's `BLOCKER`.
- Keep uncertain current-path failures in `VERIFY NOW` until failure is proven.
- Prevent pricing or legal gates for a future paid motion from blocking a currently approved free validation motion unless they directly affect that motion.
- Preserve validation compatibility for protocol 2.0/2.1 sidecars while emitting protocol 2.2.

## 2.1.0 - 2026-09-07

- Add `DECISION NOW` for unresolved consequential choices that Product Operator must frame and delegate rather than decide.
- Route `decision_required` candidates to `DECISION NOW`; `verify_first` still wins when facts/gates are missing.
- Add structured `decision_now[]` validation and reject sidecars that preselect/recommend an unresolved option.
- Separate compact Human brief from detailed Machine sidecar.
- Add response budgets and suppress non-decision-relevant connector/tool-limit noise.
- Add explicit Pricing / Offers / AI Council / legal-finance delegation rules, including free-vs-paid pilot handling.
- Preserve backward validation support for protocol 2.0 sidecars while emitting protocol 2.1 for new reports.
