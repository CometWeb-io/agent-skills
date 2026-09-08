# CI Integration

Use the deterministic engine as a policy gate only after generating a candidate-specific manifest. CI automation does not remove the need for correct scope/risk classification.

## Basic evaluation

```bash
python scripts/readiness_engine.py --input readiness.json --pretty
```

The default process exit code is `0` when the manifest is valid, regardless of release verdict. Consume the JSON verdict explicitly.

## Strict CI policy

Fail CI unless verdict is exactly `GO`:

```bash
python scripts/readiness_engine.py \
  --input readiness.json \
  --ci-policy strict
```

Exit code:

- `0` → `GO`
- `1` → `GO_WITH_CONTROLS`, `DEFER`, or `NO_GO`
- `2` → invalid manifest/input

Use this when conditional release requires a separate approval path.

## Controlled CI policy

Allow `GO` and `GO_WITH_CONTROLS`:

```bash
python scripts/readiness_engine.py \
  --input readiness.json \
  --ci-policy controlled
```

Exit code:

- `0` → `GO` or `GO_WITH_CONTROLS`
- `1` → `DEFER` or `NO_GO`
- `2` → invalid manifest/input

Use only when the organization has a real mechanism to enforce named controls/accepted risks after the automated gate.

## Validate-only

```bash
python scripts/readiness_engine.py \
  --input readiness.json \
  --validate-only \
  --pretty
```

This returns a compact summary including verdict, snapshot hash, missing required gates, and scope gaps.

## Delta in CI

```bash
python scripts/readiness_engine.py \
  --input current-readiness.json \
  --previous previous-readiness.json \
  --pretty
```

Use the `delta` object to detect:

- new blockers;
- new binding unknowns;
- newly missing required gates;
- candidate identity change;
- score/coverage regression.

## Recommended pipeline placement

A practical order:

1. build immutable candidate;
2. establish profile + complete scope/risk flags;
3. bootstrap the required-gate manifest skeleton;
4. run candidate tests/scans and collect runtime/provider/docs evidence;
5. replace placeholders with evidence-backed states;
6. evaluate release readiness;
7. require human/organizational approval where policy demands it;
8. deploy/publish through the separate authorized workflow.

Do not generate a manifest before the candidate exists and then silently attach it to a later artifact.

## Policy ownership

Version-control organization-specific additions separately from the generic skill where possible:

- higher thresholds;
- additional required gates;
- release-specific approval requirements;
- environment-specific rollout controls.

Risk-tier floors in the engine are minimum safety policy and cannot be lowered through manifest overrides.
