# Output contract

Return:
- status;
- benchmark ID, revision, immutable `benchmark_hash`, and bound `rubric_hash`;
- taxonomy, difficulty strata, positive/negative/adversarial/regression counts, and dev/holdout split counts;
- provenance coverage and candidate-exposure metadata;
- duplicate and near-duplicate findings;
- leakage status (`CLEAN`, `SUSPECT`, `CONTAMINATED`) plus immutable `corpus_fingerprint` for DEEP evaluation;
- holdout contamination/exposure decisions and removed/quarantined case IDs;
- coverage gaps and known blind spots;
- regression cases added from production failures, explicitly kept out of a clean holdout when exposed to the candidate;
- next owner (`rubric-designer`, `skill-evaluator`, `feedback-integrator`, or none).

Never claim a holdout is clean from a generic similarity glance. Preserve leakage provenance and the exact frozen corpus identity.
