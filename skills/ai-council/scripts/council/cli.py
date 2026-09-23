from __future__ import annotations

import argparse
import json

from .contract import (
    choose_council_mode,
    compile_decision_contract,
    decision_value_score,
    mode_budget,
    plan_council,
    profile_problem,
    required_confidence,
)
from .decision_memory import (
    base_rate_report,
    calibration_report,
    champion_challenger,
    consensus_failure_patterns,
    council_health,
    decision_validity_overlay,
    due_reviews,
    evaluate_watch_dependency,
    forecast_score_report,
    infer_regime_tags,
    make_decision_key,
    portfolio_report,
    rank_analogies,
    sanitize_memory_record,
    snapshot_hash,
    source_provenance_summary,
)
from .deliberation import (
        build_experiment_spec,
        consensus_report,
        contradiction_coverage,
        decompose_confidence,
        deliberation_stop,
        evidence_coverage_report,
        find_double_crux,
        framework_usefulness,
        independence_grade_report,
        information_gain_score,
        minority_sentinel,
        value_of_information,
    )
from .risk_gates import build_human_handoff_packet, gate_verdict, tool_authority_assessment
from .routing import (
    detect_missing_perspectives,
    dynamic_specialists,
    route_internal_context,
    route_legal_risk,
    route_roles,
    select_frameworks,
)
from .temporal import evaluate_temporal_truth, freshness_gate, source_authority_for_claim
from .util import _load_cli_json

def main() -> int:
    parser = argparse.ArgumentParser(description="Deterministic AI Council v5 temporal decision intelligence kernel")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("profile")
    p.add_argument("--query", required=True)

    p = sub.add_parser("contract")
    p.add_argument("--query", required=True)
    p.add_argument("--context-json", default="{}")

    p = sub.add_parser("plan")
    p.add_argument("--contract-json", required=True)
    p.add_argument("--mode")

    p = sub.add_parser("route")
    p.add_argument("--contract-json", required=True)
    p.add_argument("--mode", default="STANDARD")

    p = sub.add_parser("legal")
    p.add_argument("--query", required=True)
    p.add_argument("--context-json", default="{}")

    p = sub.add_parser("select")
    p.add_argument("--query", required=True)
    p.add_argument("--profile-json", required=True)
    p.add_argument("--experts-json", required=True)
    p.add_argument("--max-frameworks", type=int, default=3)

    p = sub.add_parser("rank")
    p.add_argument("--current-json", required=True)
    p.add_argument("--history-json", required=True)

    p = sub.add_parser("calibrate")
    p.add_argument("--rows-json", required=True)
    p.add_argument("--expert", required=True)
    p.add_argument("--domain")
    p.add_argument("--decision-kind")
    p.add_argument("--regime-tags-json")

    p = sub.add_parser("sanitize")
    p.add_argument("--record-json", required=True)

    p = sub.add_parser("key")
    p.add_argument("--query", required=True)
    p.add_argument("--date", required=True)
    p.add_argument("--context-json", default="{}")

    p = sub.add_parser("mode")
    p.add_argument("--profile-json", required=True)
    p.add_argument("--financial-impact", type=float, default=0.5)
    p.add_argument("--uncertainty", type=float, default=0.5)
    p.add_argument("--strategic-impact", type=float)

    p = sub.add_parser("budget")
    p.add_argument("--mode", required=True)

    p = sub.add_parser("threshold")
    p.add_argument("--profile-json", required=True)
    p.add_argument("--evidence-coverage", type=float, required=True)
    p.add_argument("--decision-value", type=float, default=0.5)

    p = sub.add_parser("coverage")
    p.add_argument("--rows-json", required=True)
    p.add_argument("--areas-json", required=True)

    p = sub.add_parser("crux")
    p.add_argument("--memos-json", required=True)

    p = sub.add_parser("consensus")
    p.add_argument("--memos-json", required=True)
    p.add_argument("--same-model-baseline", type=float, default=0.25)

    p = sub.add_parser("minority")
    p.add_argument("--memos-json", required=True)

    p = sub.add_parser("confidence")
    p.add_argument("--dimensions-json", required=True)
    p.add_argument("--binding-json", default="[]")

    p = sub.add_parser("voi")
    p.add_argument("--probability-change", type=float, required=True)
    p.add_argument("--value-difference", type=float, required=True)
    p.add_argument("--information-cost", type=float, required=True)
    p.add_argument("--delay-cost", type=float, default=0.0)

    p = sub.add_parser("stop")
    p.add_argument("--expected-information-gain", type=float, required=True)
    p.add_argument("--deliberation-cost", type=float, required=True)
    p.add_argument("--no-novelty-rounds", type=int, default=0)
    p.add_argument("--unresolved-mandatory-gate", action="store_true")
    p.add_argument("--critical-gap-open", action="store_true")

    p = sub.add_parser("specialists")
    p.add_argument("--query", required=True)
    p.add_argument("--experts-json", default="[]")
    p.add_argument("--max-specialists", type=int, default=5)

    p = sub.add_parser("missing")
    p.add_argument("--query", required=True)
    p.add_argument("--experts-json", default="[]")

    p = sub.add_parser("experiment")
    p.add_argument("--spec-json", required=True)

    p = sub.add_parser("snapshot")
    p.add_argument("--snapshot-json", required=True)
    p.add_argument("--version", type=int, default=3)

    p = sub.add_parser("gate")
    p.add_argument("--verdict", required=True)
    p.add_argument("--confidence", type=float, required=True)
    p.add_argument("--required-confidence", type=float, required=True)
    p.add_argument("--reversible-experiment", action="store_true")
    p.add_argument("--critical-gap")
    p.add_argument("--gate-statuses-json", default="{}")
    p.add_argument("--controls-implemented", action="store_true")
    p.add_argument("--freshness-status", default="UNKNOWN")
    p.add_argument("--required-gates-json", default="[]")
    p.add_argument("--require-go", action="store_true")
    p.add_argument("--human-approval-required", action="store_true")
    p.add_argument("--human-approved", action="store_true")

    p = sub.add_parser("regime")
    p.add_argument("--context-json", required=True)

    p = sub.add_parser("due-reviews")
    p.add_argument("--rows-json", required=True)
    p.add_argument("--today", required=True)

    p = sub.add_parser("info-gain")
    p.add_argument("--expert-vote", required=True)
    p.add_argument("--peer-votes-json", required=True)
    p.add_argument("--novel-claims", type=int, default=0)
    p.add_argument("--shared-claims", type=int, default=0)
    p.add_argument("--independence", type=float)
    p.add_argument("--decision-impact", type=float, default=0.5)
    p.add_argument("--later-validation", type=float)

    p = sub.add_parser("framework-utility")
    p.add_argument("--exposed-assumption", action="store_true")
    p.add_argument("--changed-vote", action="store_true")
    p.add_argument("--identified-test", action="store_true")
    p.add_argument("--exposed-risk", action="store_true")
    p.add_argument("--rejected", action="store_true")

    p = sub.add_parser("health")
    p.add_argument("--decisions-json", required=True)
    p.add_argument("--votes-json", required=True)
    p.add_argument("--experiments-json", required=True)
    p.add_argument("--process-json", default="[]")

    p = sub.add_parser("provenance")
    p.add_argument("--rows-json", required=True)

    p = sub.add_parser("consensus-patterns")
    p.add_argument("--rows-json", required=True)

    p = sub.add_parser("eval-compare")
    p.add_argument("--champion-json", required=True)
    p.add_argument("--challenger-json", required=True)

    p = sub.add_parser("source-authority")
    p.add_argument("--claim-type", required=True)

    p = sub.add_parser("temporal")
    p.add_argument("--row-json", required=True)
    p.add_argument("--as-of", required=True)

    p = sub.add_parser("freshness")
    p.add_argument("--rows-json", required=True)
    p.add_argument("--as-of", required=True)

    p = sub.add_parser("context-route")
    p.add_argument("--query", required=True)

    p = sub.add_parser("watch")
    p.add_argument("--dependency-json", required=True)

    p = sub.add_parser("validity")
    p.add_argument("--decision-json", required=True)
    p.add_argument("--dependencies-json", default="[]")
    p.add_argument("--as-of", required=True)

    p = sub.add_parser("contradiction")
    p.add_argument("--claims-json", required=True)

    p = sub.add_parser("independence-grade")
    p.add_argument("--memos-json", required=True)

    p = sub.add_parser("forecast-score")
    p.add_argument("--forecasts-json", required=True)

    p = sub.add_parser("base-rate")
    p.add_argument("--rows-json", required=True)
    p.add_argument("--decision-type", required=True)
    p.add_argument("--regime-tags-json", default="[]")

    p = sub.add_parser("portfolio")
    p.add_argument("--decisions-json", required=True)
    p.add_argument("--capacities-json", default="{}")

    p = sub.add_parser("handoff")
    p.add_argument("--kind", required=True)
    p.add_argument("--decision-json", required=True)
    p.add_argument("--issue-json", required=True)

    p = sub.add_parser("tool-authority")
    p.add_argument("--action-json", required=True)

    args = parser.parse_args()

    if args.command == "profile":
        result = profile_problem(args.query)
    elif args.command == "contract":
        result = compile_decision_contract(args.query, _load_cli_json(args.context_json))
    elif args.command == "plan":
        result = plan_council(_load_cli_json(args.contract_json), args.mode)
    elif args.command == "route":
        result = route_roles(_load_cli_json(args.contract_json), args.mode.upper())
    elif args.command == "legal":
        result = route_legal_risk(args.query, _load_cli_json(args.context_json))
    elif args.command == "select":
        result = select_frameworks(args.query, _load_cli_json(args.profile_json), _load_cli_json(args.experts_json), args.max_frameworks)
    elif args.command == "rank":
        result = rank_analogies(_load_cli_json(args.current_json), _load_cli_json(args.history_json))
    elif args.command == "calibrate":
        regimes = _load_cli_json(args.regime_tags_json) if args.regime_tags_json else None
        result = calibration_report(_load_cli_json(args.rows_json), args.expert, args.domain, args.decision_kind, regimes)
    elif args.command == "sanitize":
        result = sanitize_memory_record(_load_cli_json(args.record_json))
    elif args.command == "key":
        result = {"decision_key": make_decision_key(args.query, args.date, _load_cli_json(args.context_json))}
    elif args.command == "mode":
        profile = _load_cli_json(args.profile_json)
        score = decision_value_score(profile, args.financial_impact, args.uncertainty, args.strategic_impact)
        result = {"mode": choose_council_mode(profile, args.financial_impact, args.uncertainty, args.strategic_impact), "decision_value_score": score}
    elif args.command == "budget":
        result = mode_budget(args.mode)
    elif args.command == "threshold":
        result = {"required_confidence": required_confidence(_load_cli_json(args.profile_json), args.evidence_coverage, args.decision_value)}
    elif args.command == "coverage":
        result = evidence_coverage_report(_load_cli_json(args.rows_json), _load_cli_json(args.areas_json))
    elif args.command == "crux":
        result = find_double_crux(_load_cli_json(args.memos_json))
    elif args.command == "consensus":
        result = consensus_report(_load_cli_json(args.memos_json), args.same_model_baseline)
    elif args.command == "minority":
        result = minority_sentinel(_load_cli_json(args.memos_json))
    elif args.command == "confidence":
        result = decompose_confidence(_load_cli_json(args.dimensions_json), _load_cli_json(args.binding_json))
    elif args.command == "voi":
        result = value_of_information(args.probability_change, args.value_difference, args.information_cost, args.delay_cost)
    elif args.command == "stop":
        result = deliberation_stop(args.expected_information_gain, args.deliberation_cost, args.no_novelty_rounds, args.unresolved_mandatory_gate, args.critical_gap_open)
    elif args.command == "specialists":
        result = dynamic_specialists(args.query, _load_cli_json(args.experts_json), args.max_specialists)
    elif args.command == "missing":
        result = {"missing_perspectives": detect_missing_perspectives(args.query, _load_cli_json(args.experts_json))}
    elif args.command == "experiment":
        spec = _load_cli_json(args.spec_json)
        result = build_experiment_spec(
            spec.get("hypothesis", ""), spec.get("metric") or spec.get("primary_metric", ""), spec.get("baseline", ""),
            spec.get("pass_threshold") or spec.get("target", ""), spec.get("fail_threshold", ""), spec.get("duration", ""),
            spec.get("budget", ""), spec.get("sample", ""), spec.get("guardrails"), spec.get("minimum_detectable_effect", ""),
            spec.get("kill_criteria"), spec.get("evidence_gap_addressed", ""), spec.get("assumption_key", ""),
            spec.get("owner", ""), spec.get("review_date", ""),
        )
    elif args.command == "snapshot":
        result = {"snapshot_hash": snapshot_hash(_load_cli_json(args.snapshot_json), args.version), "snapshot_version": args.version}
    elif args.command == "gate":
        result = {"verdict": gate_verdict(
            args.verdict, args.confidence, args.required_confidence, args.reversible_experiment,
            args.critical_gap, _load_cli_json(args.gate_statuses_json), args.controls_implemented,
            args.freshness_status, args.human_approval_required, args.human_approved,
            _load_cli_json(args.required_gates_json),
        )}
    elif args.command == "regime":
        result = {"regime_tags": infer_regime_tags(_load_cli_json(args.context_json))}
    elif args.command == "due-reviews":
        result = due_reviews(_load_cli_json(args.rows_json), args.today)
    elif args.command == "info-gain":
        result = {"information_gain": information_gain_score(
            args.expert_vote, _load_cli_json(args.peer_votes_json), args.novel_claims, args.shared_claims,
            args.independence, args.decision_impact, args.later_validation,
        )}
    elif args.command == "framework-utility":
        result = framework_usefulness(args.exposed_assumption, args.changed_vote, args.identified_test, args.exposed_risk, args.rejected)
    elif args.command == "health":
        result = council_health(_load_cli_json(args.decisions_json), _load_cli_json(args.votes_json), _load_cli_json(args.experiments_json), _load_cli_json(args.process_json))
    elif args.command == "provenance":
        result = source_provenance_summary(_load_cli_json(args.rows_json))
    elif args.command == "consensus-patterns":
        result = consensus_failure_patterns(_load_cli_json(args.rows_json))
    elif args.command == "eval-compare":
        result = champion_challenger(_load_cli_json(args.champion_json), _load_cli_json(args.challenger_json))
    elif args.command == "source-authority":
        result = source_authority_for_claim(args.claim_type)
    elif args.command == "temporal":
        result = evaluate_temporal_truth(_load_cli_json(args.row_json), args.as_of)
    elif args.command == "freshness":
        result = freshness_gate(_load_cli_json(args.rows_json), args.as_of)
    elif args.command == "context-route":
        result = route_internal_context(args.query)
    elif args.command == "watch":
        result = evaluate_watch_dependency(_load_cli_json(args.dependency_json))
    elif args.command == "validity":
        result = decision_validity_overlay(_load_cli_json(args.decision_json), _load_cli_json(args.dependencies_json), args.as_of)
    elif args.command == "contradiction":
        result = contradiction_coverage(_load_cli_json(args.claims_json))
    elif args.command == "independence-grade":
        result = independence_grade_report(_load_cli_json(args.memos_json))
    elif args.command == "forecast-score":
        result = forecast_score_report(_load_cli_json(args.forecasts_json))
    elif args.command == "base-rate":
        result = base_rate_report(_load_cli_json(args.rows_json), args.decision_type, _load_cli_json(args.regime_tags_json))
    elif args.command == "portfolio":
        result = portfolio_report(_load_cli_json(args.decisions_json), _load_cli_json(args.capacities_json))
    elif args.command == "handoff":
        result = build_human_handoff_packet(args.kind, _load_cli_json(args.decision_json), _load_cli_json(args.issue_json))
    else:
        result = tool_authority_assessment(_load_cli_json(args.action_json))

    print(json.dumps(result, ensure_ascii=False, sort_keys=True, allow_nan=False))
    return int(args.command == "gate" and args.require_go and result["verdict"] != "GO")
