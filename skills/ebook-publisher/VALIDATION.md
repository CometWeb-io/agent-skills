# Local package validation — 2026-09-14

Command: `python -W error -m unittest discover -s tests -v`

Result: **84 tests passed; 0 failures, 0 errors, 0 skips**.
Environment: Python 3.13.5, Linux x86_64, pypdf 5.9.0.
Warnings were treated as errors. The full suite includes synthetic PDF fixtures and
therefore requires pypdf. Earlier record-checking stages use only the standard library.

Tests cover incomplete research, invalid evidence relationships, countercheck gaps,
time-sensitive records, claim-local citations, code-fence false positives, stale review
fingerprints, PDF page counts, missing page reviews, changed render/log files, unsafe
paths, malformed JSON, no-overwrite initialization, metadata, assets, and package references.
An initial test-first run failed because implementation did not yet exist; the final
implementation passed the complete suite without weakening or skipping PDF tests.

This is local synthetic software verification. It is not full-monorepo validation,
routing/model/host evaluation, independent editorial review, or a finished ebook acceptance
test. The 18 behavioural scenarios are supplied but have not been executed with a model.
No GitHub Actions or public-mirror publication was requested or run.

Test log SHA-256:
`d350334ba09a24dad2b70db9eaba98a0a9a4b0c2d48487a43b199a136c989c45`

A proposed registry entry does not activate routing. Repository installation/integration,
PR status, and ZIP identity are reported separately in the handoff.
