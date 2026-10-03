# Repair contract

The fields, enums and closure rules for one repair item are defined once, in
`references/output-contract.md`. This file explains how to fill the fields that
need judgment.

- `root_cause`: the one underlying defect the change addresses, stated so a
  reviewer can check it against the findings it groups. Correlated symptoms
  share a repair only when one change can resolve them.
- `depends_on`: the `repair_id`s that must land first. Sequence blockers and
  prerequisites before cosmetic work.
- `done_when`: the observable condition that closes the finding, written before
  the change is made.
- `verification_evidence`: fresh evidence for the current candidate only. A
  check run against a different build or version closes nothing here.
- `decision_source`: who decided a `WONT_FIX`, why, and when; in strict or DEEP
  work, also when the decision expires and must be revisited.

Preserve every source finding ID through the ledger.
