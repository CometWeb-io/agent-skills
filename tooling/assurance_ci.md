# Candidate-bound skill change reports

`assurance_ci.py` reads Git objects and supplied comparison packets. It executes
no candidate code, repository tests, model commands or command stored in evidence.
It uses the standard library and existing trusted Git/JSON/comparison validators.

```sh
python3 tooling/assurance_ci.py --repo /path/to/repo \
  --base FULL_TARGET_COMMIT_SHA --head FULL_CANDIDATE_COMMIT_SHA > report.json
python3 tooling/assurance_ci.py --repo /path/to/repo \
  --base FULL_TARGET_COMMIT_SHA --head FULL_CANDIDATE_COMMIT_SHA \
  --evidence supplied-records.json --require-evidence > report.json
```

Both revisions must be full commit SHAs available in the repository. Missing or
ambiguous merge bases are errors; there is no fallback to the current checkout.
Changed paths use merge-base → head, including added/deleted/renamed files
(renames are read as delete/add). Registry row changes and dependent aliases also
select packages. The current instruction baseline uses the exact target base
commit, which can differ from the merge base. Dirty working-tree bytes are ignored.
The report binds base, head, diff base and the complete head tree in
`candidate.candidate_sha256`.

Structural PASS covers only registry membership, required regular package files
and matching package/registry versions. It does not run the broader repository
gates or check version bump policy; the existing Validate workflow owns those.
Files, symlinks and gitlinks at `skills/<id>` are invalid package roots and must
be selected for review even when no registry row was added.
Replacing `skills` itself with a non-directory Git entry is invalid input.
A missing evidence bundle yields `comparison_evidence: NOT_RUN`, and task outcome
is always `NOT_ASSESSED`. No output from this tool is behavioral PASS, native host
qualification, release authorization or a GitHub approval.

## Supplied evidence envelope

An input has exactly these fields:

```json
{
  "schema": "cometweb.assurance-ci-evidence/v1",
  "candidate": {"...": "copy the complete candidate object from the pinned report"},
  "comparisons": [{
    "skill": "example-skill",
    "suite": {"schema": "cometweb.model-evals/v1", "cases": []},
    "max_output_tokens": 128,
    "experiment_sha256": "externally-retained experiment fingerprint",
    "bundle": {"schema": "cometweb.skill-comparison/v1", "experiment": {}, "runs": [], "reviews": []}
  }]
}
```

This is a shape illustration, not valid evidence. Use an actual frozen suite and
reviewed `comparison.json` produced by `build_review_packets.py` /
`review_skill_evals.py`. The suite fingerprint uses the runner's sorted,
indented JSON plus final newline. Experiment/instruction/stimulus fingerprints
use the existing compact `experiment_fingerprint` convention. Output fingerprints
hash exact UTF-8 bytes. The checker reconstructs declared instruction resources
and alias instructions from Git blobs and binds stimuli to prompts, fixtures,
capabilities and output budget. A packet must include all its suite's cases for
the named skill. One homogeneous instruction cohort per changed skill is supported;
split cohorts need a future explicit coverage contract, never silent aggregation.

The existing comparison validator rejects missing output, changed hashes, reused
run/response identities and inconsistent models, hosts, capabilities or cases.
This wrapper also rejects candidate/suite/resource mismatches and unexpected
fields such as self-declared `verified` or oracle commands. It rejects duplicate
JSON keys and bounds evidence size. Evidence remains supplied records, not an
authenticated execution: matching hashes do not prove the model actually ran or
that reviewers' scores are true. Review grades are reported descriptively; a
separate trusted task-outcome grader still needs integration.

Exit 0 means the declared structural/evidence policy is satisfied, exit 1 means
structural failure or required comparison coverage is missing, and exit 2 means
invalid input/identity/evidence. `--require-evidence` needs at least one complete
reviewed comparison and coverage of every selected skill. Missing runs, reviews,
packets or required skills never satisfy it. Unknown evidence is not converted
to zero, and incomplete evidence does not get a behavioral verdict.

## Read-only GitHub workflow

`.github/workflows/assurance-ci.yml` runs on PRs to main or manual dispatch. It
checks out trusted tooling at the fixed, reviewed commit
`762d3b51e19dac2e2af715218ec1104f5b56bc62` from `CometWeb-io/agent-skills`
and the candidate separately,
then reads candidate Git objects without importing or executing candidate files.
Refs reach the shell only through quoted environment variables. Actions are
pinned; checkout credentials are not persisted; repository permissions are
`contents: read`. The workflow provides no secrets, model calls, comments,
issues or approval writes. It uploads a JSON artifact even for policy/validation
failures. Normal PR runs supply no model evidence and must keep task outcome
`NOT_ASSESSED`.

The target base can predate this tool: the bootstrap uses the explicitly reviewed
snapshot above, approved before this workflow pin, rather than a moving PR head
or an automatic fallback to candidate code. The entire trusted checkout, including
transitive imports, comes from that commit. Python ignores environment-provided
module paths and user site packages (`-Es`). Missing trusted objects or tooling
fail the job; they never select a different checker. The base/head arguments still
identify the actual comparison, independently of the checker revision.

Checker changes in a PR do not change the checker executing that PR. They are
tested by Validate and need a separate reviewed pin update to become trusted;
merging code alone does not advance this pin. A green report means only the
existing structural policy was satisfied, with missing model evidence still
`NOT_RUN` and task outcome `NOT_ASSESSED`.
For checker repairs, first retain the reviewed repair commit, then update the
workflow pin in a separate commit and verify a fresh report. A green run of the
old snapshot does not verify a repair present only in the candidate checkout.

Both pytest gates print skipped test names and reasons (`-rs`). A successful
gate can still contain skipped tests. Foreign-platform cases require separate,
same-revision native evidence; missing CLI or browser opt-ins remain unassessed
capabilities. A skip count alone cannot establish which tests were skipped.

PR workflow definitions are themselves reviewable code, not an
organization-wide immutable policy boundary. A live PR run (including fork/ref
availability), organization settings, branch protection and any GitHub App
installation remain separate native integration gates. No such integration is
claimed by local fixture tests or by this workflow's presence.
