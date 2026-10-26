# Content Roaster: formal v6 reports

Load this file only when a caller requires the existing structured contract. For ordinary prose use `SKILL.md`; the fields below do not become mandatory prose sections.

Build the object described in `references/output-contract.md` and `references/report.schema.json`:

- Pin source/version, inspected and excluded scope in `source_manifest` and coverage. Keep source-linked evidence in `evidence_register`; apply `references/source-safety.md`.
- For formal review setup and closure, use `references/review-operations.md`. Record only observed passes under `references/assurance-protocol.md`.
- Recover the reader's decision contract and message chain, leaving unsupported context unknown. Create a source-anchored `claim_map`; distinguish absent proof from a false claim.
- Populate `proof_debt_ledger`, `objection_ledger` and `diagnosis_ledger` only with supported entries; an empty list is valid where the contract permits it. Diagnose the failed layer before prescribing copy changes.
- Admit findings using `references/evidence-discipline.md`, `references/severity-calibration.md` and `references/adversarial-protocol.md`. Bind each finding to the anchor source and retain uncertainty.
- Give each repair a falsifiable verification contract. Populate outcome fields and gates consistently: insufficient evidence blocks a judgment, not a clean result. Read `references/reviewer-failure-modes.md` when checking closure errors.

Additional detail is conditional:

- Read `references/revision-protocol.md` for DELTA; rerun original verification before marking resolved.
- Read `references/handoffs.md` and `references/handoff-contract.md` when emitting a typed downstream handoff; do not execute the next specialist implicitly.
- Read `references/production-ops.md` or `references/workspace-ops.md` for CI, source drift or multi-session state.
- Read `references/rubric.md`, `references/profiles.md` or `references/real-world-playbook.md` for a relevant domain question, not as mandatory review stages.
- Read `references/examples.md` or `references/eval-protocol.md` only for calibration or evaluation. Policy-pack configuration is in `references/policy-packs.md` and `references/packs/README.md`.

Validate the completed report with `python3 scripts/validate_roast.py report.json`. Validation checks shape and evidence discipline, not truth or reader response.
