# Changelog

## [1.2.0] - 2026-09-18

### Changed

- `SKILL.md` sections 3-7, 9 and 10 held second copies of the ledger schema,
  the `MUST DO` test, the capacity rules, the gate order, the human-brief
  template and the sidecar schema - all of which `portfolio-model.md`,
  `prioritization.md` and `output-contract.md` already define, in richer form.
  The gate order in section 7 and the one in `prioritization.md` were the same
  eight entries written twice, which is also two places to drift. The sections
  now point at the reference that owns each. The provenance gate and the
  depth-ceiling rule stay inline: they are what the skill must not violate even
  when it opens nothing. Front door drops from 14,046 to 11,791 bytes
  (~3,511 to ~2,947 tokens).
- The golden suite went from 11 cases to 70. Inverting the priority-score
  comparator in `rank_items` left all eleven passing, because the one ranking
  case was decided by the gate order before the score was ever consulted -- and
  the same held for the urgency ladder, five of six lanes in `classify_lane`,
  five of seven specialist routes, and nine of the rules in `validate_report`,
  including the whole depth ceiling. Ten of 61 reachable branches were held;
  55 are now.
- `run_evals.py` gains a `render` case kind. `render_human_brief` produces what
  the user actually reads and no case touched it, so the rule that
  `portfolio_outcome` replaces internal `action` text in the brief -- stated in
  SKILL.md and enforced nowhere -- is now pinned, together with omitted empty
  lanes and the `done_when`/`reason` fallback.

### Fixed

- `detect_capacity_conflicts` grouped by the raw deadline string, so two large
  hard commitments due the same calendar day were reported as no conflict when
  the dates were written differently — "2026-10-01" against
  "2026-10-01T00:00:00", or the same value with surrounding whitespace.
  Deadlines are now keyed by the day they name; an unparseable format keeps its
  stripped text so it still groups with itself. A one-day gap remains no
  conflict, as the rule states.

## 1.1.0 — 2026-09-10

- Added specialist depth ceiling so portfolio actions remain outcome-level and deep product/client/research work is delegated.
- Added provenance gate for exact user-facing dates, deadlines, numeric targets, counts, currency amounts, and time KPIs.
- Added delegation reality gate plus `DELEGATE CANDIDATE` for unconfirmed people/agents/systems.
- Expanded capacity-conflict detection to surface three or more substantial current-horizon hard commitments when exact capacity is unknown.
- Added v1.1 regression tests and golden eval cases.

## 1.0.0 — 2026-09-10

- Initial Portfolio Operator control plane for cross-domain 7/14/30-day allocation.
- Added evidence-aware commitment model, capacity honesty, focus-stream limits, and capacity-conflict surfacing.
- Added hard specialist boundaries for Product Operator, Skill Orchestrator, Release Readiness, Customer Ops, Evidence Researcher, and AI Council.
- Added deterministic kernel for ranking, conflict detection, validation, and human rendering.
- Added golden evals and regression tests for client/product/research trade-offs, future gates, delegation, and unknown capacity.
