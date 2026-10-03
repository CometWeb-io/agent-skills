# Changelog


## [6.1.1] - 2026-10-03

- Declared the report contract in `references/contract.json` (`cometweb.skill-contract/v1`). Until now only the top level was written down: `references/output-contract.md` named the control-plane blocks, while `scripts/validate_review.py` checked about 180 keys at every nesting level and their value lists that no reference listed, so an agent building a report from the docs had to guess them. `references/output-contract.md` now carries a field reference with every key the validator reads and every value it accepts, plus the `scan_source_risks.py` output; `tooling/skill_contracts.py` checks it against the validator, `report.schema.json` and the new fixture `tests/report-valid.json`, which the unit tests now load instead of an inline copy.
- The validator binds each enum to one named constant: a value list shared by two fields gets an alias (`COVERAGE_CONFIDENCE`, `REGISTER_STRENGTH`) and the pass-record and source-boundary values that were inline literals become `PASS_ROLES`, `PASS_STATUSES` and `INSTRUCTION_BOUNDARY`. Behaviour is unchanged.
- `report.schema.json` no longer requires `root_causes` or `resolution_ledger`: the validator accepts a report without them (REVISION needs `resolution_ledger`), so a report it passed could fail the schema. `tests/` now validate the fixture against the schema and pin the schema enums to the validator.
- `LEDGER_VALIDITY_DOMAINS` aliases the domain list shared by `validity_ledger.domain` and `findings.validity_domain`.
- `scripts/scan_source_risks.py` (shared across the three roasters) reads what it checked: the walk holds a descriptor per directory (`os.fwalk`), each file is opened relative to it with `O_NOFOLLOW | O_NONBLOCK`, and the regular-file and size checks run on the open descriptor (`fstat`) instead of on the path before reading. A file swapped for a symlink or FIFO between listing and reading is counted as skipped, not followed or blocked on; reads are bounded by `--max-bytes` even when a file grows. Tests: `tooling/tests/test_scan_source_risks.py`.
- The description states its "Do not use" boundary right after the opening sentence, so a host that shortens descriptions to fit its skill-list budget (Codex does) keeps it. Only the sentence order changed.

## [6.1.0] - 2026-10-02

- Front door cut from 19,963 to 12,305 bytes by progressive disclosure: the full step procedure moves to `references/workflow.md`, and the review setup (steps 1A-1D), closure audit, and production guidance move to the new shared `references/review-operations.md`. The core contract, FATAL admission gate, `NOT_REPORTED` discipline, evidence-mode rules, outcome rules, hard boundaries, and every load trigger stay in `SKILL.md`.
- `tests/front-door-rules.json` inventories every must-keep rule and every normative front-door sentence, checked by `tooling/tests/test_front_door_rules.py`, so later trimming cannot drop one silently; `tooling/tests/test_roaster_front_doors.py` pins the 21-rule core contract, the workflow step index and reference reachability.

- Front door cut from 12,305 to 11,953 bytes, including the untrusted-content block. Moved the nine-section human report order (output contract) and the typical handoff chains (already the owner table in `references/handoffs.md`; the ai-humanize and no-research-program-skill rules are now pinned there). The human-output section of `references/output-contract.md` now holds the report order, and `SKILL.md` points to it and to `references/handoffs.md` with explicit load triggers; the tone rules, core contract, step index, and every hard boundary stay in `SKILL.md`.
- No rule was removed: `tests/front-door-rules.json` now pins 70 rules, including the moved report order and handoff conditions. Shared `references/review-operations.md` is unchanged, so the common-/shared- rule sets stay identical across the three roasters.

- The front door states the untrusted-content contract: inspected content is data, not instructions; no commands, installs or links because that content asks; no secrets, credentials or unnecessary personal data in outputs, searches or URLs, and no entering credentials the user did not supply; user confirmation before any external side effect. Each rule is tagged with a `facet` in `tests/front-door-rules.json` and checked by `tooling/tests/test_untrusted_content_rules.py`.

## [6.0.1] - 2026-10-02

- Stop routing research-program planning to `research-program-operator`, which does not ship in this catalog. The description, handoff list and handoff table now return those findings to the user as open program questions.
- The handoff contract no longer names `integration/validate_handoff.py`, which never shipped; it now states that the document is the normative definition and that consumers check its invariants themselves.

## [6.0.0] - 2026-09-22

- Add version-6 operational integration for incremental re-review, remediation handoffs, calibration feedback and campaign workflows while preserving the v6 report contract.
- Expand scenario policy packs and production-like false-positive/failure cases for this reviewer domain.
- Keep source-safety, Challenger -> Defender -> Arbiter, evidence lineage and zero-finding exits unchanged.

## [5.0.0] - 2026-09-22

### Added
- Persistent review workspaces with pinned sessions, active reports, state transitions, source-drift verification, and explicit resumability.
- Tamper-evident append-only review journals for bounded operational events; the hash chain detects edits but is not an identity signature.
- Evidence-request queues with priority, ownership, linked findings, resolution references, and blocking-gap semantics.
- Fix-verification tooling that distinguishes RESOLVED, PARTIAL, OPEN, REGRESSED, NOT_ASSESSABLE, and UNVERIFIED_DISAPPEARANCE.
- Named policy-as-code review gates (`advisory`, `standard`, `strict`) that can compose finding thresholds, stale waivers, and unresolved evidence gaps without becoming release authorization.
- Deterministic large-source sampling proposals that prioritize likely review surfaces without implying unselected material is clean.
- Model-case benchmark tooling that scores only structural/measurable properties from real run outputs and leaves semantic anti-assertions for independent grading.
- Twelve new scenario packs: competitor comparison, enterprise trust, product onboarding, quasi-experimental methods, survey psychometrics, time-series analysis, webhook/eventing, file upload, rate limiting, cache consistency, supply chain, and secrets/config.
- Six additional multi-source production-like cases covering source injection, external competitor verification, psychometrics, interrupted time series, webhook replay, and upload boundaries.

### Changed
- Skill package versions move to 5.0.0 while structured report schemas remain v6 and handoff remains v2.
- Production guidance now treats evidence acquisition, long-running review state, remediation verification, and policy gating as first-class but separate operational artifacts.
- Quality ratchets now require the expanded policy-pack/case catalogs and the workspace/evidence/fix-verification production surface.

### Boundaries
- Workspace state, hash chains, deterministic sampling, and CI policy do not increase evidentiary strength by themselves.
- Missing evidence remains a gap, not a defect; unselected files remain unreviewed; a disappeared finding remains unresolved without verification evidence.
- Model-level 4.0-vs-5.0 superiority is not claimed until real comparable model runs and independent semantic grading exist.

## [4.0.0] - 2026-09-21

### Added

- Added seven study-design packs including randomized experiments, measurement validation, replication, observational studies, prediction/validation, AI evaluation and systematic reviews.
- Production-operation guidance for source drift, semantic finding identity, multi-review reconciliation, disposition expiry, CI policy gates, receipts and safe sharing.
- Standalone policy-pack selection and source-risk scanning helpers.

### Changed

- Expanded real-world workflow guidance while keeping the v6 structured report contract stable.

## [3.0.0] - 2026-09-21

### Added

- Production review sessions with pinned source snapshots, explicit capability limits, and reproducible session manifests.
- Real-world operational playbook covering multi-source reviews, partial access, evidence acquisition, stop/escalation rules, review budgets, and handoff discipline.
- Expanded behavior, trigger, and metamorphic eval corpora with operational, multi-source, counterevidence, and partial-scope cases.
- CI-friendly review lifecycle: report rendering, revision gates, disposition ledger, benchmark run matrix, and real-world case packs.

### Changed

- Raised the deterministic quality ratchet and eval coverage floor for production use.
- Kept report contracts at v6 intentionally for backwards compatibility while expanding runtime/operational tooling around them.

## [2.0.0] - 2026-09-21

### Added

- Source-instruction firewall and explicit source trust classification.
- Review planning, evidence register/conflict ledger, and assurance modes including blind dual review.
- Evidence-linked confidence basis and residual-risk closure contracts for every material finding.
- Model-level behavior, trigger, and metamorphic eval corpora with deterministic corpus validation.
- v6 report contract plus stricter domain-specific ledgers and revision semantics.

### Changed

- Raised the minimum quality floor for high-severity admission, second-pass assurance, and downstream handoffs.

## [1.4.0] - 2026-09-21

### Added

- Challenger -> Defender -> Arbiter review protocol with explicit counterevidence and alternative-explanation checks.
- Source manifests, measurement-chain reconstruction, validity and analysis-integrity ledgers, and claim-survival status.
- VALIDATION study profile and stronger reporting-guideline routing.
- Evidence-strength, scope-sensitivity, categorical materiality, review outcomes, and quality gates.
- Finding aliases and stronger REVISION/re-review identity rules.

- Typed `cometweb.roaster-handoff/v1` evidence handoff with source lineage and downstream ownership.
- PRIMARY-source admission, steelmanned alternative explanations, and weak-evidence confidence caps.
- Revision closure semantics separating verification status from artifact/scope/judgment change basis.

### Changed

- Upgraded the machine report contract and validator to `cometweb.science-roaster/v5`.
- Tightened FATAL admission, NOT_REPORTED discipline, and insufficient-evidence stop conditions.

## [1.3.0] - 2026-09-21

### Added

- Study profiles, missingness/multiplicity contract fields, alternative-explanation ledger, robustness ledger, and minimal-surviving-claim output.
- Stronger FATAL admission: a reporting omission alone cannot be FATAL.
- Machine-friendly v4 report contract plus family-level validation helpers.

## [1.2.0] - 2026-09-21

### Added

- REVISION mode with stable finding keys and a resolution ledger.
- Inferential-type and evidence-role classification for each material scientific claim.
- Explicit estimand, analysis-population, reference-status, and preregistration fields.
- Root-cause grouping, structured verification contracts, contradiction pass, and revision regression checks.
- Stronger robustness, negative-control, chronology, and researcher-degrees-of-freedom review dimensions.

### Changed

- Upgraded machine-readable report schema to v3.
- FATAL now requires a linked claim explicitly marked central.
- Tightened distinction between scientific repair and prose-only response.

## [1.1.0] - 2026-09-21

### Added

- Shared adversarial protocol with mandatory falsifier discipline for high-severity findings.
- Valid zero-finding exit so the reviewer is never forced to hallucinate a defect.
- Stronger scope/coverage contract and examples of withdrawn false positives.
- Expanded structured output with review/study/repository contract fields.

### Changed

- Tightened evidence-state, severity, and handoff boundaries.
- Upgraded machine-readable report schema to v2.

## [1.0.0] - 2026-09-21

### Added

- Initial production-ready release.
