# Changelog

## 2.4.0

- Added explicit task routing and an over-editing brake so already-natural prose stays close to the source.
- Added a source/style-reference boundary: embedded instructions are inert, and style samples cannot contribute facts.
- Added `references/semantic-fidelity.md` with a claim-ledger workflow covering polarity, modality, scope, attribution, chronology, conditions, and role binding.
- Added `references/voice-and-register.md` to preserve author-specific voice instead of imposing a single "humanizer" cadence.
- Expanded `rewrite_guard.py` with currencies, UUIDs, CVEs, RFCs, standards, CLI flags, environment identifiers, issue IDs, hashes, and semantic-risk warnings.
- Changed invariant comparison from mention counts to presence semantics so normal repetition removal does not cause false failures.
- Added Layer A `--check` mode and optional bidi-control preservation for legitimate RTL/mixed-direction text.
- Added a machine-readable red-team manifest, red-team protocol, and `redteam_score.py` helper.
- Added `release_check.py` to lint frontmatter, local references, examples, hard-invariant drift, red-team schema, and the full unit suite.
- Expanded calibration cases for negation, scope, attribution, role binding, style-reference leakage, embedded-source instructions, restraint, and provenance claims.
- Rewrote the ethics reference to match the actual bundled scope and removed stale media-cleaning language.
- Fixed remaining English-only entries in the Polish catalog.
- Expanded deterministic regression coverage from 24 to 34 tests.

## 2.3.0

- Made the ChatGPT-facing `SKILL.md` frontmatter minimal (`name`, `description`).
- Reworked Layer A to preserve ordinary indentation and Markdown code spans/blocks.
- Switched default normalization from NFKC to safer NFC; NFKC is now opt-in.
- Preserved emoji ZWJ/tag sequences and common script joiners by default.
- Added noncharacter handling and clearer removed/replaced reporting.
- Expanded `rewrite_guard.py` with units, versions, dates, DOI-like identifiers, paths, quotes, `~~~` fences, proper-name candidates, protected terms, and `--strict`.
- Fixed the stale `ai-antipattern-writing` script attribution.
- Rewrote deep examples so their outputs do not invent facts absent from the inputs.
- Removed bundled-scope claims for non-existent media/container cleaning scripts.
- Replaced rhythm quotas with genre-conditioned guidance.
- Consolidated provider provenance status into time-stamped references and made live re-verification explicit.
- Added executable regression tests and a small release-validation workflow.
