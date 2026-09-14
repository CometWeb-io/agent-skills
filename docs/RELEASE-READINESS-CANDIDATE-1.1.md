# Release Readiness 1.1.0 — local candidate, not published

This overlay upgrades the existing canonical `release-readiness` skill; it does not
introduce a second auditor, reinstate the retired writing package, or change the
independent PR #5. The underlying source revision is
`868045d5ad486c96e45556c0aa7be628d8a1cd4a`.

## Integration boundary

The code replaces the skill's two Python entry points, updates its manifest/CI
references, adds candidate-binding regression tests, and bumps VERSION/registry.
Unrelated skill resources, license, icons and references remain in the canonical
checkout. This overlay alone is not the full skill or a full monorepo clone.

Use the existing `tooling/integration_preview.py` against a full local checkout.
Review conflicts and workflow changes separately, regenerate adapters only after
all canonical source packages are present, and run the original repository
validation pipeline. Do not overlay directly onto newer work without comparison.

## Behavior changes that require migration

Resolve short commit IDs to full IDs from the source of record. Preserve explicit
evidence environment and every pinned immutable ID. Fill missing evidence only
from observations, not inference. Bare dates/naive times are not silently converted
to UTC. A null owner, malformed expiry or weaker required-evidence field can no
longer produce a controlled or unconditional green result.

`--previous` now freezes requirements by default. An intentional revised scope
needs a reviewed external contract hash; an omitted blocker is never a resolved
blocker. See the skill's updated `references/manifest-schema.md` and
`references/ci-integration.md`.

## Tests and limits

The original two scripts and two test files were reconstructed from authorized
connector reads and verified byte-for-byte using their Git blob hashes. The
original tests are retained in the delivery's evidence directory. The positive
engine test fixture was migrated in two lines (full SHA and explicit environment),
without deleting assertions or weakening expected verdicts. Bootstrap tests are
unchanged. Additional regression cases use synthetic manifests.

Passing these tests supports deterministic implementation behavior. It does not
prove a real release is safe, the whole repository is integrated, or a model will
follow the skill. No model calls, reviewer ratings, host installations, remote
writes or production changes are performed by this work.
