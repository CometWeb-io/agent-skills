# Changelog

All notable changes to the **CometWeb Agent Skills** bundle (public repo).

Format follows [Keep a Changelog](https://keepachangelog.com/). Version tags: `vMAJOR.MINOR.PATCH`.

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

[1.0.2]: https://github.com/MaciejZet/agent-skills/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/MaciejZet/agent-skills/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/MaciejZet/agent-skills/releases/tag/v1.0.0
