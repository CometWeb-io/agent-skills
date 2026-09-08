# Sequencing rules

## Execution loop

For each step in the workflow plan:

1. Announce step number, skill name, and purpose.
2. **Read** `skills/<name>/SKILL.md` (or the installed symlink path) in full for that step.
3. Execute that skill's workflow — scripts, validators, output contract included.
4. Emit the CW-AIP envelope named in the plan (`EvidenceEnvelope`, `FindingEnvelope`, etc.).
5. Pass `dependencies` from prior envelope IDs into the next step.
6. Stop at skill boundaries — do not issue downstream verdicts early.

## Hard boundaries

| Step | Must not |
| --- | --- |
| evidence-researcher | GO/NO-GO, product priorities, Council rounds |
| ai-council | Skip decision-specific re-verification of material claims |
| product-operator | Replace Release Readiness for pinned RC gates |
| release-readiness | Run without pinned artifact + environment |
| web-app-auditor | Ship verdicts — findings only |

## When to shorten the plan

- User says **evidence pack only** → single_skill → evidence-researcher.
- No material decision in goal → drop ai-council step even if archetype default includes it.
- No pinned RC → drop release-readiness; suggest repo-to-roadmap or product-operator instead.
- Step returns `READY` evidence with no gaps → proceed; do not re-research.

## When to extend the plan

- Material claim gaps after step 1 → stay in evidence-researcher until admission gate passes or user accepts gaps.
- Audit blockers for release → web-app-auditor may need a second pass with `needs-repro` items cleared.
- Council requests live re-check → run targeted verification before verdict (Council policy).

## User-visible progress

After each step, emit a short **Handoff summary**:

```text
Step 2/3 complete — EvidenceEnvelope (12 claims, 2 gaps)
Next: ai-council — decision question: <one line>
```

Final section: **Workflow result** — what each step produced and what remains manual.
