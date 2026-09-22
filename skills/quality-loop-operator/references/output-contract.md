# Output contract

Return a compact human brief plus, when supported, a machine sidecar.

Human brief default:

1. `STATE`
2. `POLICY LOCK`
3. `CONFLICTS`
4. `MEASUREMENT` — rubric/benchmark identity plus paired/stability state when the profile measures a skill
5. `RUNTIME LIFECYCLE` — compatibility, host support, rollout state, observation window, rollback/deprecation state when applicable
6. `NEXT STAGE`
7. `REVALIDATE`
8. `BLOCKER`
9. `DONE WHEN`

Machine sidecar fields:

```text
schema, run_id, profile, mode, as_of,
candidate_id, base_candidate_id?, contract_id,
policy_lock,
stages[], reconciliation[],
coverage, revalidate[], next_stage,
status, completion_evidence[],
runtime_lifecycle? {state, contract_compatibility, host_support,
                    observation_runs?, min_observation_runs?,
                    stability_status, paired_status, rollback_version?}
```

For `SKILL_QUALITY`, preserve evaluator `paired_status` and `stability_status` into runtime lifecycle governance. READY_FOR_FULL/FULL cannot be reconstructed from prose if these fields are missing. A sidecar records orchestration truth; it does not replace specialist evidence.
