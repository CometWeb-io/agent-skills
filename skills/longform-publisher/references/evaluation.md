# Evaluation contract

Golden cases must cover both valid and invalid publication states. Keep synthetic names/data unless a public fixture is intentionally required.

Required failure classes include:

- `SOURCE_BOUND_UNAUTHORIZED_SOURCE`
- `MATERIAL_CLAIM_UNSUPPORTED`
- `EVIDENCE_REF_UNRESOLVED`
- `SCIENTIFIC_READINESS_REQUIRED`
- `VOLATILE_CLAIM_STALE_EVIDENCE`
- `POST_EDIT_FIDELITY_REQUIRED`
- `PROTECTED_FACT_MISSING`
- `CITATION_MARKER_MISSING`
- `DERIVED_MASTER_HASH_MISMATCH`
- `VISUAL_QA_REQUIRED`
- `VISUAL_QA_MISSING`
- `DERIVED_PARITY_FAILED`
- `DERIVED_MATERIAL_EDIT_FORBIDDEN`
- `CRITICAL_GAP_OPEN`
- `PUBLISHED_WITHOUT_EVIDENCE`
- `STAGE_INFLATION`

Maintain scenarios for BUILD, SOURCE_BOUND, RESEARCH_EXPAND and REFRESH; humanization invariant drift; current-claim freshness; DOCX/PDF QA; canonical-master lineage; scientific-readiness handoff; and publication evidence.

When modifying the skill, run unit tests, `scripts/run_evals.py`, the example end-to-end gate, Skill Creator validation, then repeat from the unpacked final ZIP.
