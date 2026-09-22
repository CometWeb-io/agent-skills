# Review assurance protocol

The suite separates self-challenge from independent review. Challenger -> Defender -> Arbiter improves discipline inside one reasoning context, but it is not independent corroboration.

## Auditable pass records

Every report records the passes that actually ran in `assurance.pass_records`. Each pass carries a stable `pass_id`, role (`PRIMARY`, `SECONDARY`, optionally `ARBITER`), an opaque `context_ref`, status, whether it was blind to prior findings, and the exact source ids it inspected. These records are provenance, not proof that a model was competent; they exist so a later consumer can distinguish one self-review from a real separate-context pass.

## Assurance modes

- `SINGLE_REVIEW` — one reviewer context. `independence=NONE`, `second_pass_status=NOT_RUN`.
- `SECOND_PASS` — a deliberate second review pass after the first candidate set. It may run in the same context (`SAME_CONTEXT`) or a separate one (`SEPARATE_CONTEXT`). If the host cannot run it, record `UNAVAILABLE` and the limitation; do not pretend it happened.
- `BLIND_DUAL_REVIEW` — two separate reviewer contexts inspect the same pinned source boundary without seeing each other's candidate findings, then an arbiter reconciles disagreements. Requires `independence=SEPARATE_CONTEXT` and `second_pass_status=COMPLETED`.

## When to spend assurance budget

Prefer a targeted independent pass when one of these is true:

- a top-severity finding would materially change a purchase, publication, deployment, or other consequential decision;
- evidence is technically dense or ambiguous and reasonable reviewers may disagree;
- the report is a revision closure review and an incorrect `RESOLVED` state would be costly;
- the user explicitly requests maximum rigor, independent review, or multiagent review.

Do not duplicate the entire review when a second pass would not change the decision. Ask the second reviewer to attack the highest-consequence claims/findings and known uncertainty instead.

## Blind dual review procedure

1. Pin identical source manifests and review contract.
2. Reviewer A and Reviewer B independently produce candidate findings and no shared hidden reasoning.
3. Normalize candidate identity by root cause/claim/invariant rather than wording.
4. Arbiter classifies agreement as `AGREE`, `PARTIAL`, `DISAGREE`, or `UNIQUE`.
5. Search source evidence to resolve disagreements; never settle them by majority vote alone.
6. Preserve unresolved disagreement in `assurance.disagreement_summary` and calibrate confidence downward when material.

## Report semantics

`assurance` records what actually ran, not what the reviewer wished had run. A single-context second pass remains `SAME_CONTEXT`. A model reviewing its own output twice is not independent.
