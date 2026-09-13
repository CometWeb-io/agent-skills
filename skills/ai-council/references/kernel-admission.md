# Kernel admission — development 5.0.1

The kernel checks supplied records. It does not verify sources, authenticate approvals, run advisers, execute actions, or grant deployment/publication permission. A supplied `BLOCK` remains `NO-GO`; this preserves the declared constraint, not its factual authentication.

## Final gate

Pass every required role from `plan.roles.gatekeepers` to `--required-gates-json`. Missing roles and required roles marked `NOT_REQUIRED` defer the decision. The input statuses remain operator-supplied: do not mark a role CLEAR simply because it was routed.

```bash
python3 scripts/council_kernel.py gate \
  --verdict GO --confidence 0.9 --required-confidence 0.8 \
  --freshness-status CLEAR \
  --required-gates-json '["security"]' \
  --gate-statuses-json '{"security":"CLEAR"}' \
  --require-go
```

The numbers and status above are a syntax example, not evidence or recommended confidence values. Compute the applicable threshold and provide actual checked state. Freshness on the CLI defaults to `UNKNOWN`; pass `CLEAR` only after assessing applicable evidence and its coverage. The Python function retains `freshness_status="CLEAR"` solely for compatibility with existing callers; new callers must pass the assessed value explicitly.

`--require-go`: exit 0 for a resulting GO, 1 for a processed non-GO verdict, and 2 for malformed inputs. Without it, a processed DEFER/NO-GO/TEST is report output with exit 0. No exit code is authorization to execute an action.

Unknown/invalid numbers and non-boolean flags are errors, not zero, approval, or completed controls. Missing binding confidence dimensions yield overall zero and `missing_binding_dimensions`. A critical gap cannot be erased by confidence: GO/NO-GO becomes TEST when a reversible experiment is available, otherwise DEFER. That TEST is a recommendation to design/review an experiment, not permission to run one. Unimplemented required controls always defer, including a proposed TEST. A genuinely separate experiment requires its own scoped gate assessment.

## Observation and forecast accounting

Read `watch.observation_status` before interpreting `triggered`. UNKNOWN is not false. An empty freshness or contradiction input is not clearance. Contradiction coverage reads all material opposition, even when `contradiction_tested` is false, but it still relies on declared flags and does not validate an actual search log.

`forecast-score` reports input, scored, invalid and unresolved counts. Missing, non-numeric or out-of-range probabilities are invalid, not probability zero. A valid unresolved outcome is excluded from the Brier denominator. These checks do not establish that a forecast preceded the event or that forecasts are independent.

## Validation and limits

```bash
python3 -m pytest -q tests
python3 -m unittest discover -s tests -p test_council_kernel.py
```

Pytest is a development dependency for the new regression file. Runtime CLI uses the standard library only. CLI JSON rejects duplicate keys and non-finite numbers, with a four-megabyte input limit. It reports errors without echoing raw payloads. This is not a complete schema validator for every legacy command; unmodified ranking, learning and storage helpers retain their earlier contracts.

Synthetic tests assess deterministic mechanics, not decision quality, external model independence, authenticity of evidence or qualified human approval. Package VERSION is unchanged and no release is published.
