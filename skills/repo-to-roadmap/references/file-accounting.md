# Pinned file accounting

Use this workflow for an explicit every-file request, or as a precise inventory
for a subsequent delta. It complements the domain coverage and claim/evidence
model; it does not discover defects or authorize changes.

## Local Git inventory

From this skill directory, supply the actual repository and a full immutable
commit SHA (not a branch, tag or shortened SHA). Output directories must already
exist. Keep audit outputs outside the source checkout and outside the skill.

```bash
python3 scripts/coverage_inventory.py inventory \
  --repo /path/to/source-repo --repository owner/repo \
  --commit <full-commit-sha> --output /path/to/audit/inventory.json
python3 scripts/coverage_inventory.py template \
  --inventory /path/to/audit/inventory.json \
  --output /path/to/audit/review.json
```

The inventory uses the commit's entire Git tree, not the mutable worktree or
index. Uncommitted/untracked/ignored changes are not in that scope. Resolve a new
scope explicitly when those changes matter. Empty and shallow repositories are
not equivalent: an empty tree is disclosed; missing objects fail collection.

All directories and tracked entries are accounted for, including hidden files.
The tool records path, mode, type and object SHA without loading blob contents.
It rebuilds Git tree hashes bottom-up, including directory sorting, executable
bits, symlinks and gitlinks. Removing a subtree cannot keep the expected root hash.
SHA-1 and SHA-256 local Git repositories are supported.

Git object reads do not run project code, hooks, content filters or a checkout.
Lazy fetching and network protocols are disabled. These are inventory operations,
not a sandbox for arbitrary untrusted Git installations. Use a trusted Git binary.

## Connector export

Use the connected GitHub tool to read the commit's actual root tree identity and
its **complete recursive tree**, then preserve that JSON export. Do not use a
subtree as the entire commit, a search-result list, or a truncated response.

```bash
python3 scripts/coverage_inventory.py import-tree \
  --tree /path/to/audit/github-recursive-tree.json \
  --repository owner/repo --commit <full-commit-sha> \
  --expected-tree <independently-obtained-root-tree-sha> \
  --output /path/to/audit/inventory.json
```

A literal `truncated: false` is required but not sufficient: every directory hash
and the root hash are recomputed. GitHub URL/size metadata is not copied. This
adapter accepts GitHub's SHA-1 tree format. The repository name and commit-to-tree
association remain **caller-supplied connector pins**, unlike a local Git object
read. Hash consistency does not authenticate GitHub, the repository owner or a
reviewer. Obtain and retain the anchor through the authorized source of record.

## Review records

The template begins with every tracked leaf as `UNAVAILABLE` and reason
`Review not performed`. Do not call collection a review. After actually reviewing
a file, replace that record with its exact path/SHA and fields such as:

```json
{
  "path": "src/api.py",
  "sha": "<actual-object-sha-from-inventory>",
  "status": "INSPECTED",
  "reviewer": "<actual-agent-or-reviewer-reference>",
  "reviewed_at": "<actual-ISO-timestamp-with-timezone>",
  "evidence_ref": "<review-artifact-location>",
  "summary": "<what was checked and what remains unverified>"
}
```

This is a shape example, not valid completed evidence. No field should be filled
with invented facts or with an auto-generated claim that the review passed.

`EXCLUDED_GENERATED` and `EXCLUDED_VENDOR` require `reason`, `scope_basis` and
`evidence_ref`. They remain explicit exclusions. Do not exclude a difficult file
just to improve coverage. `BINARY_UNREADABLE` and `UNAVAILABLE` require a reason and
remain gaps. Symlink targets are never followed: INSPECTED can describe the link
itself only. A submodule/gitlink must stay UNAVAILABLE in the parent inventory;
assess its pinned commit as a separate repository scope.

## Validate accounting

Keep the inventory SHA-256 independently of the ledger and resulting report.

```bash
python3 scripts/coverage_inventory.py audit \
  --inventory /path/to/audit/inventory.json --ledger /path/to/audit/review.json \
  --expected-inventory-sha256 <saved-inventory-sha256> \
  --output /path/to/audit/coverage.json
```

`--require-inspected` additionally rejects a result that has legitimate exclusions.
Without the optional independent pin, the check reports self-consistency only.
It never claims to authenticate review records or test runtime behavior.

| Result | Meaning |
| --- | --- |
| `INSPECTION_RECORDS_COMPLETE` | Every tracked leaf has an admissible supplied inspection record; review quality is not established. |
| `ACCOUNTED_WITH_EXCLUSIONS` | No missing/unavailable rows, but generated/vendor files were explicitly excluded. |
| `EXHAUSTIVE_NOT_PROVEN` | At least one missing, unavailable, unreadable or unexpanded-submodule path. |
| `EMPTY_SCOPE` | No tracked leaves; not a successful source review. |

Audit exits 0 for complete records or fully accounted explicit exclusions; 1 for
gaps/empty scope (and exclusions under --require-inspected); 2 for invalid input
or execution failure. Inventory/template/delta exit 0 after successful creation,
not after a successful review. Output files are exclusively created: no implicit
overwrite, directory creation or symlink output traversal.

## Delta

```bash
python3 scripts/coverage_inventory.py delta \
  --before /path/to/audit/before-inventory.json \
  --after /path/to/audit/after-inventory.json
```

The result identifies added, removed, mode/type/content-modified and byte-identical
paths. It does not guess renames or automatically reuse an old review. Changes in
dependencies, configuration and target requirements can invalidate unchanged code.
Use the existing claim/capability/watch-dependency workflow to propagate that
invalidation. Do not call an unchanged file proof of an unchanged behavior.

## Maintenance checks

```bash
python3 -m pytest -q tests/test_coverage_inventory.py
```

Runtime uses Python's standard library and local Git. Tests require pytest and
Git. The fixture repositories and review records are synthetic, not observations
of a user's product. Repository paths can themselves be private; do not publish
inventory outputs merely because source file contents are absent.

Git behavior references reviewed 2026-09-13:
https://git-scm.com/docs/git-ls-tree and https://git-scm.com/docs/git .


## Enforce accounting in the final roadmap (kernel 2.0.1)

`roadmap_kernel.py validate` now recomputes supplied file accounting instead of
trusting a success label or a file count. In `assessment.mode: EXHAUSTIVE`, missing
file accounting is a validation error. STANDARD/FOCUSED/DELTA do not require new
file evidence by default, but supplied evidence is always checked, never ignored.
The check describes records of inspection, not source-review quality or runtime
correctness. Domain coverage, claim evidence and dependency checks still apply.

Add one exact anchor per assessed repository to `assessment.repos`:

```json
{
  "name": "owner/repo",
  "ref": "<full-pinned-commit-sha>",
  "tree_sha": "<root-tree-sha-read-from-the-authorized-source>",
  "inventory_sha256": "<inventory-fingerprint-saved-before-review>"
}
```

The placeholder strings are not valid evidence. Preserve these anchors when
reviewing; do not obtain an apparent independent anchor merely by copying it
from a finished, untrusted proof bundle. Repo labels and commit/tree associations
are still supplied data. Hash checking does not authenticate those associations.

Attach raw inventory and ledger objects to the roadmap, not local filenames and
not the output of `coverage_inventory.py audit`:

```text
file_coverage:
  schema: cometweb.roadmap-file-coverage/v1
  bundles:
    - inventory: <entire inventory JSON object>
      ledger: <entire file-review JSON object>
```

The validator does not open payload-supplied paths. It loads only the inventory
module shipped beside itself. Bundles must cover every declared repository
exactly once: missing, extra or duplicate scopes fail. All commit/tree/inventory
pins must match, and observations/reviews must not postdate assessment.as_of.
That assessment timestamp must include a timezone and must not be in the future.
A missing file, unavailable review, empty tree or unexpanded submodule blocks the
unqualified exhaustive result even with a high domain-coverage score.

The default `assessment.file_review_policy` is `all_inspected`. Explicitly choose
`allow_documented_exclusions` only when generated/vendor exclusions are within the
agreed scope. A passing result then says `ACCOUNTED_WITH_EXCLUSIONS` with a warning,
not that every file was read. A submodule remains unresolved in the parent
inventory; this change does not implement submodule coverage roll-up.

```bash
python3 scripts/roadmap_kernel.py validate \
  --roadmap-json @/path/to/audit/roadmap.json --require-valid
```

Without --require-valid, the legacy report-only CLI still returns 0 for processed
invalid results: inspect `valid` and `errors`. With it: 0 means valid supplied
records, 1 means processed validation failure, 2 means malformed/unreadable input.
The same option works for `graph`. An invalid dependency graph no longer emits
execution waves or a topological execution order. Neither validation nor its exit
code grants permission to execute tasks, publish or deploy.

### Freeze the scope before completing the review

The validation result includes `assessment_contract_sha256` even when the review
is incomplete. Save it independently before inspection. It fingerprints mode,
repository pins, target requirements and review policy, but not the review rows
or assessment timestamp. Then supply it when checking the completed roadmap:

```bash
python3 scripts/roadmap_kernel.py validate \
  --roadmap-json @/path/to/audit/roadmap.json --require-valid \
  --expected-scope-sha256 <independently-saved-contract-hash>
```

Removing a repository, weakening the exclusion policy, lowering the assessment
mode or changing target requirements fails this comparison. Without that external
pin, the validator can only check the scope supplied in the current input. A hash
is not a record of who approved the scope or whether they had authority.

### Snapshot and delta integration

The complete file-coverage payload participates in the snapshot hash. A supplied
snapshot hash inconsistent with the roadmap is rejected by validation and delta.
Changed review records or scope/policy changes require revalidation of roadmap
items. Identical incomplete file accounting does not yield a VALID delta. Existing
claim/capability/dependency invalidation remains in place; this is not automatic
reuse of previous review records. Old snapshots are not rewritten.

Maintenance: run `python3 -m pytest -W error -q tests` for both the inventory and
roadmap kernel, including their integration tests. These are deterministic tests
of synthetic records, not completed audits or a model-quality benchmark.
