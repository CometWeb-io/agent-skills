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

- Added seven scenario packs including homepage positioning, founder-led outbound, long-form reports, SaaS pricing, case-study proof, sales email and technical docs.
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

- Challenger -> Defender -> Arbiter self-challenge protocol for material findings.
- Source manifests, evidence-strength and scope-sensitivity calibration, categorical materiality, and explicit review outcomes.
- Product-page, pricing, case-study, and sales-deck profiles plus proof-debt and message-chain controls.
- Quality gates and stronger verification contracts with explicit failure signals.
- Finding aliases and stronger DELTA/re-review identity rules.

- Typed `cometweb.roaster-handoff/v1` evidence handoff with source lineage and downstream ownership.
- PRIMARY-source admission, steelmanned alternative explanations, and weak-evidence confidence caps.
- Revision closure semantics separating verification status from artifact/scope/judgment change basis.

### Changed

- Upgraded the machine report contract and validator to `cometweb.content-roaster/v5`.
- Tightened BLOCKER admission and insufficient-evidence stop conditions.

## [1.3.0] - 2026-09-21

### Added

- Review profiles, decision-cost calibration, proof-burden labels, objection ledger, and decision-impact classification.
- Stronger severity admission gates and explicit reviewer burden-of-proof discipline.
- Machine-friendly v4 report contract plus family-level validation helpers.

## [1.2.0] - 2026-09-21

### Added

- DELTA re-review mode with stable finding keys and a resolution ledger.
- Claim taxonomy, proof burden, decision role, root-cause grouping, and structured verification contracts.
- Contradiction pass, counterfactual repair test, and root-cause deduplication in the shared adversarial protocol.
- Revision protocol with RESOLVED / PARTIAL / OPEN / REGRESSED / NOT_ASSESSABLE states.

### Changed

- Upgraded machine-readable report schema to v3.
- Tightened BLOCKER claim linkage, verification, and high-severity falsifier requirements.
- Expanded rubric for cross-artifact consistency, proof timing, and revision regressions.

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
