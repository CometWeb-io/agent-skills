# Changelog

All notable changes to the **CometWeb Agent Skills** bundle are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/); repository
tags use `vMAJOR.MINOR.PATCH`.

## [Unreleased]

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

[2.0.0]: https://github.com/CometWeb-io/agent-skills/compare/v1.0.6...v2.0.0
[1.0.6]: https://github.com/CometWeb-io/agent-skills/compare/v1.0.5...v1.0.6
[1.0.5]: https://github.com/CometWeb-io/agent-skills/compare/v1.0.4...v1.0.5
[1.0.4]: https://github.com/CometWeb-io/agent-skills/compare/v1.0.3...v1.0.4
[1.0.3]: https://github.com/CometWeb-io/agent-skills/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/CometWeb-io/agent-skills/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/CometWeb-io/agent-skills/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/CometWeb-io/agent-skills/releases/tag/v1.0.0
