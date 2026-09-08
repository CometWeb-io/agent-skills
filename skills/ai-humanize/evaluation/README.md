# Evaluation

The v2.4 bundle separates three kinds of evaluation instead of treating them as one score.

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

The scorer verifies hard tokens and unsupported-certification strings. Manual review is still required for causality, attribution, scope, role binding, voice fit, and source-instruction boundaries.

## Historical style-catalog calibration

Earlier versions referenced human-writing corpora used to calibrate the EN/PL catalogs. Those corpora and their immutable source manifest are not bundled here, so historical percentages/AUC are calibration notes only, not reproducible benchmark claims.

A future publishable benchmark should include source manifests, immutable hashes, sampling/labeling rules, exact scoring code, model/runtime versions, and fixed evaluation prompts before reporting new metrics.
