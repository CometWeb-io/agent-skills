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
