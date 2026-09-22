# Changelog


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
