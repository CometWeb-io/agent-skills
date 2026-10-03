# Kernel inputs and outputs

The three scripts read one JSON object (`--input file.json`, or stdin) and print one JSON
object; an invalid payload exits 2 with an `error` message. The machine-checked contract is
`references/contract.json`; this page is the human-readable field list. Keys the scripts do
not read are ignored, so use these names exactly: a misspelled gate key silently falls back
to its default. Ratings and risks are numbers 0..5; booleans must be JSON `true`/`false`.

## score_candidate.py

`stage` is research or live (`--stage` overrides it; default research). `engagement_mode`
is one of RESEARCH_PARTNER, DESIGN_PARTNER (default), BETA_PARTNER, PAID_PILOT, LIGHTHOUSE.
`candidate` is echoed back. `dimension_confidence` optionally maps rating keys to 0..5;
values at or below 2 are listed in `low_confidence_dimensions`.

Stage A (research), keys inside `ratings`, all required; the weights and meanings are in
`partnerability-rubric.md`:

```text
problem_evidence
representativeness
urgency
learning_value
implementation_plausibility
stakeholder_path
credibility
commercial_optionality
reference_network_value
```

Stage A gates, top level:

```text
evidence_confidence        0..5, default 0 (so omitting it holds the candidate)
contradiction_risk         0..5, default 0
customization_risk         0..5, default 0
conflict_risk              0..5, default 0
professional_contact_path  bool, default false (so omitting it blocks PRIORITY_DISCOVERY)
exploration_mode           bool, default false
```

Stage B (live), keys inside `ratings`, all required:

```text
problem_confirmed
urgency_confirmed
user_champion_access
implementation_readiness
feedback_commitment
decision_procurement_feasibility
mutual_value_alignment
pilot_measurability
transferability
```

Stage B gates, top level:

```text
live_evidence_confirmed    bool, default false; false always returns HOLD_VERIFY
security_privacy_blocker   bool, default false
legal_contract_blocker     bool, default false
customization_risk         0..5, default 0
conflict_risk              0..5, default 0
commercial_commitment      0..5, default 0; checked for PAID_PILOT
reference_permission       bool, or null for unknown; checked for LIGHTHOUSE
```

Returns `status` (research: PRIORITY_DISCOVERY, DISCOVERY, WATCHLIST, HOLD_VERIFY, REJECT;
live: PARTNER_READY, ALIGNMENT_REQUIRED, PAUSE, HOLD_VERIFY, REJECT), `score`,
`base_score`, `recommended_action`, `sub_scores`, `caps_applied`, `hard_reasons`,
`hold_reasons` and, for live, `alignment_reasons`.

## select_cohort.py

```text
selection_stage            outreach_slate (default) or active_cohort; --selection-stage overrides it
size                       >= 1, default 5
max_per_segment            >= 1, default no cap
max_per_duplicate_key      >= 1, default 2
replication_threshold      0..5, default 3; coverage at or above it counts as a replication
include_alignment_required bool; active_cohort also admits ALIGNMENT_REQUIRED
questions[]                learning questions, each with the four keys below
  id                       required
  weight                   >= 0, default 1
  desired_replications     >= 1, default 1
  must_cover               bool
question_weights           used only without questions: question id to weight
desired_replications       used only without questions: question id to replications
candidates[]               the pool, each with the keys below
  company                  required; candidate is accepted instead
  status                   the scorer status; outreach_slate takes PRIORITY_DISCOVERY and DISCOVERY, active_cohort takes PARTNER_READY
  score                    0..100
  segment                  default unknown
  duplicate_key            default the segment
  effort                   0..5
  risk                     0..5
  learning_coverage        question id to coverage 0..5
  learning_questions       used only without learning_coverage: ids, each counted as 5
```

A candidate with any other `status` is listed in `excluded` with the reason, not scored.
Returns `selected`, `coverage_summary` (rows with `met`), `coverage_ratio`,
`must_cover_unmet`, `cohort_complete`, `excluded` and `not_selected`.

## assess_partner_health.py

Keys inside `ratings`, all required:

```text
workflow_usage
learning_yield
user_champion_engagement
implementation_progress
feedback_quality
transferability
value_signal
```

Top level:

```text
partner                    echoed back; candidate is accepted instead
bespoke_pressure           0..5, default 0
support_burden             0..5, default 0
blocker_persistence        0..5, default 0
willingness_to_buy         0..5, default 0
product_ready_for_conversion  bool, default false
timing_capacity_blocker    bool, default false
```

Returns `status` (CONTINUE, REPAIR, PAUSE, EXIT_REVIEW, CONVERSION_CANDIDATE),
`health_score`, `risk_penalty`, `recommended_action` and `reasons`.
