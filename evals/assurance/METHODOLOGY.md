# Original assurance cohort v1

This cohort supplies 102 original synthetic snapshot tasks: 34 each for web QA with repair/retest planning, release-evidence acceptance, and agency claim/evidence review. It is authored by an LLM in a separate context from the candidate authors. It is **not an independent expert audit**, and it does **not yet satisfy M03's independent-validation requirement**.

`human_review=not_run`, `independent_validation=not_established`, and `candidate_executions=not_run` are intentional. Source passages labelled receipts, logs, reports, advisory records, timestamps, counts or permissions are constructed task inputs, not accounts of actual executions, customers or published studies. Network hosts are reserved `.invalid` examples or localhost; no endpoint was contacted. No private business evidence is included.

## Contents and outcome criteria

- `v1/cases.json`: user request, allowed actions, source snapshots and hashes, proposed oracle, provenance, family/cluster and split for each case.
- `v1/manifest.json`: base revision, corpus/content hashes, freeze declaration, deterministic split assignment and coverage.
- `tooling/assurance_benchmark.py`: integrity/provenance/split validator and source-only review packet exporter.
- `tooling/tests/test_assurance_benchmark.py`: targeted validation and packet-isolation tests.

Oracle outcomes describe substantive behavior, factual conclusions, scope limits and prohibited actions. They do not require skill-specific headings, section names or literal answer wording. Alternative repairs that meet the stated requirements are acceptable; the proposed repair is not a unique implementation golden. Reviewers must independently inspect each source and the stated rule, rather than accept the author's oracle as ground truth merely because a hash matches.

Web tasks ask for diagnosis and a bounded repair/retest plan from snippets and state traces. They do not provide runnable applications and cannot establish that a repair was applied, that a browser retest succeeded, or that a deployment works. Release tasks distinguish measured failures from missing evidence and narrowly accepted gates. Agency tasks assess arithmetic, source support, scope, permissions, uncertainty and misleading claims. The cohort includes 20 positive, 69 negative and 13 adversarial cases. A negative case may require rejecting a bug allegation rather than finding a defect.

## Dependence and frozen split

There are 51 named families/clusters, each with two distinct tasks about related mechanisms. A change of object name or count was not used as the basis for a second task. For example, persistence covers optimistic acknowledgement versus losing a pending debounce on unmount; the tasks have different failure mechanisms and verification requirements, but are still grouped as correlated.

This grouping is an author assessment, not an empirical proof of diversity. Shared authorship, source style and reasoning patterns may create dependence across the declared clusters and workflows as well. **Do not report 102 independent trials.** Report task count, cluster count and workflow strata separately; use cluster-aware analysis when appropriate and do not infer a universal effective sample size from the 51 labels.

Before any candidate trials, the author assigned whole clusters using the manifest seed: within each workflow, sort cluster IDs by SHA-256 of `seed:cluster_id`; assign the first six clusters to holdout and the rest to development. This gives 66 development and 36 holdout tasks, with no family/cluster spanning both splits. The manifest records all case hashes and assignments. The manifest is the pre-execution snapshot; future trial receipts belong in a separate ledger and must not change its `candidate_executions=not_run` authoring-state declaration. Changes after the freeze create a new cohort version; do not silently repair the frozen inputs or oracle after viewing model results. Record ambiguous or incorrect cases as adjudication exclusions and review their impact before a replacement cohort.

The holdout is **public and frozen, not secret or access-controlled**. Its source and oracle may be exposed by publication or by reading the corpus. A public split alone cannot prove an unseen evaluation or prevent future model training contamination. Before making unseen-holdout claims, use an access-controlled independently prepared cohort and record all exposure. Candidate authors and model runners should receive only the authorized task inputs; never supply `oracle`, provenance, split or task-outcome labels in a model prompt. This bundle contains no model-runner integration and must not be passed wholesale to a model.

The author read repository instructions, file/directory names, the project plan and packaging/test configuration. The author did not read skill instructions, skill rubrics/goldens, prior model outputs or existing frozen holdouts. This is an author declaration; it is not an independently attested contamination audit.

## Validation and review packets

From repository root:

```sh
python tooling/assurance_benchmark.py
python -m pytest tooling/tests/test_assurance_benchmark.py -q
python tooling/assurance_benchmark.py --review-packets /tmp/assurance-corpus-review.jsonl
```

The exporter refuses an existing output file. It emits 102 source-only corpus-review packets with opaque packet IDs, no oracle, split, workflow, author/arm/model identity, and `candidate_output=null`. Case IDs are omitted because descriptive IDs can cue a diagnosis. The coordinator can map packet IDs back using `review-` plus the first 16 hexadecimal characters of SHA-256 of the case ID. Do not give that mapping to reviewers. These packets are prepared for review; they are not completed blind model-output evaluations. No model outputs were read or generated as task trials. Independent reviewers should derive supportable decisions and flag ambiguity, defects, overlap and independence conflicts before seeing the author oracle. Resolve disagreements with a separate adjudication record.

A future blinded output-review integration must attach real candidate outputs under randomized arm-neutral IDs and retain the arm mapping separately. That work belongs with the grading/evaluation integration; this exporter deliberately does not synthesize responses or scores. Peer-LLM review is not a substitute for the missing independent expert validation.

The validator checks JSON readability, required fields, content and source hashes, unique IDs, exact duplicate tasks, source references, explicit synthetic/LLM provenance, coverage, cluster integrity, predeclared assignment and unperformed-review status. It does not validate semantic truth, identify paraphrase duplicates, verify author independence, prove chronological freezing, provide an OS sandbox, or run the workflows. Hashes detect accidental drift against a recorded manifest, not a coordinated rewrite of both data and manifest. External reviewed revision/digest pinning remains necessary.

## Remaining evidence

Independent expert review of sources, oracles, diversity and dependence has not run. No benchmark execution, baseline comparison, judge calibration, host qualification, actual repair/retest, cost measurement or skill uplift is established by this cohort or its structural tests. These remain separate evidence gates, not implied consequences of reaching 100 cases.
