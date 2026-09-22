# Gate model

```text
gate_id
required: true|false
state: PASS|FAIL|UNKNOWN|N/A
evidence[]: {source, locator, candidate_id, observed_at}
na_rationale
```

Rules:

- `PASS` on a required gate requires non-empty structured candidate-bound evidence with timezone-aware `observed_at`.
- `FAIL` on a required gate blocks readiness.
- `UNKNOWN` means the gate cannot currently be adjudicated and yields `DEFER`.
- `N/A` means the criterion genuinely does not apply; it requires a rationale and earns no implied pass.
- Controls are separate objects and may only cover bounded `MINOR|NOTE` residual issues. They must include `issue`, `owner`, and `revisit_condition`, and may never set `required_gate_bypass: true`.
