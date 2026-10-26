# Quality loop profiles

Choose checks from the active contract before review. The profile lists available capabilities and their order; it does not require creating an artifact again or adding a second review to an existing one.

## EDITORIAL / SALES / TECHNICAL_DOCS

For an existing artifact, normally select one reviewer (`content-reviewer` for requirements/usefulness or `content-roaster` for adversarial critique), then verify the result under `artifact-acceptance`. Add repair only for accepted material findings and authorized edits. Add another review only for a named unanswered question or an explicit contract requirement. DEEP means stronger evidence for the relevant risks, not an automatic second opinion.

Formal `required_stages` may select an ordered subset of: brief-architect, content-writer, content-reviewer, content-roaster, repair-operator, artifact-acceptance. It must include at least one reviewer and artifact-acceptance. A review-only task can simply return findings without claiming formal artifact acceptance or running this control plane.

## RESEARCH

Use science-roaster for methodology and artifact-acceptance for the deliverable; add constructive content review only if communication quality is a separate open question. The available order is brief-architect, content-writer, content-reviewer, science-roaster, repair-operator, artifact-acceptance. A formal plan retains science-roaster and artifact-acceptance. It does not replace research governance or journal acceptance.

## REPO_DEEP

Audit with repo-roaster, repair when authorized, recheck changed surfaces. A formal plan contains repo-roaster and optionally repair-operator. Completion closes this audit workflow; software release verdicts belong to release-readiness for a specific candidate. Artifact acceptance may assess the report, never the software deployment.

## SKILL_QUALITY

The empirical qualification chain remains skill-auditor, rubric-designer, benchmark-curator, skill-evaluator with linked rubric/benchmark hashes. A formal required_stages plan cannot remove that chain. A static-only audit may return its bounded result without claiming model lift or formal qualification. Requested edits remain owned by skill-creator.

## Existing sidecars

Without required_stages, the kernel preserves the former full profile sequence for compatibility, including both editorial reviews. New bounded runs declare their actual required_stages and a pre-evaluation policy_lock. Do not silently narrow an existing contract after seeing a failure. Omitted stages are out of the agreed scope, not SKIPPED mandatory checks; a selected required stage cannot be skipped.
