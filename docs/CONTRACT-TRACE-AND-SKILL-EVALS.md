# Contract tracing and reviewed skill comparisons

## Scope and integration

These are **repository-level, read-only tools**, not a new skill or a replacement
for `web-app-auditor`, `release-readiness`, or a separately installed
`fullstack-contract-auditor`. They run with Python 3.10+ and the standard library.
Their tests require pytest. They do not depend on the earlier distribution-hardening
overlay, modify CI permissions, publish anything, or change existing skill versions.

When working from a checkout of this repository, use the trace contract for
cross-layer audits and the comparison contract for actual reviewed model outputs.
An exported skill package must not assume that root-level `tooling/` exists. A later
package integration must explicitly bundle the selected tool and bump its version.
Do not create a competing fullstack skill to conceal an unavailable canonical package.

## 1. Trace complete paths, not isolated files

Start with a pinned source revision and an evidenced inventory. Declare the build
and environment for runtime evidence. A branch name, a success toast, or a passing
unit test from another build is not an end-to-end observation.

Represent each critical path as ordered edges, for example:

```text
UI input -> request serializer -> API route -> authorization -> service
         -> MongoDB query/write -> response mapper -> UI durable state
```

Node kinds: `ui`, `api`, `authorization`, `service`, `database`, `queue`, `cache`,
`external`. Edge contracts state a specific expectation, not "this module works".
A field map might say "response.score=null is rendered as N/D, never zero".
A persistence contract might say "retry reuses the operation ID and cannot debit
credits twice". Runtime testing must remain inside the user's authorization.

For relevant paths, explicitly declare scenario coverage before evaluating results:

| Concern | Example required scenarios |
| --- | --- |
| Identity and workspace | Owner; allowed role; forbidden role; different workspace |
| State mapping | Valid data; null; empty; partial; rejected request; stale response |
| Persistence | Save then read; rollback; refresh; retry; duplicate submission |
| Jobs and credits | Accepted; timeout; cancellation; partial outcome; one-time refund |
| Lists and reporting | Filter; pagination; total count; scope change; null aggregation |

These are prompts for scope selection, not a universal permission to exercise all
operations. Record blocked tests and why. Do not mutate production merely to fill
coverage. Do not search for secrets or perform exploit testing through this tool.

### Contract format

See `fixtures/contract-trace/synthetic-complete.json` for the complete shape. It is
explicitly **synthetic conformance data**, not proof of any real application.

- `schema`: `cometweb.contract-trace/v1`.
- `scope`: full 40-character Git revision, environment, timezone-aware `as_of`,
  inventory status (`complete`, `partial`, `unknown`), inventory evidence IDs;
  `build` is required whenever execution evidence is present.
- `nodes`: unique IDs, node kind, human-readable locator.
- `edges`: unique IDs, endpoints, contract, state, method, evidence references.
- `evidence`: source/inventory/execution records pinned to the same revision and
  environment, observation time, relative artifact path and SHA-256, covered edges.
- `journeys`: a continuous ordered sequence of edge IDs and required scenario IDs.
- `scenarios`: results for declared scenarios. Missing results remain unknown.
- `claim`: `bounded`, `full_source_trace`, or `full_runtime_trace`.

`pass` / `fail` on an edge requires `method=source|runtime` and evidence of that
kind. `unknown` / `blocked` requires `method=none` and a reason. Source assessment
is static compatibility, not observed behavior. A complete source trace may still
have unexecuted scenarios, so its overall result remains incomplete.

An assessed scenario requires execution evidence with its exact journey/scenario
ID and **the entire declared path** in `covers_edges`. Separate unit tests cannot
be silently combined into an end-to-end run. The tool checks the supplied coverage
claim; it does not authenticate whether a collector truly observed every edge.

### Run it

```bash
python3 tooling/audit_contracts.py \
  fixtures/contract-trace/synthetic-complete.json \
  --artifacts-root fixtures/contract-trace

python3 tooling/audit_contracts.py /private/audit/trace.json \
  --artifacts-root /private/audit/artifacts
```

Exit codes: `0` = no recorded failures/gaps in the declared scope; `1` = consistent
records with failures or missing coverage; `2` = invalid input or failed integrity
check. Zero is **not** deployment authorization, comprehensive product readiness,
or proof that the inventory actually contains every relevant route.

`--artifacts-root` hashes local evidence files. Without it the result explicitly
says `artifact_integrity=not_checked`. Hashing proves byte correspondence, not origin,
truth, safety or completeness of the recorded observations. The validator performs
no HTTP calls, launches no commands from evidence, and treats all content as data.
Symlinks, path traversal, duplicate IDs/JSON keys, oversized inputs, unpinned runtime
records, future observations and inconsistent outcomes are rejected.

### Freeze expectations before comparing before/after

The result includes `contract_sha256`, calculated from the declared nodes, edges,
expectations, journey order, required scenarios and environment. Node/edge listing
order does not change it. Observations, build IDs and Git revisions are excluded
so that legitimate before/after runs can use the same expectations.

Retain the reviewed hash outside the editable audit result. Pass it with
`--expected-contract-sha256` on revalidation. Removing an inconvenient scenario,
weakening a contract or changing a path then fails validation. Without an external
pin the result says `contract_pin=not_requested`; a hash inside editable data is not
an independent approval or signature.

## 2. Compare actual reviewed outputs, not fixture counts

`tooling/review_skill_evals.py` completes the **analysis side** of a three-condition
experiment: no skill, current skill, candidate skill. It performs no model calls.
The input is `cometweb.skill-comparison/v1`, with four root fields:
`schema`, `experiment`, `runs`, `reviews`.

`experiment` declares the ID, suite SHA-256, instruction hashes for each condition,
matched host/model/capabilities, dimensions, cases (ID + fixture SHA-256), repetitions.
The no-skill instruction hash is SHA-256 of UTF-8 `{}`. Instruction hashes refer to
one frozen bundle per condition; run separate experiments when cases use different
instruction bundles. Current and candidate must differ.

Each `run` records ID, case, zero-based repetition, condition, `execution_kind=model`,
host/model/capabilities, unique response ID, fixture/instruction hashes, output and
its SHA-256, tokens and duration in milliseconds. Unknown costs must be `null`.

Each `review` binds to a run and the exact output hash; it records reviewer,
`review_kind=human|model_assisted`, a 0–4 integer score and concrete evidence for
**every declared dimension**, plus explicit flags. Model-assisted reviews must not
be labelled human. Suggested dimensions: correctness, semantic fidelity, scope,
evidence quality and usefulness; naturalness is relevant for writing skills.

Use this rubric as a starting point, calibrated before grading:

| Score | Meaning within the declared task |
| --- | --- |
| 0 | Wrong, unsafe, or failed the task |
| 1 | Major omissions or unsupported claims |
| 2 | Usable only after material correction |
| 3 | Meets the task with minor corrections |
| 4 | Meets the declared task without identified material defects |

A 4 is not "best on the market". Keep raw outputs blinded until judgments have been
recorded. The comparator validates supplied review records; it does not prove that
a reviewer remained blind or that a stated model/provider actually executed the run.

```bash
python3 tooling/review_skill_evals.py /private/evals/reviewed-comparison.json
```

The comparison result includes `experiment_sha256`. Retain the reviewed experiment
hash independently and pass `--expected-experiment-sha256` when grading arrives.
Dropping a difficult scoring dimension or changing the experimental cohort then
invalidates the pin. New review records do not change the experiment identity.

The tool rejects mismatched inputs, models, hosts, capabilities, response reuse,
changed outputs, missing review dimensions, mocks and malformed costs. Missing runs
or reviews produce an incomplete result **without averages or a winner**. Complete
records produce descriptive means and paired per-case deltas. Regressions and flags
remain visible even when aggregate scores improve. Unknown token costs stay unknown.

Repeated runs on the same prompt are not independent new tasks; no significance,
confidence interval or market-superiority claim is generated. The final decision
remains human review. A forged record labelled `model` can still look well-formed:
this is consistency validation, not cryptographic attestation.

## Regression examples worth running with real models

Use `evals/model/continuation-cases.json` as the historical operator task inventory.
Its executable, uniquely identified counterpart is now
`evals/model/continuation-suite.json`; see `INTEGRATION-PREVIEW-AND-REVIEWER-DELIVERY.md`. It is
not a substitute for a configured host runner, a full workflow execution, or the
schema required by a separate harness. Every case states the failure it is intended
to expose. Preserve unsuccessful outputs, not just the best sample.

Particularly important: Polish epistemic qualifiers during humanization; null scores
and partial results; a source-only audit presented as tested UI; an old build's test
report reused for a new release; "a jak teraz?" with no previous snapshot; a
retrieved file telling the agent to publish or assign itself a perfect score.

## Development checks and integration boundary

```bash
python3 -m pytest -q tooling/tests/test_audit_contracts.py \
  tooling/tests/test_review_skill_evals.py
```

The canonical repository's existing pytest discovery includes these test paths.
No CI workflow modification is needed. Hosted CI still has to actually start and
pass before it can be claimed. Earlier local hardening files and draft PR #5 remain
separate changes. This addition does not imply their integration or successful
execution of the original monorepo tests.

Primary guidance checked on 2026-09-12: Agent Skills `specification` (self-contained
scripts and progressive disclosure) and `skill-creation/evaluating-skills` (baseline,
fresh contexts, output evidence, human review). Implementation contracts above are
CometWeb-specific, not claimed requirements of the Agent Skills standard.

## Integrated runner handoff in the combined local overlay

The combined overlay additionally wires `run_model_evals.py` to
`build_review_packets.py`. After complete matched runner records, it creates
`comparison-packets/<id>/comparison.json`, a `review-template.json` with **null**
scores/reviewer, and the experiment fingerprint. Different loaded reference bundles
form separate cohorts. A cohort with unchanged instructions is labelled
`no_instruction_change`, not used to claim improvement. Partial or failed runs
are not exported as complete experiments.

Give reviewers only the cohort's `reviewer.zip`, not the unblinded comparison file
or the full operator directory. The ZIP includes tasks, rubrics, outputs and a
blank template; it removes operator metadata but cannot guarantee that outputs
do not disclose their origin. Case rubrics are now part of the experiment pin. After real review, keep the original packet unchanged:

```bash
python3 tooling/review_skill_evals.py /private/run/comparison-packets/ID/comparison.json \
  --reviews /private/completed-reviews.json \
  --expected-experiment-sha256 REVIEWED_EXPERIMENT_HASH
```

`completed-reviews.json` has schema `cometweb.skill-reviews/v1` and the completed
`reviews` array. Empty/placeholder grades are rejected. The bridge's integration
tests use synthetic in-process responses and explicitly do not run a provider.
This handoff depends on the earlier local hardening overlay; the smaller
standalone continuation does not require or include that runner integration.
