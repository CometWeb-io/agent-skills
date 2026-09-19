# Changelog

All notable changes to the **CometWeb Agent Skills** bundle (public repo).

Format follows [Keep a Changelog](https://keepachangelog.com/). Version tags: `vMAJOR.MINOR.PATCH`.

## [Unreleased]

### Added — context as a measured resource

- `tooling/context_budget.py` measures what a host pays to have each skill
  available: SKILL.md as the front door, references/ as depth, and a `deferred`
  ratio showing how much of a skill is held behind that door. Nothing in the
  repository measured this before, while correctness was gated ten ways — and
  context is the resource that decides whether a skill can be loaded at all.
  Loading all eighteen front doors costs roughly 56,000 estimated tokens.
- The gate is on growth, not an absolute ceiling. `registry/context-baseline.json`
  records today's cost; a front door that grows more than 10% fails until the
  new cost is accepted with `--update`. No token ceiling is asserted, because the
  right one depends on the host and this repository does not claim numbers it
  cannot evidence.
- Wired into `validate_local` (now eleven checks) and CI, with
  `docs/generated-context-budget.md` regenerated like the other generated tables.
- `tooling/new_skill.py` scaffolds a package that satisfies the shared surface,
  carries the icon the adapters need, and ships an eval harness that fails until
  an assertion exists. It does not write the registry; `sync_skill_registry.py`
  and `generate_adapters.py` own that.

### Added — what a test suite is worth

- A green suite is worth what it would fail on, and nothing here measured that.
  Inverting the priority-score comparator in `portfolio_kernel` left all ten of
  its golden cases passing, because every ranking case was decided by the gate
  order before the score was ever consulted. Counting cases cannot show that;
  removing one branch at a time and checking whether a case goes red can.
- `tooling/eval_strength.py` does exactly that. It copies each package to a
  temporary directory, replaces one `if` guard at a time with `if False:`, and
  runs that package's own harness against the copy — the working tree is never
  edited, so an interrupted run cannot leave a broken kernel behind.
  `registry/eval-strength.json` records today's floor; held counts may rise
  freely, and a fall fails the gate. The measurement takes about nine seconds.
- The first reading was blunt. `portfolio-operator` held 10 of 61 reachable
  branches: the urgency ladder, five of six lanes, five of seven specialist
  routes and nine rules in `validate_report` — the depth ceiling among them —
  could all be deleted with every case still green. `product-operator` asserted
  four of the twelve contradiction codes `reconcile_item` raises, missing
  `STATUS_CONTRADICTION`, the only `critical` one. Cases went 11 → 70 and
  14 → 27; held branches went 10 → 55 of 61 and 4 → 27 of 107.
- `portfolio-operator`'s harness gains a `render` case kind. `render_human_brief`
  produces what the user actually reads and no case touched it, so the rule that
  `portfolio_outcome` replaces internal `action` text in the brief — stated in
  SKILL.md and enforced nowhere — is now pinned.
- `product-operator`'s harness accepts `expect_absent` on a `reconcile_code`
  case. `expect` alone only proves a code fires; a guard whose removal swapped
  one code for another still passed.
- Six branches in `portfolio_kernel` remain unheld and no case was written for
  them, because none is observable: three return the same value either way, and
  two mask each other through a boolean verdict. They are listed in the table
  rather than explained away, and the gate counts them honestly.
- `product-operator` ships `prepare_brief.py` and `self_check.py`, which its
  harness never loads. The eval-strength table names them rather than folding
  them into a worse percentage.
- Eval data that nothing reads is now a test failure.
  `tooling/tests/test_eval_data_is_read.py` covers the four files that ship
  without a `scripts/run_evals.py`; each has to name the gated test that reads
  it. Two named nothing. `competitive-intelligence` and `design-partner-finder`
  ship behavioural suites that had drifted to different shapes — one spelled the
  expectation key `expect`, the other `expected` — and a grader written against
  one would have found no expectations in the other and reported every case as
  passing. Normalised, with `tooling/tests/test_model_eval_suites.py` holding the
  shape.
- Local gates: 11 → 12. Tests: 2204 → 2242.

### Changed — the measurement's first use

- `design-partner-finder` 1.1.0 and `portfolio-operator` 1.2.0 stopped paying
  twice for the same instructions. Both SKILL.md files restated checklists their
  own references already owned, in shorter and therefore lossier form: the
  partner-charter list was twelve bullets against a reference with fuller
  roles/commitments/stop-criteria/legal sections, and the portfolio gate order
  appeared identically in SKILL.md and `prioritization.md` — two places to drift.
  The steps now keep the spine: what the step decides, which reference and script
  it uses, and the prohibitions that must hold even when no reference is opened.
  Front doors drop 18,709 -> 15,496 and 14,046 -> 11,791 bytes. No rule was
  removed and no instruction moved into a reference; only the second copy went.
- `longform-publisher` has the same 0.54 deferral and was deliberately left
  alone. Its references total 11 KB across nine files, so the low ratio reports a
  thin depth layer, not a bloated front door — at ~2,358 tokens it is already
  below the median. Pushing text into 1 KB reference files to move a number is
  the failure mode this metric could induce, not a fix.
- `tooling/tests/test_authoritative_skill_sync.py` pins each authoritative
  release by literal version, so a legitimate ACTIVE bump fails the suite until
  the pin is edited. Updated for 1.2.0. The pin is doing real work for FROZEN
  releases, where a version change needs an acceptance record; for ACTIVE ones
  it is friction, and narrowing it is left as a decision rather than taken here.

### Fixed

- `tooling/validate_local.py`, the repo's own local gate, could never pass: it
  forced pytest's `importlib` import mode while `pytest.ini` declared `prepend`,
  and six test modules imported a sibling test module, which only resolves under
  `prepend`. Shared fixtures moved to `_tooling_fixtures.py` and
  `_context_fixtures.py`, no test module imports another, and the suite now
  passes under both import modes.
- Every command in `CONTRIBUTING.md` pointed at a file that does not exist —
  six of six, including one script with no counterpart anywhere in the repo.
  Rewritten against the tooling that is actually present.
- The case-collision packaging test skipped on any case-insensitive filesystem,
  which is the macOS default. It now injects the second spelling into the file
  walk and runs everywhere, so the suite has no skips and `validate_local`, which
  treats a skip as unproven coverage, can report `passed`.
- `council_kernel` used the deprecated naive `datetime.utcnow()` in its recency
  calculation — poor footing for a kernel whose subject is temporal correctness.
- Freshness and scoring defaulted "today" to the runner's local timezone, so the
  same input could score differently on two machines. Now explicitly UTC.
- Three dead locals in `evidence_kernel`, two of them readiness counters that
  were initialized and then never incremented or read.
- Exception chaining across nine files: CLI entry points suppress the traceback
  explicitly after printing their message, validators preserve the cause.
- A test read a comparison payload and discarded it; it now asserts the packet
  starts unreviewed.
- `skill-orchestrator` told an agent to build its subagent payload with
  `scripts/orchestrate_multiagent_kernel.py`, a path that does not exist in that
  package — the script ships with the multiagent skill.
- `ebook-publisher` and `longform-publisher` shipped without `assets/icon.svg`,
  so their generated host adapters carried no icon while the other sixteen did.
- Coverage reported the product-operator, longform-publisher and
  portfolio-operator kernels at 9-12%, low enough to read as untested. Their
  eval harnesses ran in a subprocess, invisible to coverage; run in-process they
  measure 61%, 63% and 56%.
- `scripts/install-all.sh` stopped at the fourth host with "Permission denied"
  on every fresh clone: the qwen, qoder and lingma installers were tracked in
  git as `100644`. README promises six hosts; three received skills.
- `longform-publisher`'s own second trigger example routed to
  `release-readiness`. Its signals never matched "report", although the skill's
  description claims reports, and the manuscript→DOCX/PDF path had no signal of
  its own. Both added; the 103 existing routing cases still pass and the example
  is pinned as case 104.

### Added

- `SECURITY.md`, `CODE_OF_CONDUCT.md`, issue forms and a pull request template
- Ruff, configured for defect rules rather than house style, run by CI and by
  `validate_local`, so the local gate and CI check the same things
- Package-layout, README-vs-registry and SKILL.md-reference tests, so the kinds
  of drift below become failures instead of things spotted by eye
- Registry self-consistency tests: every skill's published trigger examples must
  route to that skill and its negative examples must not; every routing regex
  must compile. Tracked shell scripts must carry the executable bit.
- `docs/README.md` indexes nine documents that almost nothing linked to, and
  marks which files are generated
- CI status, licence and skill-count badges
- A test that imports every skill script and forces the date-default branches,
  written after a missing import survived both a syntax check and the full
  suite because the branch containing it only runs when an optional argument is
  absent
- The existing Actions gate stays a single Python 3.12 job; generated-adapter
  validation remains fail-closed, and the full history leak scan stays a local
  pre-release check rather than running on every push and pull request

### Changed

- `pytest.ini` uses `importlib` import mode, so test basenames no longer have to
  be unique across skills

## [2.0.0] - 2026-09-14

### Changed

- This repository is now the single public canonical source; the former split
  between a private source tree and a public mirror is retired.
- Paths into private locations are placeholders in tracked files, supplied by
  untracked `*.local.json` / `*.local.txt` overlays read beside them.
- History was rewritten to remove those paths from every commit.

### Added

- `ebook-publisher`, `longform-publisher`, `portfolio-operator` and
  `cometweb-context` — 18 skills in total
- Cross-runtime host compatibility, installers and generated compatibility matrix
- Contract tracing, reviewer bundles, model/policy eval runners, routing and
  package policy registries
- Approval-gated publication with the `public_safety` scanner

### Fixed

- Provenance and conflict guards in `cometweb-context` that a merge had dropped
- Adapter YAML was written by string interpolation and could emit an
  unterminated scalar when a description was truncated mid-quote
- The leak gate allowlisted `source-registry.json`, which is where the real
  private paths were

## [1.0.6] - 2026-08-26

### Added

- Envelope validator for multiagent handoffs (`validate_envelope.py`)
- Multiagent smoke walkthrough and demo Evidence Pack (`docs/multiagent-smoke-example.md`, `docs/demo/smoke-step1-evidence.json`)

### Changed

- Multiagent docs: cloud subagent notes, step validation guidance

## [1.0.5] - 2026-08-26

### Added

- [`scripts/install-codex.sh`](scripts/install-codex.sh) — symlink all skills to `~/.codex/skills/` (replaces stale skill directories)

## [1.0.4] - 2026-08-26

### Added

- [`skills/skill-orchestrator-multiagent`](skills/skill-orchestrator-multiagent) — one subagent per specialist (Task API); `orchestrate_multiagent_kernel.py`

### Changed

- Routing rule distinguishes single-thread vs multiagent orchestrator
- `skill-orchestrator` cross-links multiagent variant

## [1.0.3] - 2026-08-26

### Added

- [`skills/skill-orchestrator`](skills/skill-orchestrator) — multi-skill workflow planning and CW-AIP sequencing (`orchestrate_kernel.py`, routing eval cases)

### Changed

- README and routing rule document orchestrator as single entry for evidence → Council and similar chains
- Install scripts install 13 skills

## [1.0.2] - 2026-08-26

### Added

- [`scripts/install-claude.sh`](scripts/install-claude.sh) — symlink all skills to `~/.claude/skills/` (Claude Code)

### Changed

- README: architecture diagram, evidence flow, per-skill roles, routing collision guide (roadmap-aligned)
- INSTALL, demo GIF, and skill INSTALL docs list Claude Code alongside Cursor and ChatGPT

## [1.0.1] - 2026-08-26

### Added

- Branded README demo GIF (`docs/demo/web-app-auditor-demo.gif`, 4 frames, ~42 KB)
- Root [`INSTALL.md`](INSTALL.md) and GitHub issue / PR templates
- Welcome thread in GitHub Discussions
- Release bundle includes `scripts/`, `INSTALL.md`, and demo artifacts

### Changed

- README landing: demo GIF, release badge, install quick path
- Demo generator: CometWeb colors, simplified layout, lighter GIF weight

## [1.0.0] - 2026-08-25

### Added

- Twelve public skills with deterministic kernels and CI
- CW-AIP v1 interchange protocol and JSON schemas
- Routing eval suite (66 cases), `validate_skills.py`, install scripts
- GitHub Actions CI: safety check, validation, routing evals, pytest
- GitHub Release v1.0.0 with per-skill and bundle ZIPs

[1.0.2]: https://github.com/CometWeb-io/agent-skills/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/CometWeb-io/agent-skills/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/CometWeb-io/agent-skills/releases/tag/v1.0.0
