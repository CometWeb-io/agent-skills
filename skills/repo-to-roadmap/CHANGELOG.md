# Changelog

## Unreleased

- Kernel 2.0.1: enforce raw file inventory/review bundles in EXHAUSTIVE roadmap validation, including every pinned repository and assessment-time consistency.
- Add an optional independently pinned assessment contract; distinguish complete inspection records from approved exclusions, gaps and malformed proof.
- Bind file-review changes to snapshots/deltas; reject mismatched supplied snapshot hashes and revalidate on scope changes or unresolved file coverage.
- Suppress execution waves/orders on invalid dependency graphs; add opt-in --require-valid exit policy for validate and graph with strict bounded JSON parsing.
- Fix canonical test helper naming so pytest does not count a dictionary-producing fixture as a passing test. Existing test assertions are retained.

- Add read-only pinned Git inventory, cryptographic recursive-tree completeness checks, explicit file review accounting and inventory deltas.
- Preserve unread, excluded, binary, symlink and unexpanded-submodule distinctions. A generated ledger contains no completed reviews.
- Route exhaustive assessment to the new file-accounting sidecar without replacing domain coverage, claim validation or the roadmap kernel.
- Tests exercise local Git fixtures and supplied review records, not host/model acceptance or a full repository audit. Package VERSION and registry are unchanged.

## 1.0.0

- Initial public release in CometWeb Agent Skills.
