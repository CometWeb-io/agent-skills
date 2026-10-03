# Output contract

Return:
- status: `READY_TO_FREEZE`, `NEEDS_REBALANCE`, `NEEDS_REVISION`, `CONTAMINATED`, or `INVALID`;
- benchmark ID, revision, immutable `benchmark_hash`, and the `rubric_hash` of the rubric from `rubric-designer` when one is bound (state `none bound` otherwise; the kernel does not check it);
- taxonomy, difficulty strata, positive/negative/adversarial/regression counts, and dev/holdout split counts;
- provenance coverage and candidate-exposure metadata;
- duplicate and near-duplicate findings;
- leakage status (`CLEAN`, `SUSPECT`, `CONTAMINATED`) plus immutable `corpus_fingerprint` for DEEP evaluation;
- holdout contamination/exposure decisions and removed/quarantined case IDs;
- coverage gaps and known blind spots;
- regression cases added from production failures, explicitly kept out of a clean holdout when exposed to the candidate;
- next owner (`rubric-designer`, `skill-evaluator`, `feedback-integrator`, or none).

Never claim a holdout is clean from a generic similarity glance. Preserve leakage provenance and the exact frozen corpus identity.
