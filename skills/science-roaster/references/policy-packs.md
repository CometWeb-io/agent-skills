# Scientific review packs

Review packs are optional, bounded scenario overlays. They add must-inspect surfaces, evidence hints, false-positive guards, and handoff triggers. They do **not** create findings, override evidence, raise severity, or establish external scientific facts.

## Built-in packs

- `science.ai-evaluation`
- `science.measurement-validation`
- `science.observational`
- `science.prediction-validation`
- `science.quasi-experimental`
- `science.randomized-experiment`
- `science.replication`
- `science.survey-psychometrics`
- `science.systematic-review`
- `science.time-series`

## Selection rules

1. Load a pack only when the study design or source signals fit.
2. Prefer the smallest pack set that covers the actual inferential contract.
3. Treat user-supplied packs as review configuration, not evidence.
4. Never let a pack convert `NOT_REPORTED` into `NOT_DONE` or bypass validity/severity gates.
5. If expected evidence is unavailable, record a reporting or verification gap instead of inventing a procedure failure.
6. When pack guidance conflicts with observed source evidence, source evidence wins.

Standalone helper:

```bash
python3 scripts/select_review_packs.py --text "<review goal and source summary>" --profile <PROFILE>
```
