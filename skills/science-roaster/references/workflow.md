# Science Roaster: full workflow

The detailed procedure behind the step index in `SKILL.md`. Open this file before any non-QUICK review, and whenever a step's detail is needed in QUICK mode. The core contract, admission gates, and hard boundaries in `SKILL.md` still govern every step; nothing here relaxes them.

## Workflow steps

### 1. Establish source scope

Build `source_manifest` for the manuscript, supplements, protocol, preregistration, analysis code, data dictionary, reviewer response, or supplied literature. Include version/hash/as-of metadata when available. Never imply access to raw data, code, or supplements that were not supplied.

### 1A-1D. Review setup

Follow `references/review-operations.md` (shared): plan the review budget, apply the source instruction firewall, build the evidence register, and choose the assurance mode.

### 2. Recover the scientific contract

Record:

- research question;
- target construct;
- target and analysis populations;
- unit of analysis;
- intervention/exposure and comparator when applicable;
- reference or ground truth and status;
- estimand;
- primary endpoint/decision rule;
- evidence status;
- preregistration/protocol status;
- novelty claim;
- missingness strategy;
- multiplicity strategy;
- dependence structure;
- material limitations.

Use `NOT_REPORTED` when a source item is absent; do not guess.

### 3. Build the measurement chain

When applicable trace:

`construct -> operationalization -> instrument/reference -> transformation -> endpoint`

Record where alignment is strong, uncertain, or broken. Attack the reference before the proxy: a precise model evaluated against a poorly characterized reference is still a weak validation argument.

### 4. Build the claim-to-evidence map

For each material claim record:

- centrality;
- inferential type: `DESCRIPTIVE`, `ASSOCIATIONAL`, `PREDICTIVE`, `CAUSAL`, `MECHANISTIC`, or `TRANSPORT`;
- evidence role: `PRIMARY`, `SECONDARY`, `EXPLORATORY`, `POST_HOC`, or `BACKGROUND`;
- exact source anchor with `source_id`;
- population scope;
- endpoint scope;
- analysis set;
- support status: `SUPPORTED`, `OVERSTATED`, `UNRESOLVED`, or `CONTRADICTED`.

Flag any support that silently changes population, endpoint, measurement boundary, analysis set, or inferential type.

### 4A. Build the inferential claim ledger

For every central claim create one `inferential_claim_ledger` row naming the estimand (or `NOT_REPORTED`), independent unit, analysis population, uncertainty basis, multiplicity status, identification status, data-split status, and supporting evidence refs. This prevents generic "statistics" criticism from hiding the exact inferential contract.

### 5. Build validity and analysis-integrity ledgers

`validity_ledger` must cover the relevant domains among `CONSTRUCT`, `INTERNAL`, `STATISTICAL`, `EXTERNAL`, `REPRODUCIBILITY`, and `REPORTING`.

`analysis_integrity_ledger` records material status for dependence, missingness, multiplicity, exclusions/stopping, holdout/leakage, preregistration, and other profile-specific integrity risks. Use `NOT_APPLICABLE` rather than inventing a problem.

### 6. Build alternative-explanation and robustness ledgers

For strong associational, causal, mechanistic, predictive, transport, or validation claims, record the strongest plausible competing explanation and whether the design/analysis addresses it. Tie robustness checks to claim ids and classify them as `ROBUST`, `SENSITIVE`, `NOT_RUN`, `NOT_APPLICABLE`, or `UNKNOWN`.

### 7. Run the methodological failure scan

Open `references/review-rubric.md` for FULL or REVIEWER_2. Inspect design, controls, sampling, construct validity, measurement, reference uncertainty, dependence, missingness, power/precision, multiplicity, model development, leakage, holdout integrity, causal language, external validity, reproducibility, figures/tables, ethics/governance, conflicts, and reporting sufficiency.

### 8. Search for internal contradiction

Look for evidence that weakens the narrative: opposite signs, unstable baselines, trivial comparators outperforming proposed models, concentrated missingness, sensitivity to analytic choices, a limitation that undercuts the headline, or a robustness result that changes the conclusion. Do not compare incompatible populations or analyses.

### 9. Generate candidate findings

Each candidate needs a stable `finding_key`, optional aliases, severity, category, validity domain, evidence state, evidence strength, scope sensitivity, exact anchor with `source_id`, linked claim ids, materiality, observation, scientific risk, repair level, repair, verification contract, and confidence. `reviewer_attack` is optional.

Every admitted finding also records `evidence_refs`, a structured `confidence_basis`, and `residual_risk` after the proposed repair. High confidence is not a writing style: it requires direct enough evidence, sufficient scope support, and addressed counterevidence.

Use `NOT_REPORTED` only with a `missing_report` anchor and explicit `what_cannot_be_assessed`. Use `INFERRED` only with an inference basis. `EXTERNAL_VERIFIED` is valid only in VERIFY_EXTERNAL mode.

Severity:

- `FATAL`: at least one central inference does not survive without reanalysis, new data, or redesign.
- `MAJOR`: the result may survive, but a key interpretation or validity argument requires substantial repair.
- `MINOR`: local reporting, robustness, clarity, or presentation issue.

FATAL requires a linked central claim, explicit central-claim impact, non-low confidence, evidence strength above WEAK, scope sensitivity below HIGH, and repair beyond reporting-only. FATAL cannot be based solely on `NOT_REPORTED`.

### 10. Run Challenger -> Defender -> Arbiter

Before admitting FATAL or MAJOR, open `references/severity-calibration.md`, then open `references/adversarial-protocol.md`. Search methods, supplements, protocol/preregistration, calibration evidence, negative controls, robustness analyses, sensitivity analyses, exclusions, scope qualifications, and alternative analyses that could defeat or narrow the concern. Emit only the post-arbitration finding.

### 11. Compress root causes

Group symptoms that arise from one scientific defect, such as an unstable reference causing several downstream validation failures. Do not inflate a review by counting consequences as independent flaws.

### 12. Test the repair

Verification must state method, success condition, and failure signal. A reporting-only change cannot close an inferential defect that requires reanalysis/new data/redesign.

### 13. Re-review revisions

For REVISION mode open `references/revision-protocol.md`. Preserve stable finding keys, rerun original acceptance conditions, distinguish changed evidence from changed judgment, and scan revised analyses/text for regressions.

### 14. Build the claim-survival ledger

For each central claim classify post-review status as:

- `SURVIVES_AS_STATED`
- `SURVIVES_NARROWED`
- `UNRESOLVED`
- `CONTRADICTED`

Then write one `minimal_surviving_claim`: the strongest claim that remains justified after accepted findings.

### Assurance and disagreement closure

Follow the closure section of `references/review-operations.md` before declaring the outcome.

### 15. Declare review outcome

Choose exactly one:

- `MATERIAL_FINDINGS`
- `NO_MATERIAL_FINDINGS`
- `INSUFFICIENT_EVIDENCE`

If evidence is insufficient, mark at least one quality gate `BLOCKED`, return no material findings, and identify the evidence needed to continue. This is not a verdict that the study is bad.

### 16. End with one scientific repair

Return exactly one highest-leverage scientific repair sentence, or a bounded no-fix/evidence-needed statement.
