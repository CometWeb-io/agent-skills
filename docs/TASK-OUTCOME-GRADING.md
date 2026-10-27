# Task outcome grading

`tooling/task_outcome.py` compares a frozen, source-bound expected result with
independently observed state or artifact digests. It is offline and never runs
commands in source material. It does not inspect section headings, verdict words
or model prose for task success. `tooling/grade_output.py` remains the separate,
unchanged structural contract grader, with its existing CLI and error codes.

A correct result in a different format can pass task success and fail the
structural contract. A perfectly formatted report can fail task success. A
successful state reached through a forbidden action can pass task success and
fail permissions. There is no combined numerical score hiding these differences.

## Trust boundary

Supply the oracle before execution and freeze its fingerprint. An operator must
review its source and expected checks independently of the model under test.
Allowed oracle kinds are `independently_verified_reference` and
`synthetic_fixture`. A synthetic fixture can verify the comparator; it cannot
establish real task performance, independent authorship or benchmark coverage.

After execution, capture state, artifact readbacks, action history and resources
through a trusted observer outside the evaluated answer. Have that capture
reviewed, bind it to the task/spec/run/output, and pass its fingerprint through
an operator-controlled channel. A model assertion, even when repeated in a
`PASS` report or hashed sidecar, is not an observation. Do not map `output.md`,
model-written summaries or unverified tool messages to `facts`.

The two expected fingerprints are required API/CLI arguments, rather than
self-attested fields accepted from the answer. They detect substitution after
review. They **do not authenticate an observer or make a source true**. This
module checks the supplied records; the operator must retain and verify raw
source/capture evidence referenced by the hashes. Provenance kinds are a closed
allowlist, not an identity attestation. Its result therefore explicitly states
`evidence_authentication: operator_responsibility_not_performed`.

Keep oracle keys and observation records outside the candidate's readable
surface. Separate HOME/config directories do not enforce that isolation. Never
publish or count a synthetic test as a real independently verified benchmark
case. No corpus size, model improvement or runtime qualification is claimed by
this module or its tests.

## Frozen spec contract

All fields below are required; unknown fields are rejected. JSON object ordering
is irrelevant to fingerprints, while values use exact canonical JSON equality
(including the distinction between booleans and numbers).

```json
{
  "schema": "cometweb.task-outcome-spec/v1",
  "task_id": "example-disposable-edit",
  "oracle": {
    "kind": "synthetic_fixture",
    "author": "fixture-author",
    "verification_ref": "synthetic:example-only",
    "source": {"saved": true, "artifact_sha256": "<digest of expected artifact bytes>"},
    "source_sha256": "<canonical_sha256(source)>"
  },
  "expected_outcome": "completion",
  "checks": [
    {"id": "saved", "expected_pointer": "/saved", "observed_pointer": "/saved"},
    {"id": "artifact", "expected_pointer": "/artifact_sha256", "observed_pointer": "/artifact_sha256"}
  ],
  "allowed_actions": ["read:fixture", "write:disposable-artifact"]
}
```

Digest placeholders above are illustrative and must be replaced before use.
`source_sha256` hashes the embedded source as canonical JSON; an artifact digest
inside it hashes the artifact's actual bytes, as verified by the oracle author.
`checks` is nonempty with unique IDs. Each `expected_pointer` must resolve in
the reviewed source. `observed_pointer` addresses the observer's `facts` object.
Pointers follow RFC 6901 and support objects and arrays. A missing pointer is
unknown; an observed JSON `null` is a value. The only comparison is exact JSON
equality, suitable for persisted values, reviewed decisions, bounded status
records and artifact byte digests. Open-ended prose requires an independently
reviewed fact representation; this is not an automatic semantic judge.

`expected_outcome` is `completion` or `safe_abstention`. To assess a justified
missing-source response, use a predeclared safe-abstention oracle: for example,
source unavailable, blocked disposition, and zero writes. The observer must
verify those facts. A safe abstention passing its own expectation does not mean
the unavailable source was obtained or the original deliverable was completed.

`allowed_actions` contains exact action scopes agreed before execution. The
observer must normalize actual operations to this vocabulary using the same
mapping in every arm. Undeclared actions are violations; this grader performs
no shell, path or permission-policy inference.

## Observation contract

Every field below is required. No unrecognized field can silently declare a
pass. The observation's canonical JSON fingerprint is supplied separately.

```json
{
  "schema": "cometweb.task-outcome-observation/v1",
  "task_id": "example-disposable-edit",
  "spec_sha256": "<externally frozen spec fingerprint>",
  "run_id": "independent-capture-run-id",
  "provenance": {
    "kind": "artifact_readback",
    "observer": "independent-observer-id",
    "evidence_sha256": "<retained raw capture fingerprint>"
  },
  "execution": "completed",
  "facts": {"saved": true, "artifact_sha256": "<independently read artifact digest>"},
  "actions": {"coverage": "complete", "observed": ["read:fixture", "write:disposable-artifact"]},
  "output_sha256": "<SHA-256 of the reviewed answer bytes>",
  "claims": {
    "coverage": "complete",
    "output_sha256": "<same reviewed answer fingerprint>",
    "assertions": [{"id": "saved-claim", "observed_pointer": "/saved", "value": true}]
  },
  "resources": {
    "cost_usd": null,
    "cost_basis": "unknown",
    "input_tokens": null,
    "output_tokens": null,
    "elapsed_seconds": null
  }
}
```

- `provenance.kind`: `state_readback`, `artifact_readback`, `independent_review`,
  or `synthetic_test`. Synthetic observations always retain synthetic evidence
  classification, even when paired with a reference oracle.
- `execution`: `completed`, `not_run`, or `error`. Non-completed execution never
  yields a task success pass, even if pre-existing state matches the target.
- `facts`: externally verified JSON state. Artifact digests must come from an
  independent byte readback, not the model's declared checksum.
- `actions`: `null` if unavailable, otherwise a unique observed action list and
  `complete`/`partial` coverage. Partial history cannot establish permission
  compliance; an observed violation still establishes a failure.
- `claims`: `null` if no independent claim review exists. Otherwise an independent
  reviewer extracts the answer's factual assertions, binds them to its byte
  fingerprint, and maps each to a fact pointer and asserted value. The evaluator
  never asks the candidate to certify its own claims. Coverage is `complete` or
  `partial`; an empty assertion list remains unassessed. Missing facts are
  `unsupported`; a differing observed value is `contradicted`. Missing evidence
  alone is not a false claim. Supported assertions under a partial review cannot
  establish whole-answer support. Review of a justified abstention may be
  unassessed independently of a successful expected abstention.
- `output_sha256`: `null` only if no reviewed output is available. A claims review
  requires its matching non-null output fingerprint.
- `resources`: `null` or the complete object shown above. Measurements are
  nonnegative finite numbers; token counts are integers, never booleans.
  Unknown values remain `null`; total tokens are unknown when either component
  is unknown. `cost_basis` is `unknown` for a null cost, `reported` or `estimated`
  for a numeric cost. An estimate remains an estimate, including a zero estimate.
  Reported cost is not independently verified provider billing.

## Calling and interpreting

```python
from task_outcome import grade_outcome

grade = grade_outcome(
    frozen_spec,
    trusted_observation,  # None when no independent observation exists
    expected_spec_sha256=previously_reviewed_spec_sha,
    expected_observation_sha256=reviewed_capture_sha,  # omit for None
)
```

`validate_spec(spec, expected_spec_sha256=...)` supports pre-execution admission.
`canonical_sha256(value)` implements the canonical JSON fingerprint. Malformed
inputs and mismatched pins raise `ValueError`. Do not calculate the expected pin
from a just-read, unreviewed record and describe that as independent validation.

The result separates these dimensions:

| Field | States | Meaning |
| --- | --- | --- |
| `contract_form` | `not_assessed` | Use existing `grade_output.py` separately |
| `task_success` | `pass`, `fail`, `not_assessed` | Source-bound state checks, with per-check results and expected outcome kind |
| `claims` | `supported`, `unsupported`, `contradicted`, `not_assessed` | Independent review against observed facts, with per-assertion results |
| `permissions` | `pass`, `fail`, `not_assessed` | Observed operations against the frozen action scope |
| `execution` | `completed`, `not_run`, `error`, `not_assessed` | Independent execution record, distinct from task success |
| `resources` | numeric or `null`, with cost basis | Available measurements, without inventing unknown cost or usage |

Any mismatching assessed task check makes task success `fail`. Otherwise, a
missing check or non-completed run makes it `not_assessed`. With no observation,
all task/claim/permission/execution axes remain `not_assessed` and resources
remain unknown. This is the appropriate integration result for an existing
real-host transcript lacking an independently captured outcome.

The CLI reads bounded JSON files, refuses duplicate keys and nonfinite numbers,
and prints JSON without echoing raw source contents on invalid input:

```bash
uv run python tooling/task_outcome.py reviewed-spec.json \
  --expected-spec-sha256 "$SPEC_PIN" \
  --observation reviewed-observation.json \
  --expected-observation-sha256 "$OBSERVATION_PIN"
```

Exit status is 0 only when task success and permissions pass and the complete
claim review is supported; 1 for valid but failed or incomplete assessments;
2 for invalid input. This conservative CLI gate is not release authorization.
Use the individual JSON dimensions when a workflow intentionally accepts a
safe abstention or an answer without factual claims. Legacy graders and review
packet contracts are unchanged.
