# Changelog

All notable changes to the **CometWeb Agent Skills** bundle are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/); repository
tags use `vMAJOR.MINOR.PATCH`.

## [Unreleased]

### Added

- Every host installer accepts `--dry-run` (run all checks, print the plan,
  write nothing) and `--uninstall` (remove only links into this checkout's
  `skills/`). All six hosts share one code path in `scripts/lib/install.sh`;
  rerunning an install prunes links to retired skills, and `install-all.sh`
  previews every host before changing any of them.
- `tooling/routing_coverage.py --check` reports positive and negative routing
  cases per skill, enforces a per-skill floor, and rejects duplicate IDs,
  near-identical prompts and prompts copied from registry examples.
  `evals/routing/known-gaps.json` records prompts the router still misroutes;
  a gap that starts passing fails the check until it is promoted to the suite.
- CW-AIP v1 and v2 conformance fixtures (valid and invalid) under
  `fixtures/cwaip-v{1,2}/conformance/`, run against the validators in the test
  suite. The multiagent envelope gate now accepts v2 envelopes.
- The README skill catalog is generated from `registry/skills.json` and
  `registry/readme-catalog.json` by `generate_adapters.py`, and repository
  Markdown links are checked by the test suite.
- `tooling/new_skill.py --root` scaffolds into another checkout.
- Public safety scanning flags personal email addresses (RFC 2606 domains and
  the project contact are allowed), any home-directory path with a real account
  name, signed JWTs, and Stripe, npm, PyPI, GitLab, Hugging Face, Slack app and
  Azure storage credentials.

- The router ignores routing signals inside a refused clause ("do not review
  the codebase, just fix the test", "nie rób przeglądu repo, tylko…"), in
  English and Polish. Scope ends at the clause, so "don't hold back: roast this
  repo" still routes. Rules live in `registry/routing-policy.json` under
  `negation`.
- `tooling/routing_coverage.py --confusion` reports misroutes and false
  positives over every labelled prompt in the repository, split into stable
  tune and holdout halves.
- Per-skill `tests/front-door-rules.json` inventories, checked by
  `tooling/tests/test_front_door_rules.py`: every must-keep rule has to stay in
  the file it is listed under, a rule moved to a reference needs a pointer with
  a load trigger in `SKILL.md`, and every normative sentence in a front door has
  to be inventoried. The three roasters, Product Operator, Release Readiness,
  Customer Ops, Product Teardown and Competitive Intelligence use it.
- Every bundled skill script answers `--help` with exit 0 and rejects unknown
  arguments; `tooling/tests/test_skill_script_cli_contract.py` checks all of
  them and that each script imports only the standard library, its siblings or
  dependencies declared in `RUNTIME.json`. A runtime-matrix workflow runs the
  skills that declare dependencies against those dependencies alone.
- Draft CW-AIP v2 schemas for the reserved `artifact`, `snapshot` and
  `specialist-handoff` kinds, with fixtures.
- Tests that the paths in `registry/hosts.json` exist and that an installer
  rerun over an older install upgrades it cleanly.

### Changed

- Broadened deterministic routing evaluation to 284 cases, including natural
  Polish requests and positive coverage for every catalog skill. The proxy is
  not a substitute for model or host-level routing acceptance.
- Roaster routing signals now pair adversarial verbs (roast, tear apart,
  red-team, stress-test, brutal critique, Polish `zroastuj`/`upiecz`/`rozjedź`)
  with each roaster's own objects. Deterministic-proxy recall on the skills'
  trigger evals rose from 5, 3 and 9 of 18 to 15, 16 and 15 of 18 for content-,
  repo- and science-roaster, with no new false positives; `routing_coverage.py
  --check` now enforces those floors, and a scope guard keeps live-UX roasts with
  web-app-auditor.
- The three roasters now verify all ten shared scripts and protocol references
  for byte-level drift, not only two scripts.
- Expanded Product Operator and Longform Publisher golden cases around evidence
  freshness, readiness, derived-artifact lineage, and manuscript placeholders.
- CI now extracts every skill ZIP and executes available offline eval/smoke
  entrypoints outside the checkout, including positive and negative multiagent
  validator checks. Local validation also gates all shared roaster resources.
- Package attestation now requires the full local gate, tree/history safety
  scans and extracted-package helper checks before building release artifacts.

- Skill descriptions for evidence-researcher, longform-publisher,
  competitive-intelligence, design-partner-finder, ebook-publisher,
  product-operator, release-readiness, science-roaster and web-app-auditor are
  host-neutral, state when not to use the skill, and no longer route to
  packages this catalog does not ship. Customer Ops replaces its restated
  per-mode procedures with one table that points at the existing references.
- Unit tests run in parallel (`pytest -n auto`). Workflow permissions are scoped
  to the job that needs them, third-party actions are pinned by commit, and
  matrix values reach shell steps through environment variables.

- Routing signals for 18 skills are narrower: bare nouns such as "ebook",
  "canonical", "blocker" or "orchestrate" no longer claim a prompt without the
  skill's verb or object, so a file conversion, a single canonical-tag edit or
  a Docker compose request reaches no skill. `parse_description` reads
  `SKILL.md` with a YAML parser, as hosts do.
- The roaster front doors (6.1.0) are 35–42% smaller; the step procedure moved
  to `references/workflow.md` per roaster and review setup to a shared
  `references/review-operations.md`. Product Operator 2.4.0, Release Readiness
  1.3.0, Customer Ops 2.2.0, Product Teardown 1.2.0 and Competitive Intelligence
  1.1.0 moved detail behind their front doors the same way.
- `tooling/eval_strength.py` finds guards the AST way and measures 888 guards
  (was 359); 765 are held by the skills' own harnesses after new eval cases
  for benchmark-curator, content-writer, feedback-integrator, rubric-designer,
  product-operator and longform-publisher.
- The multiagent CW-AIP gate checks v1 envelopes against their kind schemas,
  requires a v1 payload, and rejects a `GO`/`GO_WITH_CONTROLS` verdict that
  lists blockers. CW-AIP spec revisions 1.0.1 and 2.0.1.
- YAML frontmatter and host metadata are read with `yaml.safe_load` plus a
  duplicate-key pass; no `nosec` suppression remains.
- The OpenAI marketplace manifest declares its install policy and category.
- Ruff 0.16.10 and four development dependency patch updates.

### Fixed

- Product Operator's report validator accepted an action confidence outside
  0–1; its kernel rejects a non-object `coverage` and a string `depends_on`
  (which was read letter by letter as dependencies) instead of crashing.
- Release Readiness documented `commercial_model` while the engine read
  `scope.commercial`, so a paid release lost its billing gate; the engine now
  accepts the alias and rejects the two keys disagreeing.
- Longform Publisher reports a wrongly typed nested report field as
  `FIELD_TYPE_INVALID:<field>` instead of a traceback (frozen-release
  exception 1.1.2). `score_maxx.py` and `compare_scores.py` reject malformed
  score files with a message instead of a traceback, and Web App Auditor's
  `validate_report.py --help` works without `jsonschema`.
- Installers skip a skill directory that holds only `__pycache__` residue
  (what `git pull` leaves after a skill is retired) instead of failing, and a
  Cursor routing rule linked to the legacy `extras/cursor-routing.mdc` is
  re-pointed to the generated rule.
- Validators no longer pass malformed input: the coverage ledger rejects
  non-object rows, blank evidence references and unknown check IDs with a
  specific message; the decision validator rejects GO while human approval is
  required, pending or denied, and duplicate `gate_id` rows. Envelope and
  ledger CLIs print `FAIL:` with a reason instead of a traceback, and
  `validate_evidence_envelope.py` / `validate_decision_envelope.py --help`
  print usage instead of treating the flag as a file name.
- `doctor.py` reports skills that are missing from the registry, missing from
  disk or not installed instead of returning a clean result.
- The standard-library fallback in `tooling/validate_envelope.py` refuses
  schemas that use keywords it cannot enforce rather than ignoring them.
- `sync_skill_registry.py --apply` no longer reverts routing signals and
  descriptions that had been edited only in `registry/skills.json`; a test now
  requires the command to be a no-op on the committed registry.
- Per-skill `INSTALL.md` files named `scripts/package-releases.sh`, which does
  not exist; they now give the `tooling/package_skill.py` command, and a test
  checks that every repository path they name exists.
- The shared roaster handoff contract no longer cites a nonexistent
  `integration/validate_handoff.py`.
- Behavior evals and the orchestrator drift-guard tests no longer depend on the
  contributor's git configuration or mutate the checkout while other tests read
  it. The blind eval report carries a fixture fingerprint that ignores the run
  timestamp.

- Install targets that contain a `..` path component are rejected in the shared
  helper, including `CURSOR_RULES_DIR`. Absolute directories without `..` still
  install.
- A near-tie between incompatible specialists returns `ambiguous` instead of
  silently picking one skill. `use <skill-id>` counts as an explicit invoke.
- Product Operator's install note uses `~/.codex/skills`, the same Codex path
  as the root installer.
- Host installers reject conflicting directories, files, and foreign symlinks
  by default before linking any skill. With `SKILLS_REPLACE_CONFLICTS=1`,
  conflicting entries are moved to a dated backup and canonical links are
  recreated idempotently across supported hosts.
- Installers reject incomplete skill packages before changing any host target.
- The multiagent envelope validator bundles its schema and fails closed when
  the schema or `jsonschema` is missing; its alias dependency is explicit.
- The canonical orchestrator ZIP no longer contains an unresolved
  repository-only documentation link.
- Installers reject targets overlapping their source skill tree, including
  symlink aliases, before moving a package. The multiagent install guide now
  states its sibling-skill and Python dependency requirements.
- Product Operator golden evals now pin snapshot hash and state fingerprint
  tampering. Skill Auditor routing covers additional Polish paraphrases with
  adjacent negative controls.
- Product Operator no longer promotes actions whose prerequisites are missing;
  its golden suite now covers 60 cases, including dependency chains, cycles,
  STOP/LATER exclusions, plan caps, and malformed candidate records.
- Product Operator 2.3.1 preserves DECISION NOW through report generation and
  bilingual rendering; inferred action types no longer crash the brief bridge.

## [2.0.1] - 2026-09-22

### Added

- Integrated the quality workflow package set: artifact acceptance, briefing,
  content writing/review, repair, benchmark and rubric design, feedback
  integration, quality-loop operations, skill auditing, and skill evaluation.
- Added dedicated `content-roaster`, `science-roaster`, and `repo-roaster`
  packages from Roaster Suite 6.0.0, with the quality bundle's duplicate copies
  intentionally excluded so each skill ID has one canonical version.
- Expanded the canonical marketplace bundle from 18 to 32 skills and refreshed
  registry metadata, host adapters, routing docs, package manifests, and context
  budget baselines.

### Verification

- The imported packages retain their own references, deterministic helpers,
  eval fixtures, and tests; the source bundles' root CI and release tooling are
  not copied into this repository.
- Static package integrity, public-tree safety, registry consistency, and the
  full local validation suite remain release gates; static checks do not claim
  live-host behavioral lift.

## [2.0.0] - 2026-09-19

### Added

- `ebook-publisher`, `longform-publisher`, `portfolio-operator`, and
  `cometweb-context`, bringing the canonical bundle to 18 skills.
- Cross-runtime installation and generated adapters for Cursor, Claude Code,
  Codex, Qwen, Qoder, and Lingma.
- CW-AIP v2 schemas and validators for evidence, decisions, releases, reviews,
  and multi-skill handoffs, while retaining the documented v1 compatibility
  surface.
- Approval-gated deterministic skill packages, reviewer bundles, public-tree
  safety scanning, and history scanning with no bypass flag.
- A 12-gate local validator covering repository integrity, generated adapters,
  routing, behavior, context budgets, eval strength, security, compilation, and
  the full test suite.
- Context-budget baselines that fail on unreviewed front-door growth without
  pretending there is one universal token ceiling.
- Mutation-style eval-strength baselines that measure whether each deterministic
  rule is actually held by a failing case rather than counting green examples.
- `tooling/new_skill.py`, package-layout contracts, registry consistency checks,
  executable-bit checks, documentation indexes, issue forms, contributor and
  security policies.
- A deterministic `tooling/whykit_draft.py` boundary that validates finalized
  CW-AIP v2 evidence and decision envelopes and emits explicit, unreviewed
  WhyKit drafts without mutating a vault or allocating ledger IDs.

### Changed

- `CometWeb-io/agent-skills` is the single public canonical source. The former
  private-source/public-mirror workflow and its sync tooling are retired.
- Tracked context bindings use public placeholders; local paths belong only in
  ignored `*.local.json` and `*.local.txt` overlays.
- `registry/skills.json` remains the metadata source of truth; marketplace
  manifests, host adapters, compatibility tables, and generated documentation
  are checked against it.
- Large skill front doors were deduplicated against their own references while
  preserving binding safety rules and execution order.
- CI remains one Python 3.12 validation job. The duplicate PR-only workflow and
  recurring dependency bots are removed to avoid repeated runner cost.
- GitHub Actions are pinned to reviewed commit SHAs; full history safety remains
  a local pre-release gate rather than an every-push workflow.

### Fixed

- Local validation now passes under the declared pytest import mode; shared test
  fixtures no longer depend on importing sibling test modules.
- Routing metadata and examples no longer send long-form publishing work to
  release readiness or point the orchestrator at a script in another package.
- Context scoring and freshness defaults use UTC rather than the runner's local
  timezone, and Council recency no longer uses naive UTC datetimes.
- All documented contributor commands now map to tools that actually exist.
- Qwen, Qoder, and Lingma installers retain executable file modes in Git.
- The Codex installer no longer deletes an existing real skill directory; all
  host installers fail safely until the user moves a collision aside.
- Missing package icons, dead readiness locals, incomplete exception chaining,
  and low-visibility subprocess coverage were corrected.
- Package case-collision checks run on case-insensitive macOS filesystems instead
  of skipping the risk they exist to detect.
- The retired `ai-antipattern-writing` package cannot reappear through registry,
  adapter, or legacy-package synchronization.
- CW-AIP v2 validation remains complete without the optional `jsonschema`
  package, loads typed validators without module-name collisions, and rejects
  ambiguous JSON before rendering a WhyKit draft.
- WhyKit draft output treats producer prose as inert data, preserves decision
  approval metadata in provenance, and refuses to overwrite existing files.

### Verification

- The full deterministic test suite passes with zero failures, errors, or skips.
- All 12 local validation gates pass.
- Current-tree and full-history public-safety scans pass.
- Deterministic routing, package, adapter, context-budget, and eval-strength
  checks are part of the release candidate.

## [1.0.6] - 2026-08-26

### Added

- Envelope validator for multiagent handoffs (`validate_envelope.py`).
- Multiagent smoke walkthrough and demo Evidence Pack.

### Changed

- Multiagent documentation now covers cloud subagents and step validation.

## [1.0.5] - 2026-08-26

### Added

- `scripts/install-codex.sh` installs all skills into Codex.

## [1.0.4] - 2026-08-26

### Added

- `skill-orchestrator-multiagent` for isolated specialist execution.

### Changed

- Routing distinguishes single-thread and multiagent orchestration.

## [1.0.3] - 2026-08-26

### Added

- `skill-orchestrator` for multi-skill CW-AIP workflows.

## [1.0.2] - 2026-08-26

### Added

- `scripts/install-claude.sh` installs all skills into Claude Code.

### Changed

- Installation and architecture documentation covers Cursor, Claude Code, and
  ChatGPT-compatible hosts.

## [1.0.1] - 2026-08-26

### Added

- Branded demo, root installation guide, issue/PR templates, and release-bundle
  support files.

## [1.0.0] - 2026-08-25

### Added

- Twelve public skills with deterministic kernels and CI.
- CW-AIP v1 interchange protocol and JSON Schemas.
- Routing evaluation suite, validators, installers, safety checks, and release
  packages.

[2.0.1]: https://github.com/CometWeb-io/agent-skills/compare/v2.0.0...v2.0.1
[2.0.0]: https://github.com/CometWeb-io/agent-skills/compare/v1.0.6...v2.0.0
[1.0.6]: https://github.com/CometWeb-io/agent-skills/compare/v1.0.5...v1.0.6
[1.0.5]: https://github.com/CometWeb-io/agent-skills/compare/v1.0.4...v1.0.5
[1.0.4]: https://github.com/CometWeb-io/agent-skills/compare/v1.0.3...v1.0.4
[1.0.3]: https://github.com/CometWeb-io/agent-skills/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/CometWeb-io/agent-skills/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/CometWeb-io/agent-skills/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/CometWeb-io/agent-skills/releases/tag/v1.0.0
