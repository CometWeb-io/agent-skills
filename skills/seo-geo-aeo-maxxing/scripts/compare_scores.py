#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def num_delta(a, b):
    if a is None or b is None:
        return None
    return round(float(b) - float(a), 1)


def checks_by_id(score):
    return {row["id"]: row for row in score.get("check_results", [])}


def gate_ids(score):
    return {row["id"] for row in score.get("gates_applied", [])}


def compare(base, current, kind="delta"):
    reasons = []
    for key in ["scoring_engine_version", "registry_version", "profile", "weights", "active_pillars", "target_surfaces"]:
        if key not in base or key not in current:
            reasons.append(f"{key} missing")
        elif base.get(key) != current.get(key):
            reasons.append(f"{key} differs")
    comparable = not reasons

    pnames = []
    for p in base.get("active_pillars", []):
        if p in current.get("active_pillars", []) and p not in pnames:
            pnames.append(p)

    pillars = {}
    for p in pnames:
        a = base.get("pillars", {}).get(p, {})
        b = current.get("pillars", {}).get(p, {})
        pillars[p] = {
            "baseline_score": a.get("score"),
            "current_score": b.get("score"),
            "score_delta": num_delta(a.get("score"), b.get("score")),
            "baseline_coverage": a.get("coverage"),
            "current_coverage": b.get("coverage"),
            "coverage_delta_pp": num_delta(a.get("coverage"), b.get("coverage")),
            "baseline_evidence_grade": a.get("evidence_grade"),
            "current_evidence_grade": b.get("evidence_grade")
        }

    ca = checks_by_id(base)
    cb = checks_by_id(current)
    changes = []
    for cid in sorted(set(ca) & set(cb)):
        if ca[cid].get("verdict") != cb[cid].get("verdict"):
            changes.append({
                "id": cid,
                "from": ca[cid].get("verdict"),
                "to": cb[cid].get("verdict"),
                "points_delta": num_delta(ca[cid].get("points"), cb[cid].get("points"))
            })

    ga = gate_ids(base)
    gb = gate_ids(current)
    warnings = []
    for p, row in pillars.items():
        a_cov = row.get("baseline_coverage")
        b_cov = row.get("current_coverage")
        if a_cov is not None and b_cov is not None and abs(float(a_cov) - float(b_cov)) > 15:
            warnings.append(f"{p} evidence coverage differs by more than 15 percentage points.")

    cov_a = base.get("overall_coverage")
    cov_b = current.get("overall_coverage")
    if cov_a is not None and cov_b is not None and abs(float(cov_a) - float(cov_b)) > 15:
        warnings.append("Overall evidence coverage differs by more than 15 percentage points; treat score differences cautiously.")
    if kind == "versus" and base.get("as_of") != current.get("as_of"):
        warnings.append("VERSUS scores use different as_of dates; align dates when possible before declaring a winner.")
    if kind == "versus" and base.get("site_archetypes") != current.get("site_archetypes"):
        warnings.append("Site archetypes differ; interpret N/A/applicability differences before declaring a winner.")
    if kind == "versus" and not comparable:
        warnings.append("VERSUS comparison is asymmetric; align engine, registry, profile, pillars, and target surfaces before declaring a winner.")

    def fresh_map(score):
        return {x.get("group"): {"state": x.get("state"), "verified_at": x.get("verified_at")} for x in score.get("freshness_used", [])}
    fa, fb = fresh_map(base), fresh_map(current)
    freshness_changes = []
    for group in sorted(set(fa) | set(fb)):
        if fa.get(group) != fb.get(group):
            freshness_changes.append({"group": group, "baseline": fa.get(group), "current": fb.get(group)})

    maxx_context = base.get("score_name") == "MAXX" or current.get("score_name") == "MAXX"
    top_label = "MAXX" if maxx_context else "Focused readiness"
    top_a = base.get("maxx") if maxx_context else base.get("focused_score")
    top_b = current.get("maxx") if maxx_context else current.get("focused_score")

    return {
        "kind": kind.upper(),
        "baseline_fingerprint": base.get("audit_fingerprint"),
        "current_fingerprint": current.get("audit_fingerprint"),
        "baseline_as_of": base.get("as_of"),
        "current_as_of": current.get("as_of"),
        "comparable": comparable,
        "comparability_reasons": reasons,
        "score_name": top_label,
        "baseline_score": top_a,
        "current_score": top_b,
        "score_delta": num_delta(top_a, top_b),
        "baseline_coverage": cov_a,
        "current_coverage": cov_b,
        "pillars": pillars,
        "check_verdict_changes": changes,
        "gates_added": sorted(gb - ga),
        "gates_removed": sorted(ga - gb),
        "freshness_changes": freshness_changes,
        "warnings": warnings
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Compare two deterministic MAXX score outputs.")
    parser.add_argument("baseline")
    parser.add_argument("current")
    parser.add_argument("--kind", choices=["delta", "versus"], default="delta")
    args = parser.parse_args(argv)
    result = compare(load_json(args.baseline), load_json(args.current), args.kind)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, json.JSONDecodeError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
