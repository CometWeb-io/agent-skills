# Roaster behavioral evaluation protocol

Structural validation is necessary but does not prove review quality. Each Roaster therefore ships model-level eval specifications in `evals/` in addition to deterministic validator tests.

## Eval families

1. **Behavior evals** — realistic review tasks with expected properties and assertions. Include clean artifacts, real defects, false-positive traps, incomplete scope, revision closure, and hostile/instruction-injection content.
2. **Trigger evals** — realistic should-trigger and near-miss should-not-trigger prompts. Near misses are more valuable than obviously unrelated negatives.
3. **Metamorphic evals** — paired tasks where a controlled change should preserve or monotonically change review behavior. Examples: reducing source scope must not increase confidence; adding counterevidence must not increase severity absent a changed defect; changing roast tone must not change evidence or severity.

## Quality rules

- Compare a new skill version against the previous version, not only against a no-skill baseline.
- Run both versions on the same prompts and pinned files.
- Prefer blind comparison when the host supports independent subagents.
- Track false positives separately from recall. A Roaster that finds more issues by hallucinating defects is worse, not better.
- Preserve a clean/no-material-findings subset so the benchmark rewards restraint.
- Include at least one source-injection trap per skill.
- Include at least one revision/closure case per skill.
- Do not claim model-level benchmark improvement unless those runs were actually executed.

## Suggested metrics

Use metrics only where they are objectively defined:

- schema/contract validity rate;
- anchor/source-lineage validity;
- top-severity admission precision on gold cases;
- false-positive rate on clean and scope-limited cases;
- revision closure accuracy;
- trigger precision/recall on the trigger eval set;
- token/time cost when the host exposes it.

Human review remains appropriate for scientific judgment, persuasiveness, novelty, and repair usefulness.
