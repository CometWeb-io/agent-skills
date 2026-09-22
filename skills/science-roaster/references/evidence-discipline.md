# Science Roaster evidence discipline

## Evidence states

- `OBSERVED`: directly supported by the supplied scientific material.
- `NOT_REPORTED`: the source does not report the item required to assess a scientific question; include `what_cannot_be_assessed`.
- `INFERRED`: a bounded scientific interpretation derived from observed material; include `inference_basis`.
- `EXTERNAL_VERIFIED`: verified against external evidence and allowed only in `VERIFY_EXTERNAL` mode.

`NOT_REPORTED` is not evidence that a procedure was not performed.

## Evidence strength

- `STRONG`: direct evidence with clear relevance to the finding and limited inferential distance.
- `MODERATE`: credible but incomplete, indirect, or partially inferential evidence.
- `WEAK`: plausible concern with substantial uncertainty; cannot support FATAL.

## Scope sensitivity

- `LOW`: unseen material is unlikely to reverse the finding.
- `MEDIUM`: unseen material could narrow interpretation or severity.
- `HIGH`: unseen material could reasonably reverse the finding.

`HIGH` scope sensitivity cannot have high confidence. FATAL cannot use `HIGH` scope sensitivity.

## Inferential types

- `DESCRIPTIVE`
- `ASSOCIATIONAL`
- `PREDICTIVE`
- `CAUSAL`
- `MECHANISTIC`
- `TRANSPORT`

Do not silently upgrade one inferential type into another. A predictive association is not a mechanism; a between-group contrast is not automatically causal; a local validation does not automatically transport.

## Evidence roles

- `PRIMARY`
- `SECONDARY`
- `EXPLORATORY`
- `POST_HOC`
- `BACKGROUND`

The role affects what language the manuscript may responsibly use. Exploratory or post-hoc evidence can be valuable without becoming confirmatory.

## Validity domains

- `CONSTRUCT`: does the operationalization measure the intended construct?
- `INTERNAL`: do design and controls support the claimed within-study inference?
- `STATISTICAL`: do estimand, dependence, uncertainty, multiplicity, missingness, and analysis support the conclusion?
- `EXTERNAL`: does the claim extend beyond the observed population/setting without evidence?
- `REPRODUCIBILITY`: can the result be independently reconstructed or rerun from the reported assets?
- `REPORTING`: does missing reporting block assessment without proving underlying failure?

## Materiality

Each finding declares:

- `centrality`: `CENTRAL`, `SUPPORTING`, or `LOCAL`;
- `consequence`: `HIGH`, `MEDIUM`, or `LOW`;
- `reversibility`: `EASY`, `MODERATE`, `HARD`, or `UNKNOWN`.

FATAL generally requires `CENTRAL` + `HIGH` consequence and a repair burden beyond reporting-only.

## Fatality rules

A FATAL finding must:

- link to at least one central claim;
- explain `central_claim_impact`;
- use evidence strength `STRONG` or `MODERATE`;
- use scope sensitivity `LOW` or `MEDIUM`;
- have non-low confidence;
- require `REANALYSIS`, `NEW_DATA`, or `REDESIGN`;
- not rely solely on `NOT_REPORTED`.

If the paper cannot be assessed because key information is not reported, that can be MAJOR/blocked assessment but is not proof that the underlying study failed.

## Source lineage

Every structured claim/finding anchor must include `source_id` referencing `source_manifest`. This keeps evidence traceable when multiple artifacts, revisions, supplements, logs, or repository snapshots are reviewed together. A locator without source identity is not sufficient for machine handoff.
