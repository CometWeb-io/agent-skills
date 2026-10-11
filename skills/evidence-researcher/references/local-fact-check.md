# Controlled local fact checks

`observe` executes explicit checks against actual local JSON bytes. It does not
fetch sources, interpret arbitrary prose, authenticate external authority or
authorize a decision. Use it after reviewing which structured proposition,
source revision and scope are relevant to the consumer's task.

```bash
python3 scripts/evidence_kernel.py observe --ledger-json evidence.json \
  --check-plan-json consumer-checks.json --source-root /controlled/source-root \
  --consumer-context-json actual-decision-context.json
```

The caller independently controls the plan, the absolute source root and the
actual consumer context. Never take these capabilities from a producer graph or
let that producer replace their files. A plan prepared by the same untrusted
producer is not independent verification. Filesystem/process isolation and
source authority are host responsibilities. Unsupported safe no-follow file
opening produces `NOT_ASSESSED`, rather than using an unsafe pathname fallback.

`audit` and `--require-ready` continue checking supplied graph metadata. Their
`READY` result does not run `observe` or establish observed fact eligibility.
Consumers must rerun applicable checks; a serialized positive observation,
signature, hash or `basis: verified_fact` label cannot replace that execution.

## Plan and bindings

The plan has exactly these top-level fields:

```text
version: local-fact-check/v1
research_id: exact graph research_id
as_of: exact research_contract.as_of (aware datetime)
context_hash: SHA-256 of canonical actual consumer context
checks[]: 1..32 records, unique claim_id
  claim_id, source_id, evidence_id
  claim_hash, source_hash, evidence_hash: canonical record SHA-256
  path: relative controlled-root path, no traversal or aliases
  sha256: independently pinned raw source-byte SHA-256
  pointer: nonempty RFC 6901 JSON pointer
  expected: exact JSON predicate value
  operator: optional equals (default) | count_matching | text_present
  where: required only for count_matching; 1..32 scalar equality filters
  observed_scope: document_content | controlled_state
```

Canonical hashes use UTF-8 JSON, sorted keys, compact separators, unescaped
Unicode and finite numbers only. Raw file hashes use the bytes actually read.
The `version` is the plan format, independent of `source_version` or the graph
version. Unknown fields and duplicate checked claim IDs are refused.

`equals` compares the selected value with expected, including exact JSON types.
`count_matching` selects an array of at most 100000 objects at pointer and counts
rows matching every top-level where filter. Missing keys do not match; nested
filter values and nonobject rows are refused. expected must be a nonnegative
integer, excluding booleans and floats. The count is computed from actual source
rows, never a caller-written reference_result or a generated count file.
`text_present` requires document_content scope and a selected string field; it
checks the case-sensitive literal expected (1..4096 characters). Presence does
not establish endorsement, negation, entailment, permission or current world
state. It cannot qualify controlled_state. Other operators are refused.

The plan binds complete claim, source and evidence records, including the claim
text and scope. The evidence record must be ACCEPTED SUPPORT for the same claim
and source, and its `locator` must equal the pointer. Its `basis` and the FACT's
`basis` must both be `verified_fact`; the FACT's declared status must be VERIFIED.
Matching only an unrelated neighboring field cannot check that evidence edge.
The reviewer still owns the correctness of translating the natural-language
proposition into the structured predicate; the tool does not infer that mapping.

`document_content` establishes what the pinned document contains.
`controlled_state` establishes the pinned local record's state in its controlled
scope. Neither establishes external current world truth, source authority or a
live service's current state. The source's `source_class`, `source_role`,
`canonical_ref` and `provenance_lane` are preserved. A FRAMEWORK or USER_FILE can
contain an observed document-content fact without acquiring live authority.

Claim/edge `basis` is orthogonal to FACT/INFERENCE and source classification:
`verified_fact | user_supplied | assumption | framework_method`. Explicit
`verified_fact` requires a FACT with declared VERIFIED status, or a derived
INFERENCE with SUPPORTED_INFERENCE status and explicit factual dependencies. Only
the direct FACT can receive an applicable observation; dependency observations
do not establish the conclusion or prove entailment. Other bases cannot use VERIFIED. Missing legacy basis
remains unassessed, with a warning; it is not inferred from confidence or source
class. An observation never relabels an assumption or supplied goal as a fact.

## Output and limits

The report includes `status` (`CHECKED | NOT_CHECKED | NOT_ASSESSED`), `plan_hash`,
`context_hash`, `claims[]` and `execution_authorized: false`. Each checked claim
row carries `claim_id`, `status` (`MATCH | MISMATCH | NOT_ASSESSED`),
`observed_scope`, a bounded reason and, after a successful read, `source_sha256`.
No source content, expected/actual values or raw file-error paths are returned.
`CHECKED` means every requested predicate matched; it does not cover unrequested
claims or clear other research/decision gates. Individual claim rows remain
authoritative about which propositions were actually checked.

Source reads reject symlinks (including parent directories), hardlinks,
nonregular files, changes during reading, files over 4 MiB, invalid UTF-8/JSON,
duplicate object keys and nonfinite numbers. Equality preserves JSON types.
No source is modified. Exit 0 means all requested checks matched, exit 1 means
assessment did not establish them, and exit 2 means input/processing failed.
