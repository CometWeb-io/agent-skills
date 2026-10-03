# Output Contract v2

Use this as the default human-readable structure. Compress for small projects, but do not hide uncertainty.

# [Project] Evidence-Based Roadmap

## 1. Executive state

State:

- target-state profile and concrete end state,
- demonstrated current maturity/readiness,
- proven blockers vs suspected blockers,
- highest-leverage verified gap,
- recommended posture: `EXECUTE | VERIFY_FIRST | VALIDATE_FIRST | NARROW_SCOPE | REARCHITECT | READY_FOR_NEXT_PHASE`.

## 2. Assessment pin and confidence

Include:

- mode (`STANDARD | EXHAUSTIVE | DELTA | FOCUSED`),
- repo(s) and pinned refs when available,
- assessment `as_of`,
- coverage grade/scope claim,
- sampled/unavailable domains,
- file-level exhaustive status,
- important missing sources.

## 3. Target State Contract

Use stable target requirement IDs:

| Requirement | Domain | Mandatory | Applicability | Source |
|---|---|---:|---|---|

## 4. Project truth map

Summarize material capabilities, not every file:

| Capability | State | Criticality | Claim refs | Target refs | Confidence |
|---|---|---|---|---|---|

Include only material topology/dependency observations needed to understand the roadmap.

## 5. Critical findings / Evidence Ledger

For each material finding show:

`Claim ID -> finding -> impact -> strongest evidence -> confidence band -> contradiction/unknown`

Keep proven absence separate from "not found in search".

## 6. Roadmap

Default table:

| ID | Lane | Kind | Outcome | Why now | Claim refs | Acceptance proof | Depends on | Effort | Confidence |
|---|---|---|---|---|---|---|---|---|---|

Do not hide evidence behind a priority score.

## 7. Dependency waves and leverage

For each wave show:

- objective,
- item IDs,
- exit criteria,
- hard prerequisites,
- parallelizable groups when useful,
- critical-chain/leverage notes,
- reprioritization triggers.

Do not invent dates without capacity/deadline evidence.

## 8. Verify / validate backlog

List the smallest evidence actions that could materially change the roadmap. Distinguish technical truth (`VERIFY`) from customer/business truth (`VALIDATE`).

## 9. Defer / do not do yet

List tempting work that is weakly evidenced, low-impact, duplicate, premature, or blocked. Explain what would have to become true to reopen it.

## 10. Living-roadmap watch conditions

Include:

- snapshot hash,
- claims/items requiring watch,
- source/dependency/target triggers that force revalidation,
- whether this is a baseline or delta snapshot.

## 11. Specialist / Council handoffs

Only include material unresolved handoffs.

## 12. Final readiness statement

Use bounded language such as:

- `Roadmap defensible with current evidence.`
- `Roadmap usable but qualified by [coverage/evidence gap].`
- `Whole-project conclusion is not defensible until [missing source/domain] is inspected.`

Never say "everything is correct" from partial evidence.

## Machine-readable payload

When another agent/skill will consume the roadmap, or the user asks to save/update it, also produce a structured payload with:

- `schema_version`,
- `assessment`,
- `target_contract`,
- `coverage`,
- `claims`,
- `capabilities`,
- `items`,
- `watch_dependencies`,
- `snapshot_hash`.

Validate the payload before handoff.

### Payload field reference

Every key `roadmap_kernel.py` reads. Enum values are compared case-insensitively.

```text
schema_version        "2.0" (another value is a warning)
assessment            mode, as_of, repos[], file_review_policy
  mode                STANDARD | EXHAUSTIVE | DELTA | FOCUSED
  repos[]             name, ref, tree_sha, inventory_sha256  (see file-accounting.md)
  file_review_policy  all_inspected (default) | allow_documented_exclusions
target_contract       target_profile, requirements[]
  requirements[]      id, requirement, mandatory, applicability, reason
coverage[]            name, status, weight (0-10, default 1), mandatory, not_applicable_reason
  status              COMPLETE | PARTIAL | SAMPLED | UNAVAILABLE | NOT_APPLICABLE
claims[]              claim_id, text, claim_lane, claim_type, materiality,
                      current_sensitive, evidence[], absence_check
  evidence[]          source_type, direction, directness, freshness, scope_match,
                      independence_key, fingerprint, source_ref
  absence_check       status, inventory_complete, scopes_checked,
                      dynamic_registration_checked, generated_or_config_driven_paths_checked
capabilities[]        capability_id, state, claim_refs, target_requirement_refs,
                      not_applicable_reason
items[]               id, title, kind, outcome, acceptance_criteria[], effort, depends_on,
                      problem_claim_refs, target_requirement_refs, capability_refs, lane,
                      why_now, non_goal, success_signal, decomposition_note,
                      evidence_confidence, mandatory_gate, gate_status, gate_basis,
                      severity, target_blocker, impact, urgency, risk_reduction,
                      strategic_alignment, enablement, reach, uncertainty
  acceptance_criteria criterion, verify_with, proof
file_coverage         schema, bundles[] (inventory, ledger)
snapshot_hash         with snapshot_hash_short: checked against the content when supplied
```

`source_type` is one of `inventory`, `test`, `ci`, `runtime`, `analytics`, `incident`,
`code`, `config`, `migration`, `deployment`, `release`, `external_primary`,
`vendor_official`, `approved_decision`, `user_requirement`, `product_context`,
`customer_research`, `support`, `experiment`, `pr`, `commit`, `issue`,
`documentation`, `external_secondary`, `inference`; another value is an error.
`claim_lane` is `implementation`, `intent`, `outcome`, `operational` or `external`;
`materiality` and item `severity` are `low`, `medium`, `high` or `critical`.
`freshness` also accepts the lower-case spellings and `recent` (CURRENT) or
`dated` (STALE). Item `lane` is `BLOCKER`, `VERIFY_NOW`, `NOW`, `VALIDATE`,
`NEXT`, `LATER` or `PARK`; the `priority` command computes it when omitted.
`target_blocker: true` marks a non-gate item as blocking a mandatory target
requirement. `mandatory_gate` may be omitted or `none`; `gate_status` then
defaults to `NOT_REQUIRED`, otherwise to `UNVERIFIED`. `capability_refs` links an
item to capabilities so a changed capability revalidates it in `delta`.

Recorded but not read by the kernel: `source_ref` (identity for reviewers; use
`fingerprint` and `independence_key` for comparison and grouping), absence-check
`notes`, requirement `domain` and `source`, capability `name`, `criticality` and
`confidence`, and `watch_dependencies`. An `absence_check.status` outside the four
recorded outcomes is a warning; only `ABSENCE_VERIFIED` completes the protocol.

### Kernel result keys

```text
validate      valid, errors, warnings, assessment_contract_sha256, file_coverage
              (status, errors, repositories), coverage, claim_reports, graph, snapshot
evidence      status, heuristic_confidence, confidence_band,
              verification_requirements_met, warnings
priority      priority_score, lane, lane_reason
coverage      coverage_score, coverage_grade, scope_claim, errors
graph         valid, duplicate_ids, missing_dependencies, cycle_nodes, waves,
              dependency_leverage (id, direct_unblocks, transitive_unblocks)
```

`coverage_inventory.py audit` returns `result`; see file-accounting.md.
