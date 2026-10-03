# Output contract

Return a constructive review, with the few highest-impact findings first.

```text
schema: cometweb.content-review/v1
mode: LIGHT|STANDARD|DEEP|DELTA     # default STANDARD
candidate_id                        # OBSERVATION evidence must name it when set
base_candidate_id?
status: REVIEWED | CHANGES_REQUIRED | INVALID
required_axes[]?                    # axes coverage must reach; DEEP defaults to all seven
coverage[]: {axis, state: COVERED|N/A|UNKNOWN, rationale?}
                                    # required in DEEP and DELTA; one row per axis;
                                    # N/A needs rationale; UNKNOWN on a required axis is an error
enforce_evidence_floor?: true|false # see references/evidence-calibration.md
findings[]: {finding_id, finding_status: NEW|CARRIED|REOPENED, axis, severity, observation, interpretation, evidence[]}
                                    # full finding fields: references/finding-contract.md
verify[]
recommended_next_skill
```

Axes are `brief-compliance`, `reader-value`, `structure`, `claim-integrity`,
`actionability`, `consistency` and `language-ux`. `schema`,
`base_candidate_id`, `interpretation`, `verify` and `recommended_next_skill`
are for the reader; the kernel does not check them.

Each material finding uses stable identity. Keep `observation` separate from `interpretation`; preserve uncertainty. `CARRIED` requires revalidation against the current candidate. Do not provide a final READY verdict — `artifact-acceptance` owns that. Do not silently rewrite the whole artifact.

`kernel.review(payload)` returns `{status, blockers, majors, errors[],
coverage_complete, covered_axes, mode}`; any error makes the status INVALID.
