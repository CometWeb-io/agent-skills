# Evaluation

The v2.4.1 integration candidate separates three kinds of evaluation instead of treating them as one score.

## 1. Deterministic regression

Run:

```bash
python3 -m unittest discover -s tests -v
```

This covers Unicode hygiene, Markdown/code preservation, CLI check mode, hard rewrite invariants, and semantic-risk warnings.

## 2. Bundle release lint

Run:

```bash
python3 scripts/release_check.py
```

This validates the ChatGPT-facing frontmatter shape, local file references, few-shot examples, hard invariant preservation in examples, red-team manifest structure, and the unit suite.

## 3. Behavioral red team

Read `redteam-protocol.md` and use `redteam-cases.json` against an actual model/runtime using the skill. Saved outputs can be checked with:

```bash
python3 scripts/redteam_score.py evaluation/outputs
```

The scorer checks hard tokens and flags potentially unsupported certification strings. Flags can also match legitimate quotations or negated statements; they require review, not an automatic accusation. Manual review is still required for causality, attribution, scope, role binding, voice fit, and source-instruction boundaries.

Exit codes and per-case states:

| Exit | Meaning |
|---|---|
| `0` | All saved outputs meet the automated checks; manual review is still pending. |
| `1` | At least one output is missing/invalid or requires review. |
| `2` | Invalid manifest/directory or an incomplete operation. No valid overall result. |

The per-case states are `automated_pass`, `review`, `missing_output` and `invalid_output`. The former `pass` state is deliberately not emitted. Semantic-risk warnings from the guard lead to `review`, even when `guard_passed` is true. The guard itself continues to report hard-token checks separately from semantic heuristics for backwards compatibility.

Each manifest case (`redteam-cases.json` is a JSON list of 1 to 1000 cases) has exactly these keys:

```text
id: unique, lowercase letters, digits, _ and -, at most 128 characters
language: en|pl
request: the instruction given to the model
mode_expectation: the rewrite depth a reviewer should expect, free text
source: the text to rewrite
manual_checks[]: at least one case-specific review criterion
protected[]: optional exact terms the output must keep
style_reference: optional voice sample; content from it must not enter the output
```

`release_check.py` loads the manifest through the scorer's own loader, so a case the scorer would reject fails the release gate too.

With `--json` the scorer prints one result per case:

```text
id, manual_checks: copied from the case
status: automated_pass|review|missing_output|invalid_output
manual_review: not_performed
semantic_equivalence: not_verified
claim_assessment: heuristic_only
source_sha256, case_sha256: fingerprints of the case
output_sha256: fingerprint of the saved output (scored cases only)
guard_passed: the strict rewrite_guard verdict
missing_invariants, added_invariants, semantic_risk_markers: the guard's findings
provenance_string_flags[]: unsupported-claim strings found in the output
```

Keep one UTF-8 `<case-id>.txt` output per declared case. Unknown `.txt` filenames, duplicate or unsafe case IDs, empty manifests and nonfinite JSON values are rejected. Empty, unreadable, oversized or symlinked output files do not count as a completed case. Include no credentials or customer data in test inputs.

The result records case/source/output SHA-256 fingerprints. These bind the report to supplied bytes; they do not authenticate their author, prove a model ran, or establish factual correctness. Reusing the input verbatim can pass automatic checks without being a good rewrite.

Numeric guards recognize the Unicode minus sign and literal number comparisons. They do not solve equations, prove inequalities written in words, or establish that a number is still attributed to the correct subject. Protected quotations/code remain exact-match controlled.

## Historical style-catalog calibration

Earlier versions referenced human-writing corpora used to calibrate the EN/PL catalogs. Those corpora and their immutable source manifest are not bundled here, so historical percentages/AUC are calibration notes only, not reproducible benchmark claims.

A future publishable benchmark should include source manifests, immutable hashes, sampling/labeling rules, exact scoring code, model/runtime versions, and fixed evaluation prompts before reporting new metrics.
