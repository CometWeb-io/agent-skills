from __future__ import annotations

from typing import Any

from .constants import ROLE_REGISTRY
from .util import (
    _boolean,
    _clamp01,
    _dedupe,
    _jaccard,
    _rows,
    _sample_strength,
    _setish,
    _strings,
    _unit_interval,
)

def evidence_coverage_report(rows: list[dict[str, Any]], critical_areas: list[str]) -> dict[str, Any]:
    areas = _dedupe([str(x) for x in critical_areas if x]) or ["other"]
    per_area: dict[str, float] = {}
    per_area_unknown: dict[str, int] = {}
    all_groups: set[str] = set()
    for area in areas:
        best_by_group: dict[str, float] = {}
        unknown_count = 0
        for row in rows:
            if not row.get("accepted") or row.get("critical_area") != area:
                continue
            raw_group = str(row.get("independence_group") or "").strip()
            quality = _clamp01(row.get("source_quality", 0.5))
            directness = _clamp01(row.get("directness", 0.5))
            independence_confidence = _clamp01(row.get("independence_confidence", 1.0 if raw_group else 0.35))
            weight = quality * directness * (0.5 + 0.5 * independence_confidence)
            if raw_group:
                group = raw_group[:120]
            else:
                group = f"unknown_independence:{area}"
                unknown_count += 1
                weight *= 0.60
            best_by_group[group] = max(best_by_group.get(group, 0.0), weight)
            all_groups.add(group)
        remaining = 1.0
        for weight in best_by_group.values():
            remaining *= 1.0 - min(0.85, weight)
        score = 1.0 - remaining if best_by_group else 0.0
        if unknown_count and not any(not g.startswith("unknown_independence:") for g in best_by_group):
            score = min(score, 0.55)
        per_area[area] = round(score, 6)
        per_area_unknown[area] = unknown_count
    critical_gap = min(areas, key=lambda a: (per_area[a], areas.index(a)))
    overall = sum(per_area.values()) / len(per_area)
    return {
        "overall": round(overall, 6),
        "per_area": per_area,
        "critical_gap": critical_gap,
        "independent_source_count": len([g for g in all_groups if not g.startswith("unknown_independence:")]),
        "unknown_independence_sources": sum(per_area_unknown.values()),
        "unknown_independence_by_area": per_area_unknown,
    }


def find_double_crux(memos: list[dict[str, Any]]) -> dict[str, Any]:
    by_key: dict[str, list[dict[str, Any]]] = {}
    for memo in memos:
        for assumption in memo.get("assumptions") or []:
            key = str(assumption.get("key") or assumption.get("assumption_key") or "").strip()
            if not key:
                continue
            by_key.setdefault(key, []).append({
                "expert_id": str(memo.get("expert_id") or memo.get("role_id") or ""),
                "vote": memo.get("vote"),
                "value": str(assumption.get("value") or assumption.get("position") or "")[:200],
                "importance": _clamp01(assumption.get("importance", 0.5)),
                "uncertainty": _clamp01(assumption.get("uncertainty", 0.5)),
            })
    candidates = []
    for key, entries in by_key.items():
        values = {e["value"] for e in entries}
        votes = {e["vote"] for e in entries}
        if len(entries) < 2 or len(values) < 2 or len(votes) < 2:
            continue
        importance = sum(e["importance"] for e in entries) / len(entries)
        uncertainty = sum(e["uncertainty"] for e in entries) / len(entries)
        score = importance * (0.5 + 0.5 * uncertainty)
        candidates.append((score, importance, key, entries))
    if not candidates:
        return {"assumption_key": None, "experts": [], "positions": [], "importance": 0.0, "crux_score": 0.0}
    candidates.sort(key=lambda x: (-x[0], x[2]))
    score, importance, key, entries = candidates[0]
    return {
        "assumption_key": key,
        "experts": sorted({e["expert_id"] for e in entries if e["expert_id"]}),
        "positions": [{"expert_id": e["expert_id"], "value": e["value"], "vote": e["vote"]} for e in entries],
        "importance": round(importance, 6),
        "crux_score": round(score, 6),
    }


def consensus_share(votes: list[str]) -> float:
    usable = [str(v) for v in votes if v]
    if not usable:
        return 0.0
    counts = {v: usable.count(v) for v in set(usable)}
    return max(counts.values()) / len(usable)


def consensus_report(memos: list[dict[str, Any]], same_model_baseline: float = 0.25) -> dict[str, Any]:
    usable = [m for m in memos if m.get("vote")]
    n = len(usable)
    if not n:
        return {
            "raw_consensus": 0.0, "adjusted_consensus": 0.0, "majority_vote": None,
            "average_pairwise_correlation": 0.0, "effective_independent_perspectives": 0.0,
        }
    votes = [str(m["vote"]) for m in usable]
    counts = {v: votes.count(v) for v in set(votes)}
    majority = sorted(counts.items(), key=lambda x: (-x[1], x[0]))[0][0]
    raw = counts[majority] / n
    correlations = []
    baseline = _clamp01(same_model_baseline)
    for i in range(n):
        for j in range(i + 1, n):
            a, b = usable[i], usable[j]
            fw = _jaccard(_setish(a.get("frameworks") or a.get("framework_ids")), _setish(b.get("frameworks") or b.get("framework_ids")))
            src = _jaccard(_setish(a.get("independence_groups")), _setish(b.get("independence_groups")))
            claims = _jaccard(_setish(a.get("claim_ids") or a.get("unique_claim_ids")), _setish(b.get("claim_ids") or b.get("unique_claim_ids")))
            overlap = 0.30 * fw + 0.45 * src + 0.25 * claims
            correlations.append(max(baseline, overlap))
    avg_corr = sum(correlations) / len(correlations) if correlations else baseline
    effective_n = n / (1.0 + max(0, n - 1) * avg_corr)
    independence_ratio = min(1.0, effective_n / n)
    adjusted = 0.5 + (raw - 0.5) * independence_ratio
    return {
        "raw_consensus": round(raw, 6),
        "adjusted_consensus": round(_clamp01(adjusted), 6),
        "majority_vote": majority,
        "average_pairwise_correlation": round(avg_corr, 6),
        "effective_independent_perspectives": round(effective_n, 6),
        "perspective_count": n,
    }


def minority_sentinel(memos: list[dict[str, Any]]) -> dict[str, Any]:
    report = consensus_report(memos)
    majority = report.get("majority_vote")
    protected = []
    for memo in memos:
        if not memo.get("vote") or memo.get("vote") == majority:
            continue
        peers = [m for m in memos if m is not memo]
        peer_sources = set().union(*[_setish(m.get("independence_groups")) for m in peers]) if peers else set()
        own_sources = _setish(memo.get("independence_groups"))
        unique_sources = own_sources - peer_sources
        peer_assumptions = set()
        for peer in peers:
            peer_assumptions |= {str(a.get("key") or a.get("assumption_key")) for a in (peer.get("assumptions") or []) if a.get("key") or a.get("assumption_key")}
        own_assumptions = [a for a in (memo.get("assumptions") or []) if a.get("key") or a.get("assumption_key")]
        unique_high_risk = 0
        for assumption in own_assumptions:
            key = str(assumption.get("key") or assumption.get("assumption_key"))
            risk = _clamp01(assumption.get("importance", 0.5)) * _clamp01(assumption.get("uncertainty", 0.5))
            if key not in peer_assumptions and risk >= 0.35:
                unique_high_risk += 1
        role_id = str(memo.get("expert_id") or memo.get("role_id") or "")
        role_class = memo.get("role_class") or ROLE_REGISTRY.get(role_id, {}).get("class")
        gate_bonus = 0.35 if role_class == "gatekeeper" else 0.0
        score = min(1.0, 0.25 * min(2, len(unique_sources)) + 0.25 * min(2, unique_high_risk) + gate_bonus + 0.15 * _clamp01(memo.get("decision_impact", 0.5)))
        if score >= 0.35:
            protected.append({
                "expert_id": role_id,
                "vote": memo.get("vote"),
                "protection_score": round(score, 6),
                "unique_evidence_groups": sorted(unique_sources)[:5],
                "unique_high_risk_assumptions": unique_high_risk,
                "role_class": role_class or "unknown",
            })
    protected.sort(key=lambda x: (-x["protection_score"], x["expert_id"]))
    return {"majority_vote": majority, "protected_minority": protected, "must_surface": bool(protected)}


def detect_consensus_failure(votes: list[str], decision_quality: str | None,
                             outcome: str | None, outcome_attribution: list[str] | None = None) -> bool:
    if consensus_share(votes) <= 0.80:
        return False
    attrs = set(outcome_attribution or [])
    thesis_failure = decision_quality == "Bad" or "thesis_wrong" in attrs
    return bool(thesis_failure and outcome in {"Failure", "Mixed"})


def assumption_risk(importance: float, uncertainty: float) -> float:
    return round(_clamp01(importance) * _clamp01(uncertainty), 6)


def decompose_confidence(dimensions: dict[str, Any], binding_dimensions: list[str] | None = None) -> dict[str, Any]:
    if not isinstance(dimensions, dict):
        raise ValueError("dimensions must be an object")
    binding = _strings(binding_dimensions if binding_dimensions is not None else [], "binding_dimensions")
    clean = {k: _unit_interval(v, "confidence dimension") for k, v in dimensions.items()}
    if any(not isinstance(k, str) or not k.strip() for k in clean):
        raise ValueError("dimension names must be nonempty strings")
    missing = sorted(set(binding) - clean.keys())
    default_weights = {
        "thesis": 0.28, "evidence": 0.22, "execution": 0.18, "financial": 0.10,
        "legal": 0.08, "security": 0.06, "privacy": 0.04, "timing": 0.04,
    }
    weights = {k: default_weights.get(k, 0.05) for k in clean}
    total = sum(weights.values()) or 1.0
    weighted = sum(clean[k] * weights[k] for k in clean) / total
    if missing:
        weighted = 0.0
    elif binding:
        weighted = min(weighted, min(clean[b] for b in binding) + 0.10)
    return {
        "dimensions": {k: round(v, 6) for k, v in clean.items()},
        "overall": round(weighted, 6), "binding_dimensions": binding,
        "missing_binding_dimensions": missing,
        "weakest_dimension": min(clean, key=lambda k: (clean[k], k)) if clean else None,
    }


def value_of_information(probability_decision_changes: float, value_difference: float,
                         information_cost: float, delay_cost: float = 0.0) -> dict[str, Any]:
    p = _clamp01(probability_decision_changes)
    value = max(0.0, float(value_difference or 0.0))
    cost = max(0.0, float(information_cost or 0.0))
    delay = max(0.0, float(delay_cost or 0.0))
    gross = p * value
    net = gross - cost - delay
    return {
        "probability_decision_changes": round(p, 6),
        "gross_value_of_information": round(gross, 6),
        "information_cost": round(cost, 6),
        "delay_cost": round(delay, 6),
        "net_value_of_information": round(net, 6),
        "recommendation": "GATHER_EVIDENCE" if net > 0 else "DECIDE_NOW",
    }


def deliberation_stop(expected_information_gain: float, deliberation_cost: float,
                      no_novelty_rounds: int = 0, unresolved_mandatory_gate: bool = False,
                      critical_gap_open: bool = False) -> dict[str, Any]:
    gain = max(0.0, float(expected_information_gain or 0.0))
    cost = max(0.0, float(deliberation_cost or 0.0))
    if unresolved_mandatory_gate:
        stop = False
        reason = "mandatory_gate_unresolved"
    elif critical_gap_open and gain > 0:
        stop = gain <= cost and int(no_novelty_rounds) >= 2
        reason = "critical_gap_but_low_marginal_value" if stop else "critical_gap_still_worth_investigating"
    elif int(no_novelty_rounds) >= 2:
        stop = True
        reason = "information_saturation"
    else:
        stop = gain <= cost
        reason = "marginal_gain_below_cost" if stop else "continue_positive_information_value"
    return {
        "stop": bool(stop),
        "reason": reason,
        "expected_information_gain": round(gain, 6),
        "deliberation_cost": round(cost, 6),
        "no_novelty_rounds": int(no_novelty_rounds),
    }

def build_experiment_spec(hypothesis: str, metric: str, baseline: str, pass_threshold: str,
                          fail_threshold: str, duration: str, budget: str, sample: str,
                          guardrails: list[str] | None = None, minimum_detectable_effect: str = "",
                          kill_criteria: list[str] | None = None, evidence_gap_addressed: str = "",
                          assumption_key: str = "", owner: str = "", review_date: str = "") -> dict[str, Any]:
    return {
        "hypothesis": str(hypothesis)[:500],
        "primary_metric": str(metric)[:200],
        "metric": str(metric)[:200],
        "baseline": str(baseline)[:200],
        "target": str(pass_threshold)[:200],
        "pass_threshold": str(pass_threshold)[:200],
        "fail_threshold": str(fail_threshold)[:200],
        "minimum_detectable_effect": str(minimum_detectable_effect)[:200],
        "duration": str(duration)[:120],
        "budget": str(budget)[:120],
        "sample": str(sample)[:200],
        "guardrails": [str(x)[:200] for x in (guardrails or [])[:8]],
        "kill_criteria": [str(x)[:200] for x in (kill_criteria or [])[:8]],
        "decision_rule": {"GO": str(pass_threshold)[:200], "NO-GO": str(fail_threshold)[:200], "otherwise": "DEFER"},
        "evidence_gap_addressed": str(evidence_gap_addressed)[:300],
        "assumption_key": str(assumption_key)[:120],
        "owner": str(owner)[:120],
        "review_date": str(review_date)[:40],
    }

def information_gain_score(expert_vote: str, peer_votes: list[str], novel_claims: int = 0, shared_claims: int = 0,
                           independence: float | None = None, decision_impact: float = 0.5,
                           later_validation: float | None = None) -> float:
    peers = [str(v) for v in peer_votes if v]
    surprise = 1.0 - peers.count(str(expert_vote)) / len(peers) if peers else 0.5
    novel = max(0, int(novel_claims))
    shared = max(0, int(shared_claims))
    novelty = novel / (novel + shared) if (novel + shared) else 0.0
    independence_score = _clamp01(independence if independence is not None else surprise)
    validation = _clamp01(later_validation if later_validation is not None else 0.5)
    impact = _clamp01(decision_impact)
    return round(_clamp01(0.30 * novelty + 0.30 * independence_score + 0.25 * impact + 0.15 * validation), 6)


def framework_usefulness(exposed_assumption: bool, changed_vote: bool, identified_test: bool,
                         exposed_risk: bool, rejected: bool) -> dict[str, Any]:
    if rejected:
        score = 0.0
    else:
        score = 0.25 * sum(bool(x) for x in (exposed_assumption, changed_vote, identified_test, exposed_risk))
    return {"utility_score": round(score, 6), "rejected": bool(rejected)}


def framework_usefulness_report(rows: list[dict[str, Any]], framework_id: str) -> dict[str, Any]:
    usable = [row for row in rows if row.get("memory_status") == "Complete" and row.get("framework") == framework_id]
    n = len(usable)
    mean_utility = sum(_clamp01(row.get("utility_score", 0)) for row in usable) / n if n else 0.0
    return {"framework_id": framework_id, "sample_size": n, "sample_strength": _sample_strength(n), "mean_utility": round(mean_utility, 6)}


def information_gain_report(rows: list[dict[str, Any]], expert_id: str) -> dict[str, Any]:
    usable = [row for row in rows if row.get("memory_status") == "Complete" and (row.get("expert") == expert_id or row.get("expert_id") == expert_id)]
    n = len(usable)
    mean_gain = sum(_clamp01(row.get("information_gain", 0)) for row in usable) / n if n else 0.0
    if n < 5:
        signal = "insufficient"
    elif mean_gain < 0.20:
        signal = "redundant"
    elif mean_gain >= 0.55:
        signal = "high_value"
    else:
        signal = "useful"
    return {"expert_id": expert_id, "sample_size": n, "sample_strength": _sample_strength(n), "mean_information_gain": round(mean_gain, 6), "signal": signal}


def should_run_counterfactual(mode: str, confidence: float, required_confidence_value: float,
                              consensus_value: float) -> bool:
    if str(mode).upper() == "DEEP":
        return True
    if str(mode).upper() == "STANDARD" and (
        _clamp01(confidence) < _clamp01(required_confidence_value) or _clamp01(consensus_value) > 0.80
    ):
        return True
    return False

def contradiction_coverage(claims: list[dict[str, Any]]) -> dict[str, Any]:
    material, tested, unresolved, critical_unresolved = [], [], [], []
    for c in _rows(claims, "claims"):
        flags = {n: _boolean(c.get(n, n == "material"), n) for n in
                 ("material", "contradiction_tested", "unresolved_contradiction", "contradiction_resolved")}
        count = c.get("opposing_evidence_count", 0)
        if type(count) is not int or count < 0:
            raise ValueError("opposing_evidence_count must be a nonnegative integer")
        importance = _unit_interval(c.get("importance", 0.5), "importance")
        if not flags["material"]:
            continue
        material.append(c)
        if flags["contradiction_tested"]:
            tested.append(c)
        # Opposition is not erased by omitting the search-completed flag.
        if flags["unresolved_contradiction"] or (count > 0 and not flags["contradiction_resolved"]):
            unresolved.append(c)
            if importance >= 0.8:
                critical_unresolved.append(c)
    return {
        "material_claims": len(material), "contradiction_tested": len(tested),
        "contradiction_coverage": round(len(tested) / len(material), 6) if material else None,
        "unresolved_contradictions": len(unresolved),
        "critical_unresolved_claim_ids": [c.get("claim_id") or c.get("id") for c in critical_unresolved],
        "decision_ready": bool(material) and len(tested) == len(material) and not unresolved,
        "verification_scope": "declared_claim_records_only",
    }


def independence_grade(memo: dict[str, Any], peers: list[dict[str, Any]]) -> str:
    if bool(memo.get("human_external", False)) or str(memo.get("actor_type") or "").lower() == "human":
        return "I4"
    def declared(row: dict[str, Any]) -> tuple[str, str] | None:
        """Provider/model pair, or None when either is undeclared.

        Absence is unknown independence, not a distinct origin — see
        references/evidence-policy.md. Folding a missing field into the literal
        "unknown" and then comparing it made an undeclared adviser differ from a
        declared one, so it scored I3 (0.75) instead of I1 (0.25) and tripled the
        panel's measured independence on nothing but a blank field.
        """
        provider = str(row.get("provider") or "").strip()
        model = str(row.get("model_family") or row.get("model") or "").strip()
        return (provider, model) if provider and model else None

    mine = declared(memo)
    others = [p for p in peers if p is not memo and (p.get("expert_id") or p.get("id")) != (memo.get("expert_id") or memo.get("id"))]
    if mine and any((theirs := declared(p)) is not None and theirs != mine for p in others):
        return "I3"
    groups = _setish(memo.get("independence_groups"))
    peer_groups = set().union(*[_setish(p.get("independence_groups")) for p in others]) if others else set()
    if groups and peer_groups and not (groups & peer_groups):
        return "I2"
    if str(memo.get("expert_id") or memo.get("role") or "") and others:
        return "I1"
    return "I0"


def independence_grade_report(memos: list[dict[str, Any]]) -> dict[str, Any]:
    grades = []
    for memo in memos:
        grades.append({"expert_id": memo.get("expert_id") or memo.get("id"), "grade": independence_grade(memo, memos)})
    counts = {grade: sum(1 for r in grades if r["grade"] == grade) for grade in ("I0", "I1", "I2", "I3", "I4")}
    numeric = {"I0": 0.0, "I1": 0.25, "I2": 0.5, "I3": 0.75, "I4": 1.0}
    mean = sum(numeric[r["grade"]] for r in grades) / len(grades) if grades else 0.0
    return {"grades": grades, "counts": counts, "mean_independence_grade": round(mean, 6)}
