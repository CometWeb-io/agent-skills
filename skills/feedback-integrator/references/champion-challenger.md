# Champion/challenger promotion

Do not promote a skill change because one example looks better. Compare the challenger against a frozen baseline corpus, repeat stochastic runs where applicable, require at least one repeatable improvement, and permit zero known regressions in protected invariants. Any safety/evidence regression is HOLD. Record the evaluated host/model scope rather than generalizing beyond it.

`kernel.promotion` (eval cases with `"operation": "promotion"`) checks this
payload:

```text
baseline_version                    # required, different from challenger_version
challenger_version
frozen_case_count                   # positive integer
repeated_runs                       # integer, at least 2
improvements                        # non-negative integer; at least 1 to promote
regressions                         # non-negative integer; any regression is HOLD
safety_regression?: true|false      # true is HOLD
evaluation_scope                    # the evaluated host/model scope
```

It returns `{status: PROMOTE|HOLD|INVALID, errors[], reason}`.
