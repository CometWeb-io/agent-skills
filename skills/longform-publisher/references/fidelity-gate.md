# Post-edit fidelity gate

Run this after `ai-humanize`, strong/deep rewrite, translation with substantive re-expression, or another edit that could change meaning.

The gate is not a style review. It verifies that the edited manuscript still expresses the admitted claim state.

Protect at minimum when material:

- names and organizations;
- numbers, percentages, currencies, units and thresholds;
- dates, versions and time windows;
- URLs, citations, identifiers and quoted text;
- negation and modality (`may`, `must`, `cannot`, `likely`, etc.);
- scope markers (`only`, `all`, `some`, geography/population/product scope);
- attribution and causal direction;
- user-designated exact wording.

Record substantial edits in `edit_history[]`. Set `fidelity.required=true` and promote to `MASTER_LOCKED` only after `fidelity.passed=true` with a check timestamp/evidence.

If an edit changes `may` to `will`, removes a protected number such as `37%`, drops a required citation, or changes a protected date, fail the gate until reconciled.
