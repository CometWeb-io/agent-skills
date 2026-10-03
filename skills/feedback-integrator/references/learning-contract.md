# Learning proposal contract

```text
pattern
observations[]
independence_count
run_count
severity: NOTE|MINOR|MAJOR|BLOCKER
root_layer: ROUTING|INSTRUCTION|REFERENCE|KERNEL|EVAL|HOST|PROCESS
causal_hypothesis
evidence[]
affected_skills[]
proposal
expected_effect
blast_radius
compatibility_risk
regression_test: {id, assertion}
test_gap: {assertion, owner}
lifecycle_status: WATCH|PROPOSED|ACCEPTED|IMPLEMENTED_UNVERIFIED|VERIFIED|REJECTED
```

This is the human-facing proposal record. The kernel computes `pattern`,
`independence_count`, `run_count`, `severity` and `root_layer` from the input
records in `references/output-contract.md` and reads `regression_test`,
`test_gap` and `expected_effect`; the remaining fields (`observations`,
`causal_hypothesis`, `affected_skills`, `proposal`, `blast_radius`,
`compatibility_risk`, `lifecycle_status`) are for the reader.

Count independence by distinct task/context, not multiple runs of the same fixture. A proposal needs independent recurrence or clearly systemic BLOCKER evidence plus a regression test or owned test gap. Conflicting root-layer evidence stays WATCH until resolved.
