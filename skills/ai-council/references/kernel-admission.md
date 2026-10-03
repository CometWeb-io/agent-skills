# Kernel admission — development 5.0.1

The kernel checks supplied records. It does not verify sources, authenticate approvals, run advisers, execute actions, or grant deployment/publication permission. A supplied `BLOCK` remains `NO-GO`; this preserves the declared constraint, not its factual authentication.

## Final gate

Pass every required role from `plan.roles.gatekeepers` to `--required-gates-json`. Missing roles and required roles marked `NOT_REQUIRED` defer the decision. The input statuses remain operator-supplied: do not mark a role CLEAR simply because it was routed.

```bash
python3 scripts/council_kernel.py gate \
  --verdict GO --confidence 0.9 --required-confidence 0.8 \
  --freshness-status CLEAR \
  --required-gates-json '["security"]' \
  --gate-statuses-json '{"security":"CLEAR"}' \
  --require-go
```

The numbers and status above are a syntax example, not evidence or recommended confidence values. Compute the applicable threshold and provide actual checked state. Freshness on the CLI defaults to `UNKNOWN`; pass `CLEAR` only after assessing applicable evidence and its coverage. The Python function retains `freshness_status="CLEAR"` solely for compatibility with existing callers; new callers must pass the assessed value explicitly.

`gate` prints `{"verdict": ..., "envelope_verdict": ...}`. `envelope_verdict` is the same verdict in the CW-AIP v2 `DecisionEnvelope` spelling (`NO-GO` becomes `NO_GO`; `GO`, `TEST` and `DEFER` are unchanged); copy that field, not `verdict`, into a v2 envelope payload. The Python function `envelope_verdict()` performs the same mapping and raises `ValueError` for anything that is not a Council verdict.

`--require-go`: exit 0 for a resulting GO, 1 for a processed non-GO verdict, and 2 for malformed inputs. Without it, a processed DEFER/NO-GO/TEST is report output with exit 0. No exit code is authorization to execute an action.

Unknown/invalid numbers and non-boolean flags are errors, not zero, approval, or completed controls. Missing binding confidence dimensions yield overall zero and `missing_binding_dimensions`. A critical gap cannot be erased by confidence: GO/NO-GO becomes TEST when a reversible experiment is available, otherwise DEFER. That TEST is a recommendation to design/review an experiment, not permission to run one. Unimplemented required controls always defer, including a proposed TEST. A genuinely separate experiment requires its own scoped gate assessment.

## Observation and forecast accounting

Read `watch.observation_status` before interpreting `triggered`. UNKNOWN is not false. An empty freshness or contradiction input is not clearance. Contradiction coverage reads all material opposition, even when `contradiction_tested` is false, but it still relies on declared flags and does not validate an actual search log.

`forecast-score` reports input, scored, invalid and unresolved counts. Missing, non-numeric or out-of-range probabilities are invalid, not probability zero. A forecast `outcome` is `0` or `1`; the strings `1`, `yes`, `true`, `success` and `occurred` read as `1`, and `0`, `no`, `false`, `failure` and `did_not_occur` as `0` (case-insensitive). Any other outcome is unresolved and excluded from the Brier denominator. These checks do not establish that a forecast preceded the event or that forecasts are independent.

## Payload fields by command

Every key the kernel reads from a JSON argument. Anything else is ignored.

```text
contract --context-json   decision_type, objective, options, status_quo, constraints,
                          time_horizon, success_metric, financial_impact, strategic_impact,
                          uncertainty, reversibility, risk_level, cost_of_delay,
                          cost_of_false_positive, cost_of_false_negative, known_facts,
                          known_unknowns, stakeholders, execution_dependencies,
                          jurisdictions (or one jurisdiction), risk_surfaces
plan/route --contract-json  the contract output: question, decision_type, primary_domain,
                          secondary_domains, decision_kind, reversibility, risk_level,
                          financial_impact, risk_surfaces, ...
mode/threshold/select --profile-json  risk_level, reversibility, financial_impact,
                          uncertainty, strategic_impact, cost_of_false_positive,
                          cost_of_false_negative, primary_domain, secondary_domains, decision_kind
legal --context-json      jurisdictions, force_legal_gate, material_legal_uncertainty,
                          counsel_required (the whole context is also keyword-scanned)
key --context-json        decision_type, options, objective, jurisdictions
regime --context-json     company_stage, market_volatility, geography, business_model, motion
temporal/freshness rows   claim_id | evidence_id | id, claim_type (or freshness_policy),
                          material, draft, verified_for_decision, system_of_record_verified,
                          published_at, effective_from, effective_to, expires_at,
                          last_verified_at, verified_at, observed_at, superseded_by,
                          source_version
coverage --rows-json      accepted, critical_area, independence_group,
                          independence_confidence, source_quality, directness
contradiction claims      claim_id | id, material, contradiction_tested,
                          unresolved_contradiction, contradiction_resolved,
                          opposing_evidence_count, importance
crux/consensus/minority/independence-grade memos
                          expert_id | role_id | id | role, vote, assumptions[] (key |
                          assumption_key, value | position, importance, uncertainty),
                          frameworks | framework_ids, independence_groups,
                          claim_ids | unique_claim_ids, role_class, decision_impact,
                          human_external, actor_type, provider, model_family | model
watch dependency          dependency_id | id, type, operator, previous, current,
                          threshold, materiality, assumption_keys, triggered
validity --decision-json  material_stale_evidence_count, next_revalidation_at, superseded_by
forecast-score rows       probability, outcome (0 | 1)
experiment --spec-json    hypothesis, metric | primary_metric, baseline,
                          pass_threshold | target, fail_threshold, duration, budget, sample,
                          guardrails, minimum_detectable_effect, kill_criteria,
                          evidence_gap_addressed, assumption_key, owner, review_date
gate --gate-statuses-json {gatekeeper role: gate status}
portfolio decisions       decision_id | decision_key | id, resource_claims, depends_on,
                          expected_value; --capacities-json {resource: number}
handoff --decision-json   question | decision, decision_key, jurisdictions, known_facts
handoff --issue-json      question | exact_question, material_uncertainty | uncertainty,
                          primary_sources, alternative_interpretations,
                          business_consequence, deadline, decision_change_condition
tool-authority action     write, external_side_effect, financial, public, destructive,
                          credential_sensitive, sensitive_data, irreversible
provenance rows           accepted, source_class, evidence_weight
eval-compare runs         critical_assumptions_found, material_risks_found,
                          evidence_gaps_found, minority_preservation,
                          legal_constraints_found, test_quality, calibration_score,
                          latency, token_cost, tool_calls (each 0-1)
memory rows               memory_status, outcome, decision_quality, decision_key, domain,
                          decision_kind, decision_type, risk, reversibility, verdict,
                          resolved_vote, blind_vote, blind_confidence, expert | expert_id,
                          framework | framework_ids, expert_ids, regime_tags, updated_at,
                          outcome_lesson, outcome_attribution, review_date | review_dates,
                          consensus_failure, event_type, utility_score, information_gain
rank --current-json       primary_domain, decision_kind, decision_type, risk_level,
                          reversibility, framework_ids, expert_ids, regime_tags, as_of
```

Routed values are checked; an unknown value is an input error (exit 2), not a fallback:

- `decision_type`: `binary`, `option_selection`, `resource_allocation`, `sequencing`, `market_entry`, `pricing`, `build_vs_buy`, `launch`, `partnership`, `hiring`, `m_and_a`, `shutdown`, `product_investment`.
- `reversibility`: `reversible`, `hard_to_reverse`. `risk_level`: `low`, `medium`, `high`.
- `risk_surfaces`: `legal`, `privacy`, `security`, `financial`, `responsible_ai`, `reputation`, `technical`, `people`.
- `primary_domain` and `secondary_domains`: `strategy`, `marketing`, `sales`, `offer_pricing`, `product_customer`, `growth`, `operator`. `decision_kind`: `strategy`, `marketing`, `sales`, `pricing`, `product_customer`, `growth`, `operations`.
- Temporal `claim_type`: `law_regulation`, `regulatory_guidance`, `security_advisory`, `vendor_policy`, `competitor_pricing`, `breaking_market`, `internal_metric`, `official_technical_docs`, `academic_evidence`, `doctrine`, `general_web`; another value is `UNKNOWN`.
- Watch `operator`: `changed`, `gt`, `gte`, `lt`, `lte`, `pct_change_gt`; another value is `observation_status: UNKNOWN`.
- Gate statuses: `NOT_REQUIRED`, `CLEAR`, `CLEAR_WITH_CONTROLS`, `COUNSEL_REQUIRED`, `BLOCK`; another value defers.

Compared as given and not validated (the legacy memory helpers keep their earlier contracts): memo `vote` and memory `verdict`, `blind_vote` and `resolved_vote` (`GO`, `NO-GO`, `TEST`, `DEFER`); `memory_status` (only `Complete` rows count); memory `outcome` (`Pending`, `Success`, `Failure`, `Mixed`); `decision_quality` (`Good`, `Bad`, `Unclear`, `Pending`); `outcome_attribution` (`thesis_wrong`, `thesis_correct`, `execution_failure`, `external_shock`, `wrong_timing`); `event_type` (`router_miss`, `minority_vindicated`); `source_class` (`CURRENT_FACT`, `PRIVATE_KNOWLEDGE`, `DECISION_MEMORY`, `FRAMEWORK`, `LIVE_WEB`, `EXPERT_JUDGMENT`); `actor_type` (`human` marks an external human). Free text and numbers outside the checked commands are clamped or truncated, not rejected.

Identifier lists (`frameworks`, `framework_ids`, `independence_groups`, `claim_ids`, `unique_claim_ids`) take strings or objects; an object counts by its first present `id`, `key`, `claim_id`, `text` or `value`.

`sanitize` keeps only the Decision Memory keys: `decision_key`, `domain`, `decision_kind`, `decision_type`, `risk`, `risk_level`, `reversibility`, `verdict`, `confidence`, `outcome`, `resolved_vote`, `framework_ids`, `expert_ids`, `outcome_lesson`, `updated_at`, `decision_quality`, `execution_quality`, `outcome_attribution`, `same_decision_again`, `snapshot_hash`, `snapshot_version`, `regime_tags`, `evidence_coverage`, `required_confidence`, `consensus_failure`, `council_mode`, `decision_value_score`, `double_crux`, `evidence_critical_gap`, `missing_perspectives`, `counterfactual_tested`, `council_version`, `kernel_version`, `route_version`, `gate_statuses`, `adjusted_consensus`, `effective_independent_perspectives`, `review_dates`. `snapshot --snapshot-json` hashes any object as given.

Result keys other commands consume: `status` (temporal: the statuses in `freshness.md`; freshness: `CLEAR` or `REFRESH_REQUIRED`; validity: `VALID`, `WATCH`, `STALE`, `REOPEN`, `SUPERSEDED`), `admissible`, `age_hours`, `observation_status` (`OBSERVED`, `UNKNOWN`), `majority_vote`, `missing_binding_dimensions`.

## Validation and limits

```bash
python3 -m pytest -q tests
python3 -m unittest discover -s tests -p test_council_kernel.py
```

Pytest is a development dependency for the new regression file. Runtime CLI uses the standard library only. CLI JSON rejects duplicate keys and non-finite numbers, with a four-megabyte input limit. It reports errors without echoing raw payloads. This is not a complete schema validator for every legacy command; unmodified ranking, learning and storage helpers retain their earlier contracts.

Synthetic tests assess deterministic mechanics, not decision quality, external model independence, authenticity of evidence or qualified human approval. Package VERSION is unchanged and no release is published.
