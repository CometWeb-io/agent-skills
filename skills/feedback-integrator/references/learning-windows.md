# Learning windows and evidence weighting

Patterns should reflect current behavior, not an immortal pile of historical failures.

Set an `as_of` time and a bounded learning window when timestamps exist. Observations outside the window become historical context unless explicitly revalidated.

Distinguish outcomes:

- `CONFIRMED`: the observed failure was real.
- `FALSE_POSITIVE`: the detector/reviewer was wrong.
- `RESOLVED`: the failure was real but the current version no longer reproduces it.
- `UNKNOWN`: insufficient evidence.

A false-positive-dominant cluster stays `WATCH`; a resolved-only cluster should retire rather than generate a fresh change proposal.

For strict improvement proposals require: proposed change, expected effect, evaluation plan, and a regression test or explicit test gap. Optimize for recurrence reduction without weakening safety or evidence gates.
