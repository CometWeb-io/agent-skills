# Evaluation contract

Optimize for **high-precision editorial defects and repair value**.

## Invariants

- BLOCKER/MAJOR requires precise locator, impact, and structured evidence.
- Evidence must declare `kind: OBSERVATION|EXTERNAL|INFERENCE` plus source and locator.
- Taste/style alone cannot become material severity unless it violates the brief.
- BLOCKER must actually block an acceptance condition.
- Duplicate/invalid finding IDs fail closed.
- Suspicion about truth remains VERIFY/INFERENCE, not an asserted falsehood.

## Golden cases

Cover valid major, material finding without evidence, malformed evidence, style-only inflation, blocker without acceptance impact, duplicate IDs, minor/note without unnecessary ceremony, and malformed ledgers.

## Champion/challenger metrics

Measure material-defect precision, material-defect recall against a frozen expert ledger, false-positive severity rate, repair usefulness, finding deduplication quality, and verbosity. Never optimize for number of findings.

Run `python3 scripts/run_evals.py` plus release hardening gates when modifying the package.
