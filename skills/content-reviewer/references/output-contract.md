# Output contract

Return a constructive review, with the few highest-impact findings first.

```text
schema: cometweb.content-review/v1
mode: LIGHT|STANDARD|DEEP|DELTA
candidate_id
base_candidate_id?
review_status: REVIEWED | CHANGES_REQUIRED | INVALID
coverage: {axis: COVERED|N/A|UNKNOWN}
findings[]: {finding_id, state:NEW|CARRIED|REOPENED, axis, severity, observation, interpretation, evidence[]}
verify[]
recommended_next_skill
```

Each material finding uses stable identity. Keep `observation` separate from `interpretation`; preserve uncertainty. `CARRIED` requires revalidation against the current candidate. Do not provide a final READY verdict — `artifact-acceptance` owns that. Do not silently rewrite the whole artifact.
