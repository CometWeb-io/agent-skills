# Longform Publisher 1.0.0 — real-world acceptance

Status: **FROZEN**

Acceptance date: 2026-09-11 (Europe/Warsaw)

## Scenario

A full `REFRESH` run rebuilt an existing ebook into an updated 2026 release candidate using Longform Publisher 1.0.0 on High reasoning.

The run completed the required deterministic publication workflow:

`validate -> check-manuscript -> check-derived -> render-manifest -> check-brief`

All required gates returned `OK`.

Final publication state: `RELEASE_READY`.

The run correctly did **not** mark the publication as `PUBLISHED` because no publication evidence existed.

## Produced artifacts

- canonical `manuscript.md`
- derived DOCX
- derived PDF
- `publication-report.json`
- publication brief / manifest

Canonical manuscript hash reported by the run:

`48e2780646f16181710b5c8f4cf741ee2f78a0f01d35512de779f587de39ea32`

Unresolved issues blocking `RELEASE_READY`: none reported.

## Freeze rationale

This real-world run exercises the important v1.0 control-plane behavior together: REFRESH mode, source/evidence handling, canonical manuscript ownership, derived-artifact lineage, format QA, release-stage discipline, and the distinction between `RELEASE_READY` and `PUBLISHED`.

Longform Publisher 1.0.0 is therefore treated as a frozen baseline. Future changes should require a concrete regression, contract change, or explicitly designed feature rather than speculative hardening.

## Evidence boundary

This acceptance record captures the run result supplied by the operator. It does not independently re-audit the final manuscript, DOCX, PDF, or publication-report contents inside this repository.
