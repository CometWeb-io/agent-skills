## What changes

<!-- One or two sentences. What behaviour is different after this PR? -->

## Why

<!-- The problem this solves. Link an issue if there is one. -->

## Checks

```
uv run python tooling/check_all.py --ci
# A new report directory outside the checkout; nothing is overwritten.
uv run python tooling/validate_local.py --trusted-checkout --output ../agent-skills-pr-validation --timeout 900
```

- [ ] Canonical CI gates pass with zero failed or skipped gates
- [ ] External validation `report.json` says `passed` (no skipped test cases)
- [ ] `./tooling/public-safety-check.sh` reports no findings
- [ ] Registry and packages agree — generated files regenerated, not hand-edited

## If behaviour changed

- [ ] A test or eval case fails without this change and passes with it
- [ ] Routing changes come with a case in `evals/routing/suite.json`
- [ ] Changed skills have their `VERSION` and `CHANGELOG.md` updated

## Notes for review

<!-- Anything deliberately left out, or a decision worth a second opinion. -->
