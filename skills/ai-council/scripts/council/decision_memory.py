from __future__ import annotations

import hashlib
import json
import math
from typing import Any

from .constants import COUNCIL_VERSION, _MEMORY_ALLOWLIST_V4
from .util import (
    _aware_time,
    _boolean,
    _clamp01,
    _finite_number,
    _is_non_thesis_row,
    _norm,
    _parse_date,
    _recency_factor,
    _rows,
    _sample_strength,
    _setish,
    _strings,
    _unit_interval,
)

def rank_analogies(current: dict[str, Any], history: list[dict[str, Any]], limit: int = 3) -> list[dict[str, Any]]:
    scored = []
    current_fw = set(current.get("framework_ids") or [])
    current_experts = set(current.get("expert_ids") or [])
    current_regimes = set(current.get("regime_tags") or [])
    for row in history:
        if row.get("memory_status") != "Complete" or row.get("outcome") in (None, "Pending"):
            continue
        quality_factor = 0.65 if row.get("decision_quality") in {"Pending", "Unclear", None} else 1.0
        score = 0.0
        if row.get("domain") == current.get("primary_domain"):
            score += 5
        if row.get("decision_kind") == current.get("decision_kind"):
            score += 4
        if row.get("decision_type") == current.get("decision_type"):
            score += 4
        if row.get("risk") == current.get("risk_level"):
            score += 2
        if row.get("reversibility") == current.get("reversibility"):
            score += 2
        score += min(3, len(current_fw & set(row.get("framework_ids") or [])))
        score += min(2, len(current_experts & set(row.get("expert_ids") or [])))
        regime_overlap = len(current_regimes & set(row.get("regime_tags") or []))
        score += min(4, 2 * regime_overlap)
        recency = _recency_factor(row.get("updated_at"), current.get("as_of"))
        score = score * quality_factor + 2.0 * recency
        scored.append({
            "decision_key": row.get("decision_key", ""), "score": round(score, 6),
            "outcome": row.get("outcome"), "resolved_vote": row.get("resolved_vote"),
            "domain": row.get("domain"), "decision_kind": row.get("decision_kind"),
            "decision_type": row.get("decision_type"), "decision_quality": row.get("decision_quality"),
            "outcome_lesson": str(row.get("outcome_lesson") or "")[:500],
            "updated_at": row.get("updated_at") or "", "regime_overlap": regime_overlap,
            "recency_factor": round(recency, 6),
        })
    scored.sort(key=lambda x: (-x["score"], x["decision_key"]))
    return scored[:max(0, min(3, int(limit)))]

def calibration_report(rows: list[dict[str, Any]], expert_id: str, domain: str | None = None,
                       decision_kind: str | None = None, regime_tags: list[str] | None = None) -> dict[str, Any]:
    candidates = [
        row for row in rows
        if row.get("memory_status") == "Complete"
        and row.get("outcome") not in (None, "Pending")
        and (row.get("expert") == expert_id or row.get("expert_id") == expert_id)
        and (domain is None or row.get("domain") == domain)
        and (decision_kind is None or row.get("decision_kind") == decision_kind)
        and row.get("resolved_vote")
    ]
    excluded_non_thesis = sum(1 for row in candidates if _is_non_thesis_row(row))
    usable = [row for row in candidates if not _is_non_thesis_row(row)]
    if regime_tags:
        wanted = set(regime_tags)
        regime_matches = [row for row in usable if wanted & set(row.get("regime_tags") or [])]
        if len(regime_matches) >= 5:
            usable = regime_matches
    n = len(usable)
    if n == 0:
        return {
            "expert_id": expert_id, "sample_size": 0, "sample_strength": "none", "hit_rate": 0.0,
            "mean_confidence": 0.0, "brier_like_error": 0.0, "flags": [], "excluded_non_thesis": excluded_non_thesis,
        }
    correct = [1.0 if row.get("blind_vote") == row.get("resolved_vote") else 0.0 for row in usable]
    confidence = [_clamp01(row.get("blind_confidence") or 0) for row in usable]
    hit = sum(correct) / n
    mean_conf = sum(confidence) / n
    brier = sum((c - y) ** 2 for c, y in zip(confidence, correct, strict=True)) / n
    flags = []
    if mean_conf - hit >= 0.15:
        flags.append("overconfidence")
    if hit - mean_conf >= 0.15:
        flags.append("underconfidence")
    go_share = sum(1 for row in usable if row.get("blind_vote") == "GO") / n
    test_share = sum(1 for row in usable if row.get("blind_vote") == "TEST") / n
    if go_share >= 0.7:
        flags.append("go_bias")
    if test_share >= 0.7:
        flags.append("test_bias")
    return {
        "expert_id": expert_id, "sample_size": n, "sample_strength": _sample_strength(n),
        "hit_rate": round(hit, 6), "mean_confidence": round(mean_conf, 6),
        "brier_like_error": round(brier, 6), "flags": flags,
        "excluded_non_thesis": excluded_non_thesis,
    }

def infer_regime_tags(context: dict[str, Any]) -> list[str]:
    mappings = [
        ("company_stage", {"early": "early_stage", "early_stage": "early_stage", "growth": "growth_stage", "growth_stage": "growth_stage", "mature": "mature_stage", "mature_stage": "mature_stage"}),
        ("market_volatility", {"stable": "stable_market", "stable_market": "stable_market", "volatile": "volatile_market", "volatile_market": "volatile_market"}),
        ("geography", {"local": "local", "international": "international"}),
        ("business_model", {"b2b": "b2b", "b2c": "b2c"}),
        ("motion", {"self_serve": "self_serve", "sales_led": "sales_led"}),
    ]
    out = []
    for key, mapping in mappings:
        value = str(context.get(key) or "").strip().casefold()
        if value in mapping:
            out.append(mapping[value])
    return out


def source_provenance_summary(rows: list[dict[str, Any]]) -> dict[str, str]:
    classes = ["CURRENT_FACT", "PRIVATE_KNOWLEDGE", "DECISION_MEMORY", "FRAMEWORK", "LIVE_WEB", "EXPERT_JUDGMENT"]
    result = {}
    for source_class in classes:
        weights = [_clamp01(row.get("evidence_weight", 0)) for row in rows if row.get("accepted") and row.get("source_class") == source_class]
        strength = max(weights) if weights else 0.0
        if strength >= 0.8:
            label = "HIGH"
        elif strength >= 0.4:
            label = "MEDIUM"
        elif strength > 0:
            label = "LOW"
        else:
            label = "NONE"
        result[source_class] = label
    return result


def consensus_failure_patterns(rows: list[dict[str, Any]]) -> dict[str, Any]:
    failures = [row for row in rows if row.get("memory_status") == "Complete" and row.get("consensus_failure")]
    framework_counts: dict[str, int] = {}
    expert_counts: dict[str, int] = {}
    for row in failures:
        for framework in row.get("framework_ids") or []:
            framework_counts[str(framework)] = framework_counts.get(str(framework), 0) + 1
        for expert in row.get("expert_ids") or []:
            expert_counts[str(expert)] = expert_counts.get(str(expert), 0) + 1
    return {
        "failure_count": len(failures),
        "top_frameworks": sorted(framework_counts.items(), key=lambda x: (-x[1], x[0]))[:5],
        "top_experts": sorted(expert_counts.items(), key=lambda x: (-x[1], x[0]))[:10],
    }


def learning_weight(decision_quality: str | None, outcome_attribution: list[str] | None = None) -> float:
    attrs = set(outcome_attribution or [])
    if attrs & {"execution_failure", "external_shock", "wrong_timing"} and not attrs & {"thesis_wrong", "thesis_correct"}:
        return 0.0
    if decision_quality in {"Good", "Bad"}:
        return 1.0
    if decision_quality == "Unclear":
        return 0.25
    return 0.0


def due_reviews(rows: list[dict[str, Any]], today: str) -> list[dict[str, Any]]:
    now = _parse_date(today)
    if not now:
        return []
    due = []
    for row in rows:
        if row.get("memory_status") != "Complete" or row.get("outcome") != "Pending":
            continue
        dates = row.get("review_dates") or [row.get("review_date")]
        parsed = [_parse_date(d) for d in dates if d]
        if any(d and d.date() <= now.date() for d in parsed):
            due.append(row)
    due.sort(key=lambda row: (str(row.get("review_date") or ""), str(row.get("decision_key") or "")))
    return due


def council_health(decisions: list[dict[str, Any]], votes: list[dict[str, Any]], experiments: list[dict[str, Any]],
                   process_rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    complete = [d for d in decisions if d.get("memory_status") == "Complete"]
    resolved = [d for d in complete if d.get("outcome") not in (None, "Pending")]
    verdict_counts = {v: sum(1 for d in complete if d.get("verdict") == v) for v in ("GO", "NO-GO", "TEST", "DEFER")}
    process_rows = process_rows or []
    return {
        "council_version": COUNCIL_VERSION,
        "total_decisions": len(complete),
        "resolved_decisions": len(resolved),
        "good_decisions": sum(1 for d in resolved if d.get("decision_quality") == "Good"),
        "bad_decisions": sum(1 for d in resolved if d.get("decision_quality") == "Bad"),
        "failed_outcomes": sum(1 for d in resolved if d.get("outcome") == "Failure"),
        "consensus_failures": sum(1 for d in resolved if bool(d.get("consensus_failure"))),
        "verdict_counts": verdict_counts,
        "pending_experiments": sum(1 for e in experiments if e.get("memory_status") == "Complete" and e.get("outcome") == "Pending"),
        "resolved_votes": sum(1 for v in votes if v.get("memory_status") == "Complete" and v.get("outcome") not in (None, "Pending")),
        "process_events": len([r for r in process_rows if r.get("memory_status") == "Complete"]),
        "router_misses": sum(1 for r in process_rows if r.get("memory_status") == "Complete" and r.get("event_type") == "router_miss"),
        "minority_vindications": sum(1 for r in process_rows if r.get("memory_status") == "Complete" and r.get("event_type") == "minority_vindicated"),
    }

def sanitize_memory_record(raw: dict[str, Any]) -> dict[str, Any]:
    clean = {k: raw[k] for k in _MEMORY_ALLOWLIST_V4 if k in raw}
    clean["outcome_lesson"] = str(clean.get("outcome_lesson") or "")[:500]
    clean["framework_ids"] = [str(x) for x in clean.get("framework_ids") or []][:6]
    clean["expert_ids"] = [str(x) for x in clean.get("expert_ids") or []][:20]
    clean["regime_tags"] = [str(x) for x in clean.get("regime_tags") or []][:12]
    clean["outcome_attribution"] = [str(x) for x in clean.get("outcome_attribution") or []][:6]
    clean["missing_perspectives"] = [str(x) for x in clean.get("missing_perspectives") or []][:20]
    clean["review_dates"] = [str(x) for x in clean.get("review_dates") or []][:8]
    clean["snapshot_hash"] = str(clean.get("snapshot_hash") or "")[:80]
    clean["double_crux"] = str(clean.get("double_crux") or "")[:300]
    clean["evidence_critical_gap"] = str(clean.get("evidence_critical_gap") or "")[:120]
    clean["gate_statuses"] = {str(k)[:80]: str(v)[:40] for k, v in dict(clean.get("gate_statuses") or {}).items()}
    for key in ("confidence", "evidence_coverage", "required_confidence", "decision_value_score", "adjusted_consensus", "effective_independent_perspectives"):
        if key in clean:
            clean[key] = _clamp01(clean[key]) if key != "effective_independent_perspectives" else max(0.0, float(clean[key] or 0))
    return clean


def make_decision_key(question: str, date_key: str, context: dict[str, Any] | None = None) -> str:
    stable_context = {
        "decision_type": (context or {}).get("decision_type"),
        "options": (context or {}).get("options"),
        "objective": (context or {}).get("objective"),
        "jurisdictions": (context or {}).get("jurisdictions"),
    }
    payload = json.dumps({
        "date": date_key.strip(), "question": _norm(question).strip(), "context": stable_context,
    }, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "dc-" + hashlib.sha256(payload).hexdigest()[:16]


def snapshot_hash(snapshot: dict[str, Any], version: int = 3) -> str:
    payload = {"snapshot_version": int(version), "snapshot": snapshot}
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return "snap-" + hashlib.sha256(canonical).hexdigest()


def champion_challenger(champion: dict[str, Any], challenger: dict[str, Any]) -> dict[str, Any]:
    benefit_keys = [
        "critical_assumptions_found", "material_risks_found", "evidence_gaps_found", "minority_preservation",
        "legal_constraints_found", "test_quality", "calibration_score",
    ]
    cost_keys = ["latency", "token_cost", "tool_calls"]

    def score(row: dict[str, Any]) -> float:
        benefit = sum(_clamp01(row.get(k, 0)) for k in benefit_keys) / len(benefit_keys)
        cost = sum(_clamp01(row.get(k, 0)) for k in cost_keys) / len(cost_keys)
        return 0.8 * benefit - 0.2 * cost

    c_score = score(champion)
    h_score = score(challenger)
    delta = h_score - c_score
    return {
        "champion_score": round(c_score, 6),
        "challenger_score": round(h_score, 6),
        "delta": round(delta, 6),
        "winner": "challenger" if delta > 0.03 else ("champion" if delta < -0.03 else "tie"),
        "promotion_recommended": bool(delta > 0.03),
    }

def evaluate_watch_dependency(dependency: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(dependency, dict):
        raise ValueError("dependency must be an object")
    op = dependency.get("operator", "changed")
    op = op.lower() if isinstance(op, str) else "unknown"
    previous, current, threshold = (dependency.get(n) for n in ("previous", "current", "threshold"))
    materiality = _unit_interval(dependency.get("materiality", 0.5), "materiality")
    keys = _strings(dependency.get("assumption_keys", []), "assumption_keys")
    triggered, status, reason = None, "UNKNOWN", "unusable observation"
    try:
        if "triggered" in dependency:
            _boolean(dependency["triggered"], "triggered")
        if op == "changed":
            if previous is None or current is None:
                raise ValueError("both observations are required")
            # JSON equality is typed: boolean true is not the numeric value 1.
            before = json.dumps(previous, sort_keys=True, allow_nan=False)
            after = json.dumps(current, sort_keys=True, allow_nan=False)
            triggered = before != after
        elif op in {"gt", "gte", "lt", "lte", "pct_change_gt"}:
            c = _finite_number(current, "current")
            t = _finite_number(threshold, "threshold")
            if op == "pct_change_gt":
                p = _finite_number(previous, "previous")
                if p == 0 or t < 0:
                    raise ValueError("percentage change requires nonzero baseline and nonnegative threshold")
                change = abs((c - p) / p)
                if not math.isfinite(change):
                    raise ValueError("percentage change overflow")
                triggered = change > t
            else:
                triggered = {"gt": c > t, "gte": c >= t, "lt": c < t, "lte": c <= t}[op]
        else:
            raise ValueError("unknown watch operator")
        status, reason = "OBSERVED", "comparison completed on supplied observations"
    except (ValueError, TypeError, OverflowError):
        triggered, status, reason = None, "UNKNOWN", "missing, invalid or incomparable observation"
    return {
        "dependency_id": dependency.get("dependency_id") or dependency.get("id"),
        "type": dependency.get("type") or "generic", "operator": op,
        "triggered": triggered, "observation_status": status, "materiality": materiality,
        "assumption_keys": keys, "previous": previous, "current": current,
        "threshold": threshold, "reason": reason,
    }


def decision_validity_overlay(decision: dict[str, Any], dependencies: list[dict[str, Any]], as_of: str) -> dict[str, Any]:
    now = _aware_time(as_of, "as_of")
    if not isinstance(decision, dict):
        raise ValueError("decision must be an object")
    stale = decision.get("material_stale_evidence_count", 0)
    if type(stale) is not int or stale < 0:
        raise ValueError("material_stale_evidence_count must be a nonnegative integer")
    evaluated = [evaluate_watch_dependency(dep) for dep in _rows(dependencies, "dependencies")]
    triggered = [d for d in evaluated if d["triggered"] is True]
    unknown = [d for d in evaluated if d["observation_status"] == "UNKNOWN"]
    high = [d for d in triggered if d["materiality"] >= 0.7]
    status, reasons = "VALID", []
    if high:
        status = "REOPEN"
        reasons.append("high-materiality watch dependency changed")
    elif stale:
        status = "STALE"
    elif triggered or unknown or not evaluated:
        status = "WATCH"
    if stale:
        reasons.append("material evidence is stale")
    if triggered and not high:
        reasons.append("watch dependency changed")
    if unknown or not evaluated:
        reasons.append("watch coverage is incomplete or observation is unknown")
    if decision.get("next_revalidation_at") is not None:
        try:
            due = now >= _aware_time(decision["next_revalidation_at"], "next_revalidation_at")
        except ValueError:
            due = True
            reasons.append("invalid next revalidation timestamp")
        if due:
            if status == "VALID":
                status = "WATCH"
            reasons.append("scheduled revalidation is due")
    if decision.get("superseded_by"):
        status = "SUPERSEDED"
        reasons.append("decision explicitly superseded")
    return {
        "status": status, "as_of": as_of,
        "reason": "; ".join(reasons) or "no change in supplied dependencies",
        "triggered_dependencies": triggered, "unknown_dependencies": unknown,
        "affected_assumptions": sorted({key for d in triggered + unknown for key in d["assumption_keys"]}),
        "revalidation_required": status in {"WATCH", "REOPEN", "STALE"},
        "evidence_authentication": "not_performed",
    }

def forecast_score_report(forecasts: list[dict[str, Any]]) -> dict[str, Any]:
    resolved, invalid, unresolved = [], [], []
    for index, row in enumerate(_rows(forecasts, "forecasts")):
        try:
            p = _unit_interval(row.get("probability"), "probability")
        except ValueError:
            invalid.append({"index": index, "reason": "invalid_probability"})
            continue
        outcome = row.get("outcome")
        if isinstance(outcome, str):
            outcome = {"1": 1, "true": 1, "yes": 1, "success": 1, "occurred": 1,
                       "0": 0, "false": 0, "no": 0, "failure": 0, "did_not_occur": 0}.get(outcome.lower())
        if type(outcome) not in (int, float, bool) or outcome not in (0, 1):
            unresolved.append(index)
            continue
        resolved.append((p, int(outcome)))
    accounting = {"input_count": len(forecasts), "invalid_count": len(invalid),
                  "unresolved_count": len(unresolved), "invalid_rows": invalid}
    if not resolved:
        return {**accounting, "n": 0, "sample_strength": "none", "brier_score": None, "calibration_error": None}
    brier = sum((p - y) ** 2 for p, y in resolved) / len(resolved)
    bins: dict[int, list[tuple[float, int]]] = {}
    for p, y in resolved:
        bucket = min(4, int(p * 5))
        bins.setdefault(bucket, []).append((p, y))
    cal = 0.0
    for vals in bins.values():
        avg_p = sum(p for p, _ in vals) / len(vals)
        avg_y = sum(y for _, y in vals) / len(vals)
        cal += abs(avg_p - avg_y) * (len(vals) / len(resolved))
    return {
        **accounting,
        "n": len(resolved),
        "sample_strength": _sample_strength(len(resolved)),
        "brier_score": round(brier, 6),
        "calibration_error": round(cal, 6),
        "mean_forecast": round(sum(p for p, _ in resolved) / len(resolved), 6),
        "base_rate": round(sum(y for _, y in resolved) / len(resolved), 6),
    }


def base_rate_report(rows: list[dict[str, Any]], decision_type: str, regime_tags: list[str] | None = None) -> dict[str, Any]:
    target_regimes = set(regime_tags or [])
    eligible = []
    for row in rows:
        if row.get("memory_status") != "Complete":
            continue
        if str(row.get("decision_type") or row.get("decision_kind") or "") != str(decision_type):
            continue
        if target_regimes:
            row_regimes = _setish(row.get("regime_tags"))
            if not (target_regimes & row_regimes):
                continue
        outcome = str(row.get("outcome") or "")
        if outcome not in {"Success", "Failure"}:
            continue
        eligible.append(1 if outcome == "Success" else 0)
    n = len(eligible)
    return {
        "decision_type": decision_type,
        "n": n,
        "sample_strength": _sample_strength(n),
        "success_base_rate": round(sum(eligible) / n, 6) if n else None,
        "usable_as_prior": n >= 5,
        "warning": None if n >= 5 else "insufficient resolved analogues; do not overfit the outside view",
    }


def portfolio_report(decisions: list[dict[str, Any]], capacities: dict[str, Any] | None = None) -> dict[str, Any]:
    capacities = dict(capacities or {})
    totals: dict[str, float] = {}
    ids = {str(d.get("decision_id") or d.get("decision_key") or d.get("id")) for d in decisions}
    missing_dependencies = []
    ranked = []
    for d in decisions:
        did = str(d.get("decision_id") or d.get("decision_key") or d.get("id"))
        claims = d.get("resource_claims") or {}
        total_claim = 0.0
        for resource, amount in claims.items():
            try:
                value = max(0.0, float(amount))
            except (TypeError, ValueError):
                value = 0.0
            totals[resource] = totals.get(resource, 0.0) + value
            total_claim += value
        for dep in d.get("depends_on") or []:
            if str(dep) not in ids:
                missing_dependencies.append({"decision_id": did, "missing_dependency": str(dep)})
        ev = float(d.get("expected_value") or 0.0)
        ranked.append({"decision_id": did, "expected_value": ev, "resource_claim_total": total_claim, "value_density": round(ev / (1.0 + total_claim), 6)})
    conflicts = []
    for resource, used in totals.items():
        if resource in capacities:
            try:
                cap = float(capacities[resource])
            except (TypeError, ValueError):
                continue
            if used > cap:
                conflicts.append({"resource": resource, "used": round(used, 6), "capacity": round(cap, 6), "over_by": round(used - cap, 6)})
    ranked.sort(key=lambda r: (-r["value_density"], -r["expected_value"], r["decision_id"]))
    return {"resource_totals": totals, "capacity_conflicts": conflicts, "missing_dependencies": missing_dependencies, "value_density_ranking": ranked}
