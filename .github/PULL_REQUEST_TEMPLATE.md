## What changes

<!-- One or two sentences. What behaviour is different after this PR? -->

## Why

<!-- The problem this solves. Link an issue if there is one. -->

## Checks

```
python3 tooling/validate_local.py --output .validation --timeout 900
```

- [ ] `report.json` says `passed` (every check green, nothing skipped)
- [ ] `./tooling/public-safety-check.sh` reports no findings
- [ ] Registry and packages agree — generated files regenerated, not hand-edited

## If behaviour changed

- [ ] A test or eval case fails without this change and passes with it
- [ ] Routing changes come with a case in `evals/routing/suite.json`
- [ ] Changed skills have their `VERSION` and `CHANGELOG.md` updated

## Notes for review

<!-- Anything deliberately left out, or a decision worth a second opinion. -->
