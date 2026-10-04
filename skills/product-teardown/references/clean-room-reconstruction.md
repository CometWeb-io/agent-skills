# Clean-room reconstruction

Use this extension when the source is an application, website, API, or
open-source product that the destination team wants to learn from or
reimplement.

## Boundary

Reconstruct observable behavior and the underlying problem, not the source's
identity. Preserve the destination's brand, terminology, design system,
architecture, data ownership, and legal obligations.

Allowed evidence can include:

- public documentation, pricing, changelogs, help content, and API contracts;
- user-visible flows, states, accessibility behavior, and error handling;
- source code that is explicitly licensed for reuse, with provenance recorded;
- the destination's own support, analytics, product, and repository evidence.

Do not copy source code, bundles, private endpoints, credentials, proprietary
data, distinctive copy, trademarks, assets, or trade dress unless the relevant
rights and provenance are explicitly verified. Public visibility is not
permission. A clean-room note is a process control, not legal clearance.

## Reconstruction map

Create a `cometweb.reconstruction-map/v1` JSON map before implementation. It
must identify:

1. the pinned source and destination;
2. source evidence with locators, claim state, and confidence;
3. stable screen/flow IDs and observed states;
4. features with `must`, `should`, or `could` priority;
5. deliberate scope cuts with a reason;
6. unknowns that can change implementation;
7. explicit prohibited material and the chosen transfer mode.

The map uses `allowed` and `prohibited` boundary lists, `default_transfer_mode`,
`screens`, `source_evidence_ids`, and `status` fields. Feature rows use
`scope_reason` for deliberate cuts; valid statuses include `done`, `partial`,
`missing`, and `skip`.

Use `scripts/validate_recon_map.py` before handing the map to architecture or
implementation. A valid map proves structure and boundary declarations only;
it does not prove that the source behavior, rights, or destination need are
true.

## Feature matrix

Use `scripts/feature_matrix.py` to score only a validated matrix. Weights are
`must=3`, `should=2`, and `could=1`; `partial` receives half credit. A
deliberate `skip` is excluded from the denominator only when it has a
non-empty scope reason. Missing source or destination evidence cannot be
silently treated as complete.

The matrix is a sequencing aid, not a release verdict. Pair it with browser
QA, accessibility checks, security review, and the destination's own
acceptance criteria.

## Required transfer discipline

For each adopted pattern, preserve:

`source evidence -> observed mechanism -> destination problem evidence ->
destination-native implementation -> validation -> rollback/kill condition`

If destination evidence is missing, keep the pattern `CANDIDATE` or
`EXPERIMENT`; do not promote it because the source looks successful.
