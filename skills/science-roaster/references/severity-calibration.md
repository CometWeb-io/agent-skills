# Science severity calibration

Severity measures damage to the scientific inference, not reviewer annoyance or reporting style.

## FATAL

Admit only when the central inference cannot remain as stated without reanalysis, new data, redesign, or a materially narrower claim. Require:

- at least one linked central claim;
- evidence strength STRONG or MODERATE;
- scope sensitivity LOW or MEDIUM;
- non-low confidence;
- explicit central-claim impact;
- repair level REANALYSIS, NEW_DATA, or REDESIGN;
- a surviving Challenger -> Defender -> Arbiter pass.

A FATAL finding cannot rest solely on `NOT_REPORTED` evidence.

Examples: the reference measure cannot identify the target construct and the central validation claim depends on it; the analysis leaks the holdout into model selection and the claimed generalization result depends on that holdout; the study design cannot identify the claimed causal effect.

## MAJOR

Use when a key claim may survive but its interpretation, uncertainty, validity domain, analysis, or scope requires substantial repair.

Examples: unmodeled dependence materially changes uncertainty; the analysis population differs from the population named in the claim; the strongest result is exploratory but written as confirmatory; the comparator or robustness result materially weakens the headline claim.

## MINOR

Use for local reporting, clarity, reproducibility, or robustness issues that do not materially change the central inference.

Examples: incomplete parameter reporting with recoverable code, local figure ambiguity, missing rationale for a secondary analysis.

## Downgrade tests

Downgrade when:

- the criticism assumes an inferential claim the manuscript does not make;
- the issue is reporting-only and the underlying procedure is otherwise evidenced;
- the challenged analysis is explicitly exploratory and not used to support a confirmatory conclusion;
- a supplied supplement, protocol, or code artifact directly answers the concern;
- the effect concerns a local secondary claim rather than the central inference.

## Stop condition

If the review lacks the manuscript section, supplement, analysis, or source needed to distinguish `NOT_REPORTED` from an actual methodological failure, do not convert uncertainty into a FATAL conclusion. Use `INSUFFICIENT_EVIDENCE`, a verification queue, or a narrower finding.
