#!/usr/bin/env python3
"""Select an outreach slate or active design-partner cohort.

The greedy objective rewards candidate quality plus marginal weighted learning
coverage, while penalizing effort, risk, and duplicate learning profiles. It is a
transparent heuristic, not an optimizer that can replace product judgment.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any

RESEARCH_ELIGIBLE = {"PRIORITY_DISCOVERY", "DISCOVERY"}
ACTIVE_ELIGIBLE = {"PARTNER_READY"}
STATUS_BONUS = {
    "PRIORITY_DISCOVERY": 4.0,
    "DISCOVERY": 0.0,
    "PARTNER_READY": 4.0,
    "ALIGNMENT_REQUIRED": -8.0,
}


def _number(value: Any, name: str, lo: float | None = None, hi: float | None = None) -> float:
    try:
        x = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if math.isnan(x) or math.isinf(x):
        raise ValueError(f"{name} must be finite")
    if lo is not None and x < lo:
        raise ValueError(f"{name} must be >= {lo}")
    if hi is not None and x > hi:
        raise ValueError(f"{name} must be <= {hi}")
    return x


def _strict_bool(value: Any, name: str, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    raise ValueError(f"{name} must be boolean")


def _questions(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    raw = payload.get("questions")
    if raw is not None:
        if not isinstance(raw, list):
            raise ValueError("questions must be an array")
        for row in raw:
            if not isinstance(row, dict):
                raise ValueError("each question must be an object")
            qid = str(row.get("id") or "").strip()
            if not qid:
                raise ValueError("question id is required")
            out[qid] = {
                "weight": _number(row.get("weight", 1), f"question:{qid}.weight", 0.0),
                "desired_replications": int(_number(row.get("desired_replications", 1), f"question:{qid}.desired_replications", 1)),
                "must_cover": _strict_bool(row.get("must_cover"), f"question:{qid}.must_cover", False),
            }
    else:
        weights = payload.get("question_weights") or {}
        desired = payload.get("desired_replications") or {}
        if not isinstance(weights, dict) or not isinstance(desired, dict):
            raise ValueError("question_weights and desired_replications must be objects")
        ids = sorted(set(weights) | set(desired))
        for qid in ids:
            out[str(qid)] = {
                "weight": _number(weights.get(qid, 1), f"question:{qid}.weight", 0.0),
                "desired_replications": int(_number(desired.get(qid, 1), f"question:{qid}.desired_replications", 1)),
                "must_cover": False,
            }
    return out


def _coverage(candidate: dict[str, Any], question_ids: set[str]) -> dict[str, float]:
    raw = candidate.get("learning_coverage")
    if raw is None:
        raw = {str(q): 5 for q in (candidate.get("learning_questions") or [])}
    if not isinstance(raw, dict):
        raise ValueError(f"learning_coverage:{candidate.get('company')} must be an object")
    out: dict[str, float] = {}
    for qid, value in raw.items():
        qid = str(qid)
        if question_ids and qid not in question_ids:
            continue
        out[qid] = _number(value, f"learning_coverage:{candidate.get('company')}:{qid}", 0.0, 5.0)
    return out


def select(payload: dict[str, Any], selection_stage: str) -> dict[str, Any]:
    stage = selection_stage.lower()
    if stage not in {"outreach_slate", "active_cohort"}:
        raise ValueError("selection_stage must be outreach_slate or active_cohort")

    size = int(_number(payload.get("size", 5), "size", 1))
    max_per_segment_raw = payload.get("max_per_segment")
    max_per_segment = int(_number(max_per_segment_raw, "max_per_segment", 1)) if max_per_segment_raw is not None else None
    max_per_duplicate_key = int(_number(payload.get("max_per_duplicate_key", 2), "max_per_duplicate_key", 1))
    replication_threshold = _number(payload.get("replication_threshold", 3), "replication_threshold", 0, 5)
    include_alignment = _strict_bool(payload.get("include_alignment_required"), "include_alignment_required", False)

    questions = _questions(payload)
    question_ids = set(questions)
    eligible = set(RESEARCH_ELIGIBLE if stage == "outreach_slate" else ACTIVE_ELIGIBLE)
    if stage == "active_cohort" and include_alignment:
        eligible.add("ALIGNMENT_REQUIRED")

    candidates: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    for raw in payload.get("candidates") or []:
        if not isinstance(raw, dict):
            raise ValueError("each candidate must be an object")
        c = dict(raw)
        company = str(c.get("company") or c.get("candidate") or "").strip()
        if not company:
            raise ValueError("candidate company is required")
        c["company"] = company
        c["score"] = _number(c.get("score", 0), f"score:{company}", 0, 100)
        c["status"] = str(c.get("status") or "")
        c["segment"] = str(c.get("segment") or "unknown")
        c["duplicate_key"] = str(c.get("duplicate_key") or c["segment"] or company)
        c["effort"] = _number(c.get("effort", 0), f"effort:{company}", 0, 5)
        c["risk"] = _number(c.get("risk", 0), f"risk:{company}", 0, 5)
        c["learning_coverage"] = _coverage(c, question_ids)
        if c["status"] not in eligible:
            excluded.append({"company": company, "reason": f"status:{c['status'] or 'missing'}"})
            continue
        candidates.append(c)

    selected: list[dict[str, Any]] = []
    segment_counts: Counter[str] = Counter()
    duplicate_counts: Counter[str] = Counter()
    replication_counts: Counter[str] = Counter()
    remaining = list(candidates)
    total_weight = sum(q["weight"] for q in questions.values()) or 1.0

    while remaining and len(selected) < size:
        ranked: list[tuple[float, float, str, dict[str, Any], dict[str, float], float]] = []
        for c in remaining:
            if max_per_segment is not None and segment_counts[c["segment"]] >= max_per_segment:
                continue
            if duplicate_counts[c["duplicate_key"]] >= max_per_duplicate_key:
                continue

            marginal: dict[str, float] = {}
            marginal_raw = 0.0
            for qid, strength in c["learning_coverage"].items():
                q = questions.get(qid)
                if not q:
                    continue
                current = replication_counts[qid]
                desired = max(1, int(q["desired_replications"]))
                need_fraction = max(0.0, 1.0 - current / desired)
                value = q["weight"] * (strength / 5.0) * need_fraction
                if value > 0:
                    marginal[qid] = round(value, 4)
                    marginal_raw += value

            coverage_bonus = 20.0 * marginal_raw / total_weight
            objective = (
                c["score"]
                + STATUS_BONUS.get(c["status"], 0.0)
                + coverage_bonus
                - 2.5 * c["effort"]
                - 2.5 * c["risk"]
                - 4.0 * duplicate_counts[c["duplicate_key"]]
            )
            ranked.append((objective, c["score"], company.casefold() if (company := c["company"]) else "", c, marginal, coverage_bonus))

        if not ranked:
            break
        ranked.sort(key=lambda item: (-item[0], -item[1], item[2]))
        objective, _, _, chosen, marginal, coverage_bonus = ranked[0]
        selected.append({
            **chosen,
            "cohort_objective": round(objective, 3),
            "coverage_bonus": round(coverage_bonus, 3),
            "incremental_learning_value": marginal,
        })
        segment_counts[chosen["segment"]] += 1
        duplicate_counts[chosen["duplicate_key"]] += 1
        for qid, strength in chosen["learning_coverage"].items():
            if strength >= replication_threshold:
                replication_counts[qid] += 1
        remaining = [c for c in remaining if c is not chosen]

    coverage_summary: list[dict[str, Any]] = []
    must_cover_unmet: list[str] = []
    for qid, q in questions.items():
        achieved = replication_counts[qid]
        desired = int(q["desired_replications"])
        met = achieved >= desired
        if q["must_cover"] and achieved < 1:
            must_cover_unmet.append(qid)
        coverage_summary.append({
            "question": qid,
            "weight": q["weight"],
            "desired_replications": desired,
            "achieved_replications": achieved,
            "met": met,
            "must_cover": q["must_cover"],
        })

    not_selected = []
    for c in remaining:
        reasons = []
        if max_per_segment is not None and segment_counts[c["segment"]] >= max_per_segment:
            reasons.append("segment_cap")
        if duplicate_counts[c["duplicate_key"]] >= max_per_duplicate_key:
            reasons.append("duplicate_cap")
        if not reasons:
            reasons.append("lower_objective_under_capacity")
        not_selected.append({"company": c["company"], "status": c["status"], "score": c["score"], "reasons": reasons})

    met_count = sum(1 for row in coverage_summary if row["met"])
    coverage_ratio = round(met_count / len(coverage_summary), 4) if coverage_summary else 1.0

    return {
        "selection_stage": stage,
        "requested_size": size,
        "selected_count": len(selected),
        "selected": selected,
        "coverage_summary": coverage_summary,
        "coverage_ratio": coverage_ratio,
        "must_cover_unmet": must_cover_unmet,
        "cohort_complete": len(selected) == size and not must_cover_unmet,
        "segment_counts": dict(segment_counts),
        "duplicate_counts": dict(duplicate_counts),
        "excluded": excluded,
        "not_selected": not_selected,
        "interpretation": "Review uncovered must-answer hypotheses and capacity constraints; selection is a transparent heuristic, not proof of optimality.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", help="Input JSON file; omit to read stdin")
    parser.add_argument("--selection-stage", choices=("outreach_slate", "active_cohort"), help="Override payload selection_stage")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    try:
        if args.input:
            payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
        else:
            payload = json.load(sys.stdin)
        stage = args.selection_stage or str(payload.get("selection_stage") or "outreach_slate")
        result = select(payload, stage)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2 if args.pretty else None, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
