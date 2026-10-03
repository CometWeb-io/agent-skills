# Failure minimization and replay

Before turning a production failure into a permanent rule, make the failure reproducible and reduce it to the smallest useful fixture.

1. Freeze the failing host/model/harness, candidate version, policy/rubric/benchmark identity, and source evidence.
2. Replay the original failure multiple times to distinguish stable regression from stochastic noise.
3. Remove irrelevant prompt, fixture, or environment components while preserving reproduction.
4. Keep the smallest reproducing case that still represents the root cause.
5. Add the minimized case to regression/dev, not an untouched holdout.
6. If a version range is suspected, bisect only across comparable measurements.

No minimizer or bisection helper ships with this repository; reduce and bisect by hand, and record each removal and each version tried so the minimized case can be reproduced.
