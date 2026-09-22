# Paired statistics and stability

Use this reference for real-host candidate-vs-baseline comparisons.

## Paired outcomes first

When candidate and baseline run on the same benchmark cases, preserve case identity and compare outcomes as pairs. Prefer an exact McNemar/binomial analysis of discordant pairs over treating the two pass rates as independent samples.

Record at minimum:

- same frozen rubric, benchmark, suite, host, model, harness, and reasoning configuration;
- per-case candidate and baseline outcome;
- candidate-only passes and baseline-only passes;
- exact two-sided p-value;
- pass-rate delta;
- predeclared alpha and minimum material effect.

A higher raw pass rate is not, by itself, evidence of a reliable improvement.

## Non-inferiority

Use a predeclared non-inferiority margin only when the product question genuinely permits a small quality loss in exchange for another benefit such as cost or latency. Never invent the margin after seeing results.

## Repeated-run stability

For stochastic hosts, retain repeated outcomes per case. Mark a case flaky when identical frozen inputs produce both pass and fail outcomes across the required attempts. DEEP real-host promotion requires `STABLE` evidence; a materially flaky candidate is a trade-off or insufficient evidence, not an unconditional improvement.

## Sequential stopping

If cost requires early stopping, predeclare checkpoints before execution. Use an alpha-spending rule at those checkpoints; do not continuously peek at p-values and stop when the result becomes favorable.

When suite tooling is available, use:

- `tooling/paired_significance.py`
- `tooling/flakiness_analyzer.py`
- `tooling/sequential_stop.py`

These helpers support the evidence contract but do not replace judgment about benchmark representativeness or product materiality.
