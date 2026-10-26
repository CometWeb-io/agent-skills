# Requested audit depth and coverage

Default depth is `recon`: the named job, primary safe interactions, evidence,
cleanup and explicit limits. No exhaustive control inventory or JSON is required.
Use a larger depth only when requested; scope and permissions still bound it.

| Depth | Required coverage |
|---|---|
| `standard` | All primary actions, unique interaction/state patterns, form/validation classes and high-risk claims in scope; representative repeated low-risk instances |
| `forensic` | Every in-scope instance; no sampling |

For standard sampling, name the repeated pattern and representatives. Cover its
material state variants; a sample of one pattern does not cover another.
For unbounded forensic scope, establish a finite boundary or report incomplete.

Modes describe the selected target, not additional passes:

- `page`: one route and its owned dialogs.
- `area`: one bounded feature across screens.
- `crawl`: bounded navigation/templates; standard covers each of up to 15
  templates, otherwise primary destinations and a representative per template.
- `flow`: one user job with start, steps and observable terminal outcome.
- `data`: compare IDs, values, units, counts and state across the relevant views.
- `visual`: rendered facts; static-only completion applies only to a static brief.
- `regression`: requires a prior finding or explicit baseline to recheck.
- `a11y`: measured interaction/semantics and applicable criteria, not blanket compliance.
- `contract-trace`: explicitly requested cross-layer journey; read
  `references/contract-tracing.md` for its scenario and runtime-binding contract.

Coverage: `tested | sampled | policy-blocked | environment-blocked | unreachable`;
record out-of-scope notes separately. Incomplete required coverage stays incomplete
in downstream reports. Source/screenshot/fetch-only evidence cannot complete an
interaction-heavy standard/forensic audit unless the brief is explicitly static.
Use the verdict/count/schema mapping in `references/evidence-and-report.md`.
