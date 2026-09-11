# publication-report.json contract

Use protocol `longform-publisher/1`.

Required top-level publication state:

- `protocol_version`, `as_of`, `mode`, `status`, `status_reason`;
- `publication{}` with id/title/type/audience/objective;
- `source_policy{}` and `sources[]`;
- `lifecycle{}` and `current_stage`;
- `canonical_master{path, version, sha256}` once drafting has begun;
- `sections[]`;
- `claim_uses[]`;
- `protected_facts[]`;
- `fidelity{}` and `edit_history[]` when relevant;
- `unresolved_gaps[]`;
- `derived_artifacts[]`;
- `publication_evidence[]`;
- `actions{blockers, verify_now, decision_now, now, next_milestone, delegate, waiting, stop}`.

## Admission rules

- SOURCE_BOUND may reference only authorized sources.
- Material FACT claims cannot claim reconciliation without support. Every `evidence_ref` must resolve to a registered source; otherwise return `EVIDENCE_REF_UNRESOLVED`.
- Volatile current claims cannot rely only on stale/unknown evidence.
- Declared `current_stage` cannot exceed the stage inferred from gates.
- Critical open gaps block RELEASE_READY.
- `PUBLISHED` requires publication evidence.
- `SCIENTIFIC_MANUSCRIPT`, `ACADEMIC_PAPER`, and `RESEARCH_PAPER` at RELEASE_READY/PUBLISHED require `scientific_readiness.status=PASS`, `source=research-program-operator`, and a resolvable evidence reference; otherwise return `SCIENTIFIC_READINESS_REQUIRED`.
- Substantial rewrite/humanization requires post-edit fidelity before MASTER_LOCKED.
- Derived artifacts must bind to the current master hash and pass format-specific QA/parity.

Run the kernel in this order when applicable:

```bash
python3 scripts/publication_kernel.py validate --report-json publication-report.json
python3 scripts/publication_kernel.py check-manuscript --report-json publication-report.json --manuscript-file manuscript.md
python3 scripts/publication_kernel.py check-derived --report-json publication-report.json
python3 scripts/publication_kernel.py render-manifest --report-json publication-report.json --output publication-brief.md
python3 scripts/publication_kernel.py check-brief --report-json publication-report.json --brief-file publication-brief.md
```
