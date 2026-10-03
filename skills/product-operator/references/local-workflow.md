# Local workflow: plan -> validated brief -> snapshot

All paths below are relative to the skill directory. Runtime uses only the Python
standard library; it does not require the monorepo tooling directory or an API key.
Read and redact input before use: reports contain the supplied evidence summaries.
Do not paste secrets or unnecessary personal information into those summaries.

## Inspect without writing

```bash
python3 scripts/operator_kernel.py plan --input-json examples/plan.synthetic.json
python3 scripts/prepare_brief.py --input examples/plan.synthetic.json --language pl
python3 scripts/self_check.py
```

The shipped example is deliberately synthetic. Replace it with a sourced plan input:
`target`, `goal`, `horizon`, timezone-aware `as_of`, `coverage`, `state_items`, and
`candidates`. Candidates contain action/why_now/done_when/confidence/evidence,
action_type, scoring dimensions and depends_on. Unknown coverage stays unavailable.
Explicit critical_gap_open and material_current_evidence_block are binding signals.
Do not use a fabricated high evidence_strength to overcome missing source proof.

## Save a new analysis packet

```bash
python3 scripts/prepare_brief.py --input /private/plan-input.json --output /private/new-brief --language pl
```

The parent must exist and the output directory must not. No old file is overwritten.
The command validates first, then saves brief.md, operator-plan.json,
operator-report.json, operator-snapshot.json, validation.json and BRIEF-MANIFEST.json.
Every candidate survives in the machine report even if it is not shortlisted. NEXT
cannot precede its prerequisites. STOP and readiness-held work are not executed.

A non-ready but structurally valid brief is useful: it states why implementation
must wait and which independent checks may proceed. Exit 0 means artifact generation,
not authorization, READY, validated application behavior, or successful installation.
Exit 2 means invalid input/baseline/output; no completed artifact is claimed.

## Repeat

```bash
python3 scripts/prepare_brief.py --input /private/new-input.json --previous /private/old-brief/operator-snapshot.json --output /private/newer-brief
```

This adds delta.json. It does not invent a baseline for a new project. A malformed
snapshot fails. Changed scope and unverified removed blockers remain explicit.
The input hash and artifact hashes track content consistency, not source authorship.
The brief renderer escapes supplied HTML/Markdown; raw values are retained in JSON.

## Capability limits

self_check validates only bundled resources and selected deterministic scenarios.
pytest runs the larger developer suite. Neither runs a model or queries GitHub,
Notion, a browser or a production application. A tool-free host must perform a
bounded manual analysis and report the unavailable checks instead of inventing them.

## Kernel payload fields

`references/contract.json` binds these names to the scripts; the checker fails when
they drift. `?` marks optional keys. Booleans accept true/false.

```text
plan input (plan, prepare_brief --input):
  target, goal, horizon: non-empty text
  as_of: ISO-8601 with timezone
  mode?: PULSE | STANDARD | DEEP | DELTA | RELEASE (DELTA needs --previous)
  decision?: text; derived from readiness when absent
  coverage?: {github, notion, product_context, outcome_data}: verified | partial | unavailable | not-required
  state_items[]?, candidates[]?
  blockers[]?: unique id; any blocker sets critical_gap_open
  unknowns[]?: at most 3; any unknown sets material_unknowns_open
  critical_gap_open?, unresolved_gate?, material_current_evidence_block?: BLOCKED
  material_unknowns_open?: PROVISIONAL
  outcome_required?: outcome_data coverage then counts
  blocker_resolutions[]?: id | blocker_id | resolved_id of a closed blocker
  environment?, revision?, config_fingerprint?, coverage_exclusions?: copied to the report
readiness input: coverage, goal_known (default true), and the flags above
reconcile input: items[] or a bare list of state items

candidates[]:
  id, action, rationale?, why_now, done_when, confidence, evidence[]
  action_type?: verify | implement | decision | stop; any other value is an input error
  impact, goal_alignment, urgency, dependency_leverage, risk_reduction, learning_value: 0-5
  effort: 0.5-5
  evidence_strength: 0-1
  blocker?, blocks_current_goal?, blocked_item?, future_gate?, trust_critical?
  verify_first?, stop?, decision_required?, decision_domain?
  question?, options[]?, delegated_to?: decision framing
  depends_on[]?: candidate ids
  critical_blocker?: lets a NOW / VERIFY_NOW item exceed its cap

state item:
  id (or name), states: {intent, planned, implemented, verified, shipped, outcome}
  evidence[], outcome_required?
  stale_plan?, orphaned_wip?, context_drift?, context_to_plan_drift?: raise that drift code

evidence:
  source, locator, claim, claim_type: required in a report
  stage: intent | planned | implemented | verified | shipped | outcome
  authority: the lane named in source-routing.md
  freshness_status?: CURRENT | NEAR_EXPIRY | STALE | SUPERSEDED | UNKNOWN | NOT_REQUIRED
  temporal_status?: legacy alias of freshness_status, same values
  observed_at? (verified_at accepted), max_age_days?: compute freshness when no label
  not_required?: NOT_REQUIRED
  required_current?: STALE, SUPERSEDED or UNKNOWN then fails

report (validate):
  protocol_version: 2.0 | 2.1 | 2.2 (blocker checks apply to 2.2)
  as_of, mode, target, goal, horizon, decision, coverage
  mutations?: read-only | none
  readiness: {status: READY | PROVISIONAL | BLOCKED, reasons[]}
  blockers[]: id, condition, blocks_current_goal: true, blocked_item, why_blocking, evidence[], title?
  verify_now[], now[], next[]: candidate rows
  decision_now[]: id, question, decision_domain, why_now, options[] (2+), delegated_to, done_when, evidence[]
    selected_option, recommendation, verdict: forbidden, FAIL when present
  later[], watch[], stop[], drift[], delegations[], unknowns[], state_items[]
snapshot: {snapshot_version, as_of, target, snapshot_hash, state_fingerprint, report}
```

Outputs: `validate` prints `{status: PASS | WARN | FAIL, errors[], warnings[]}`.
`rank` adds `priority_tier` (BLOCKER, VERIFY_NOW, DECISION_NOW, NOW, NEXT, LATER, STOP)
and `priority_score` to each row. `reconcile` issues carry `item_id`, `code`, `severity`,
message and stage; `EVIDENCE_STAGE_UNKNOWN` marks evidence whose stage is not one of the six.
