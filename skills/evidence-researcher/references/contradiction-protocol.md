# Contradiction and Falsification Protocol

## Objective

Actively try to falsify every critical/material claim. Support search and contradiction search are separate research operations.

## Minimum auditable requirement

For each critical/material claim, log at least one completed search/inspection record whose purpose is one of:

- `FALSIFIER`
- `RETRACTION`
- `VERSION`
- `NEGATIVE_CASE`
- `ABSENCE_TEST`

`contradiction_tested=true` without such a record is invalid.

## Falsifier patterns

Use one or more:

- negated proposition,
- alternate definition or terminology,
- negative/failure case,
- newer version/date/effective state,
- retraction/correction/erratum,
- regulator/maintainer disagreement,
- competing dataset/method,
- jurisdiction/population qualifier,
- critic/counterparty source,
- primary source behind disputed secondary reporting.

## Evidence of absence

A failed ordinary search is not evidence that something does not exist.

Use `ABSENCE_TEST` only when the search space and detection method make non-detection meaningful. Record:

- where absence was tested,
- expected location/index/system,
- coverage limitations,
- why a missing observation supports the proposition.

Otherwise label the result `UNKNOWN` or a gap.

## Classify disagreement

Use one type:

- `genuine_conflict`
- `definition_mismatch`
- `population_mismatch`
- `jurisdiction_mismatch`
- `version_mismatch`
- `time_mismatch`
- `method_mismatch`
- `authority_mismatch`
- `superseded_evidence`
- `derivative_duplication`
- `unknown`

## Resolution order

Do not resolve by source count. Evaluate:

1. controlling authority for the claim type,
2. directness,
3. scope fit,
4. temporal/version fit,
5. measurement quality,
6. independent corroboration.

Preserve credible minority evidence. Record what observation would change the synthesis.

## Blocking rule

- critical unresolved contradiction -> `BLOCKED_BY_CONTRADICTION`,
- material unresolved contradiction -> normally `PARTIAL`,
- resolved contradiction remains in the graph with explicit resolution basis.
