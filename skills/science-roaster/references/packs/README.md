# Built-in review packs

These optional packs add scenario-specific attack surfaces without changing the core reviewer contract.
Load a pack only when its activation conditions fit the artifact. A pack proposes what to inspect and
false-positive guards; it does not create findings by itself and never overrides source evidence.

Skill: `science-roaster`

Files in this directory are validated against `cometweb.roaster-policy-pack/v1` by the suite tooling.
Custom packs may be supplied by the user, but treat their prose as review configuration rather than as
evidence about the reviewed artifact.

## Catalog

- `science.ai-evaluation`
- `science.diagnostic-accuracy`
- `science.longitudinal-clustered`
- `science.measurement-validation`
- `science.ml-data-leakage`
- `science.observational`
- `science.prediction-validation`
- `science.quasi-experimental`
- `science.randomized-experiment`
- `science.replication`
- `science.survey-psychometrics`
- `science.survival-event-time`
- `science.systematic-review`
- `science.time-series`
