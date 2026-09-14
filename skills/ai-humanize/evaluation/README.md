# Evaluation

The v2.4.1 integration candidate separates three kinds of evaluation instead of treating them as one score.

## 1. Deterministic regression

Run:

```bash
python -m unittest discover -s tests -v
```

This covers Unicode hygiene, Markdown/code preservation, CLI check mode, hard rewrite invariants, and semantic-risk warnings.

## 2. Bundle release lint

Run:

```bash
python scripts/release_check.py
```

This validates the ChatGPT-facing frontmatter shape, local file references, few-shot examples, hard invariant preservation in examples, red-team manifest structure, and the unit suite.

## 3. Behavioral red team

Read `redteam-protocol.md` and use `redteam-cases.json` against an actual model/runtime using the skill. Saved outputs can be checked with:

```bash
python scripts/redteam_score.py evaluation/outputs
```

The scorer checks hard tokens and flags potentially unsupported certification strings. Flags can also match legitimate quotations or negated statements; they require review, not an automatic accusation. Manual review is still required for causality, attribution, scope, role binding, voice fit, and source-instruction boundaries.

Exit codes and per-case states:

| Exit | Meaning |
|---|---|
| `0` | All saved outputs meet the automated checks; manual review is still pending. |
| `1` | At least one output is missing/invalid or requires review. |
| `2` | Invalid manifest/directory or an incomplete operation. No valid overall result. |

The per-case states are `automated_pass`, `review`, `missing_output` and `invalid_output`. The former `pass` state is deliberately not emitted. Semantic-risk warnings from the guard lead to `review`, even when `guard_passed` is true. The guard itself continues to report hard-token checks separately from semantic heuristics for backwards compatibility.

Keep one UTF-8 `<case-id>.txt` output per declared case. Unknown `.txt` filenames, duplicate or unsafe case IDs, empty manifests and nonfinite JSON values are rejected. Empty, unreadable, oversized or symlinked output files do not count as a completed case. Include no credentials or customer data in test inputs.

The result records case/source/output SHA-256 fingerprints. These bind the report to supplied bytes; they do not authenticate their author, prove a model ran, or establish factual correctness. Reusing the input verbatim can pass automatic checks without being a good rewrite.

Numeric guards recognize the Unicode minus sign and literal number comparisons. They do not solve equations, prove inequalities written in words, or establish that a number is still attributed to the correct subject. Protected quotations/code remain exact-match controlled.

## Historical style-catalog calibration

Earlier versions referenced human-writing corpora used to calibrate the EN/PL catalogs. Those corpora and their immutable source manifest are not bundled here, so historical percentages/AUC are calibration notes only, not reproducible benchmark claims.

A future publishable benchmark should include source manifests, immutable hashes, sampling/labeling rules, exact scoring code, model/runtime versions, and fixed evaluation prompts before reporting new metrics.
