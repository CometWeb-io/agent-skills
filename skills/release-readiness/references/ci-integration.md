# CI Integration — engine 2.1

CI must use a candidate-specific manifest produced from actual scope and evidence.
JSON consistency is not evidence authentication and never authorizes deployment.

## Exit policies

```bash
python scripts/readiness_engine.py --input readiness.json --pretty
python scripts/readiness_engine.py --input readiness.json --ci-policy strict
python scripts/readiness_engine.py --input readiness.json --ci-policy controlled
```

| Policy | Exit 0 | Exit 1 | Exit 2 |
| --- | --- | --- | --- |
| `none` (default) | Valid assessment, regardless of verdict | Not used | Invalid input or unsafe/unavailable output |
| `strict` | `GO` only | Any other verdict | Invalid input or unsafe/unavailable output |
| `controlled` | `GO` or `GO_WITH_CONTROLS` | `DEFER` or `NO_GO` | Invalid input or unsafe/unavailable output |

Always inspect exit status and verdict; never pipe a failed command through a
success-returning consumer and call that a green gate. `controlled` is appropriate
only when a separate organizational process enforces and approves the controls.

`--validate-only` emits a smaller report, not weaker checks; `valid: true` means
structurally valid input, not approval. The compact report retains the verdict,
snapshot hash, contract hash, contract mismatch, and scope/gate gaps.

## Frozen before/after review

```bash
python scripts/readiness_engine.py \
  --input current-readiness.json \
  --previous previous-readiness.json \
  --ci-policy strict --pretty
```

This automatically freezes current requirements against the previously assessed
contract. Removing an inconvenient check cannot turn a failed previous review into
a clean current review. The `delta` object separates actual verified resolutions,
removed checks, changed requirements, newly unverified checks and missing gates.

For an explicitly reviewed scope change, provide the new independently approved
`--expected-contract-hash`. Never generate the supposed approval from the changed
manifest inside the same CI job. Hash consistency does not establish who approved
it, so retain the approval provenance outside this skill.

## Immutable local outputs

```bash
python scripts/readiness_engine.py --input readiness.json \
  --output results/candidate-assessment.json --ci-policy strict
```

An output must not replace either input manifest, traverse output symlinks, or
replace an existing different result. Repeating byte-identical output is allowed.
Use a new result path for a new assessment. The bootstrapper applies the same
protection to its `--context` and `--output` paths. No JSON success is printed when
output creation fails.

## Collection and release flow

Build the immutable candidate; resolve scope/risk flags; bootstrap required gates
as unknown; freeze reviewed requirements; run the actual checks; preserve the
run's full candidate identities, environment, optional config fingerprint and
explicit-offset observation times; replace placeholders with evidence; evaluate
and red-team the result; require any independent approval; deploy only through a
separately authorized workflow.

A unit-test count, mocked integration trace, generated manifest, copied answer or
self-asserted `verified` label is not a runtime test. Keep the original artifacts
and review whether they support the claimed behavior.

Organization-specific thresholds and approval requirements remain separate from
this generic skill. Baseline floors cannot be lowered via manifest overrides.
For the full input contract and stricter legacy migration, read
`manifest-schema.md`.
