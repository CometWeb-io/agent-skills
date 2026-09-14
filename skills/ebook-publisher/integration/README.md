# Proposed integration only

`registry-entry.json` is a candidate entry, not an active registry. Its `lifecycle: active`
is the intended value after reviewed integration, not evidence of installation. See
`references/integration.md` for boundaries and repository precautions. The skill package
can be loaded explicitly by reading SKILL.md before repository-wide routing is integrated.

Positive and negative routing/behaviour scenarios are in `evaluation/cases.json`; they
are not a replacement for the repository's current routing harness. `eval_suite` remains
null until that harness has a compatible, actually integrated suite. Do not invent a path
that a harness will treat as already evaluated. No generated host adapters are shipped.
