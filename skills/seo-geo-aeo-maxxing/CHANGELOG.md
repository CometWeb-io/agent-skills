# Changelog

## 1.2.2 — 2026-10-03

- `score_maxx.py` rejects a non-object audit and non-string pillar, surface, check id, verdict, profile or evidence class values with `ERROR:` and exit 1 instead of a traceback.
- `compare_scores.py` validates both score files (object shape, numeric scores and coverage, string ids and groups) and names the offending file and field instead of failing with a traceback.

## 1.2.1 — 2026-09-25

- Add a content-rewrite route to `references/composability.md`: which findings go to a writing skill, what to pass (priority question, failed extraction criteria, preserve list) and which findings need evidence work first.
- Clarify AEO-01: a labelled answer template is not required, a short hook before a prompt answer is fine, and an answer that loses its subject across a fragment is still a weakness.

## 1.2.0 — 2026-09-12

- Add scoped currentness, evidence, safety and domain acceptance contracts.
- Normalize host metadata and verify standalone package structure.
- Preserve the existing executable decision protocol and its fixtures; skill release version and protocol version remain separate.

## 1.1.0

- Added formal protocol/version metadata.
- Added explicit boundaries with Competitive Intelligence, Product Operator, Repo to Roadmap, Release Readiness, Evidence Researcher, and AI Council.
- Added `references/composability.md` with a lossless finding/evidence handoff contract.
- Clarified that VERSUS diagnosis is not ongoing competitor monitoring and that diagnostic results are not release authorization.
