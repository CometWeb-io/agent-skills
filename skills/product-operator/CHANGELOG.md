# Changelog

## [2.4.0] - 2026-10-03

### Changed

- Front door cut from 16.2 KB to 9.1 KB. All eight control-plane references
  were already read every run, so SKILL.md repeated them; it now keeps the run
  loop, kernel entry points, escalation, output budgets and hard boundaries.
  The operating contract moved to `modes.md`, the Product State Ledger to
  `state-model.md`, candidate generation and contract to `prioritization.md`,
  the stop rule and definition of done to `control-loop.md`, and sidecar
  validation to `output-contract.md`.
- `references/local-workflow.md` shipped but nothing pointed to it; SKILL.md
  now loads it when running the kernel or brief bridge on local files.
- The description sends customer support triage to customer-ops.
- `tests/front-door-rules.json` pins every hard boundary and moved rule.

### Fixed

- `operator_kernel.py plan` rejects a non-object `coverage` and a non-list `depends_on` with an input error (exit 2). A string `depends_on` such as `"AB"` was read letter by letter as dependencies `A` and `B`, and a number crashed with a traceback; `sequence` and `readiness` apply the same checks.
- `prepare_brief.py` treats `"coverage": null` as absent instead of crashing.
- `scripts/self_check.py` answers `--help` and rejects unknown arguments instead of ignoring them and running.
- `validate_report` accepted an action confidence of 1.5 or -0.5: it tested
  `clamp(confidence, 0, 1) < 0`, and clamping pulls both into range, so only a
  non-number failed. Out-of-range and non-finite values now fail.

### Evals

- 79 golden cases added (60 -> 139): two pin the input checks above, and a `validate_report` kind pins the exact
  error and warning lists against a valid base report changed one field at a
  time, covering actions, blockers, decisions, evidence freshness, lane caps,
  the 2.2-only blocker checks, mutations and state-item contradictions.
  `delta_fields` and `unwrap_kind` cover state transitions, volatile
  timestamps, scope changes and blocker resolution, and bare reports versus
  snapshots. Held guards: 71 of 187 -> 140 of 189.

## [2.3.2] - 2026-10-02

- The description had no exclusions. It now hands first-time whole-project
  baselines to repo-to-roadmap, release-candidate verdicts to
  release-readiness, and cross-product capacity allocation to
  portfolio-operator, the three skills whose requests it overlaps.
- `INSTALL.md` still introduced the package as a 1.2.0-rc.1 candidate; it now
  points at `VERSION`.

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
