#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import sys
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse

VERDICT_POINTS = {"PASS": 1.0, "WEAK": 0.5, "FAIL": 0.0}
EXCLUDED = {"N/A", "NOT_ASSESSED"}
VALID_VERDICTS = set(VERDICT_POINTS) | EXCLUDED
PILLARS = ["foundation", "relevance", "authority", "geo", "aeo"]
MODES = {"RECON", "FULL", "PILLAR", "VERSUS", "DELTA"}
ENGINE_VERSION = "3.0.0"


def fail(msg):
    raise ValueError(msg)


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def parse_day(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        fail(f"Invalid date {value!r}; expected YYYY-MM-DD")


def get_as_of(cli_value=None):
    raw = cli_value or os.environ.get("MAXX_AS_OF_DATE")
    return parse_day(raw) if raw else date.today()


def tier_for(score, tiers):
    if score is None:
        return None
    for tier in tiers:
        if tier["min"] <= score <= tier["max"]:
            return tier["label"]
    return None


def evidence_grade(value):
    if value is None:
        return None
    if value >= 90:
        return "A"
    if value >= 75:
        return "B"
    if value >= 60:
        return "C"
    return "D"


def validate_evidence(items, evidence_classes, cid):
    if not isinstance(items, list) or not items:
        fail(f"{cid} scored verdict requires a non-empty evidence list")
    qualities = []
    normalized = []
    for idx, item in enumerate(items, 1):
        if not isinstance(item, dict):
            fail(f"{cid} evidence item {idx} must be an object")
        cls = item.get("class")
        artifact = str(item.get("artifact", "")).strip()
        if cls not in evidence_classes:
            fail(f"{cid} evidence item {idx} has unknown class: {cls}")
        if not artifact:
            fail(f"{cid} evidence item {idx} requires artifact")
        source = str(item.get("source", "")).strip()
        normalized.append({"class": cls, "artifact": artifact, **({"source": source} if source else {})})
        qualities.append(float(evidence_classes[cls]))
    # Conservative: the verdict is only as strong as the weakest material evidence item supplied.
    return normalized, min(qualities)


def validate_distribution(row, cid):
    dist = row.get("distribution")
    if dist is None:
        return None
    if not isinstance(dist, dict):
        fail(f"{cid} distribution must be an object")
    keys = {"pass", "weak", "fail"}
    if set(dist) != keys:
        fail(f"{cid} distribution must contain exactly: pass, weak, fail")
    vals = {}
    for key in keys:
        value = dist[key]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            fail(f"{cid} distribution.{key} must be a non-negative integer")
        vals[key] = value
    total = sum(vals.values())
    if total <= 0:
        fail(f"{cid} distribution total must be greater than zero")
    derived = (vals["pass"] + 0.5 * vals["weak"]) / total
    verdict = row.get("verdict")
    if derived == 1.0 and verdict != "PASS":
        fail(f"{cid} all-pass distribution requires verdict PASS")
    if derived == 0.0 and verdict != "FAIL":
        fail(f"{cid} all-fail distribution requires verdict FAIL")
    if 0.0 < derived < 1.0 and verdict != "WEAK":
        fail(f"{cid} mixed distribution requires verdict WEAK")
    return {**vals, "total": total, "points": round(derived, 6)}


def validate_weights(weights, active, custom=False):
    if not isinstance(weights, dict):
        fail("Pillar weights must be an object")
    missing = [p for p in active if p not in weights]
    if missing:
        fail("Missing pillar weights: " + ", ".join(missing))
    if custom:
        extra = sorted(set(weights) - set(active))
        if extra:
            fail("Custom weights contain inactive/unknown pillars: " + ", ".join(extra))
    vals = {p: float(weights[p]) for p in active}
    if any(v < 0 for v in vals.values()) or sum(vals.values()) <= 0:
        fail("Pillar weights must be non-negative and sum to more than zero")
    return vals


def source_group_map(source_registry):
    return {row["id"]: row for row in source_registry.get("groups", [])}


def validate_freshness(group_id, source_registry, overrides, as_of):
    groups = source_group_map(source_registry)
    if group_id not in groups:
        fail(f"Unknown platform source group: {group_id}")
    group = groups[group_id]
    ttl = int(group.get("ttl_days", source_registry.get("default_ttl_days", 30)))
    verified = parse_day(group.get("last_verified"))
    age = (as_of - verified).days
    future_bundled = verified > as_of
    if not future_bundled and age <= ttl:
        return {"group": group_id, "state": "bundled_fresh", "verified_at": str(verified), "age_days": age}

    override = (overrides or {}).get(group_id)
    if not isinstance(override, dict):
        if future_bundled:
            fail(
                f"Platform fact group {group_id} was bundled from {verified}, after audit as_of {as_of}; "
                f"provide freshness_overrides.{group_id} verified on or before the audit date to avoid temporal leakage"
            )
        fail(
            f"Platform fact group {group_id} is stale ({age} days > TTL {ttl}); "
            f"refresh the official source and add freshness_overrides.{group_id}"
        )
    odate = parse_day(override.get("verified_at"))
    oage = (as_of - odate).days
    if oage < 0:
        fail(f"freshness_overrides.{group_id}.verified_at cannot be in the future")
    if oage > ttl:
        fail(f"freshness_overrides.{group_id} is still stale ({oage} days > TTL {ttl})")
    sources = override.get("sources")
    if sources is None and override.get("source"):
        sources = [override.get("source")]
    if not isinstance(sources, list) or not sources or not all(str(s).startswith("https://") for s in sources):
        fail(f"freshness_overrides.{group_id} requires at least one https official source")
    allowed_hosts = {urlparse(str(u)).hostname for u in group.get("official_sources", []) if urlparse(str(u)).hostname}
    supplied_hosts = {urlparse(str(u)).hostname for u in sources if urlparse(str(u)).hostname}
    if allowed_hosts and not any(h in allowed_hosts for h in supplied_hosts):
        fail(
            f"freshness_overrides.{group_id} must include a source on an official registry host: "
            + ", ".join(sorted(allowed_hosts))
        )
    return {"group": group_id, "state": "live_override", "verified_at": str(odate), "age_days": oage, "sources": sources}


def score_audit(audit, root, as_of=None):
    as_of = as_of or get_as_of()
    registry = load_json(root / "references" / "check-registry.json")
    source_registry = load_json(root / "references" / "live-source-registry.json")
    evidence_classes = registry.get("evidence_classes", {})

    if audit.get("registry_version") != registry["version"]:
        fail(
            f"Audit registry_version {audit.get('registry_version')!r} does not match current registry {registry['version']}; "
            "use the audit template and do not silently rescore across registry versions"
        )

    if audit.get("subject") is not None and not isinstance(audit.get("subject"), str):
        fail("subject must be a string when provided")
    if audit.get("scope") is not None and not isinstance(audit.get("scope"), dict):
        fail("scope must be an object when provided")
    archetypes = audit.get("site_archetypes", [])
    if not isinstance(archetypes, list) or any(not isinstance(x, str) for x in archetypes):
        fail("site_archetypes must be a list of strings")
    if len(archetypes) != len(set(archetypes)):
        fail("site_archetypes contains duplicates")
    unknown_archetypes = sorted(set(archetypes) - set(registry.get("site_archetypes", [])))
    if unknown_archetypes:
        fail("Unknown site archetypes: " + ", ".join(unknown_archetypes))

    source_group_ids = set(source_group_map(source_registry))
    overrides = audit.get("freshness_overrides", {})
    if overrides is not None and not isinstance(overrides, dict):
        fail("freshness_overrides must be an object")
    unknown_override_groups = sorted(set((overrides or {}).keys()) - source_group_ids)
    if unknown_override_groups:
        fail("Unknown freshness override groups: " + ", ".join(unknown_override_groups))

    mode = str(audit.get("mode", "FULL")).upper()
    if mode not in MODES:
        fail("Unknown mode: " + mode)

    active = audit.get("active_pillars")
    if active is None:
        active = list(PILLARS) if mode == "FULL" else list(PILLARS)
    if not isinstance(active, list) or not active:
        fail("active_pillars must be a non-empty list")
    if len(active) != len(set(active)):
        fail("active_pillars contains duplicates")
    unknown_pillars = [p for p in active if p not in PILLARS]
    if unknown_pillars:
        fail("Unknown active pillars: " + ", ".join(unknown_pillars))
    if mode == "FULL" and set(active) != set(PILLARS):
        fail("FULL mode requires all five pillars")

    target_surfaces = audit.get("target_surfaces", registry.get("default_surfaces", []))
    if not isinstance(target_surfaces, list):
        fail("target_surfaces must be a list")
    if len(target_surfaces) != len(set(target_surfaces)):
        fail("target_surfaces contains duplicates")
    unknown_surfaces = sorted(set(target_surfaces) - set(registry.get("surfaces", [])))
    if unknown_surfaces:
        fail("Unknown target surfaces: " + ", ".join(unknown_surfaces))

    check_defs = {c["id"]: c for c in registry["checks"]}
    seen = set()
    rows = []
    freshness_used = {}

    checks = audit.get("checks", [])
    if not isinstance(checks, list):
        fail("checks must be a list")

    for row in checks:
        if not isinstance(row, dict):
            fail("Each check must be an object")
        cid = row.get("id")
        verdict = row.get("verdict")
        if cid not in check_defs:
            fail(f"Unknown check id: {cid}")
        if cid in seen:
            fail(f"Duplicate check id: {cid}")
        seen.add(cid)
        cdef = check_defs[cid]
        if verdict not in VALID_VERDICTS:
            fail(f"Invalid verdict for {cid}: {verdict}")

        na_policy = cdef.get("na_policy", "conditional")
        if verdict == "N/A":
            reason = str(row.get("reason", "")).strip()
            if not reason:
                fail(f"{cid} N/A requires non-empty reason")
            if na_policy == "never":
                fail(f"{cid} cannot be N/A; use PASS/WEAK/FAIL or NOT_ASSESSED")
            if na_policy == "surface" and cdef.get("surface") in target_surfaces:
                fail(f"{cid} targets {cdef.get('surface')} and cannot be N/A while that surface is in scope")
            normalized_evidence = []
            evidence_quality = None
            points = None
            distribution = None
            if na_policy == "conditional":
                app_evidence, _ = validate_evidence(row.get("applicability_evidence"), evidence_classes, f"{cid} applicability")
                required_target = set(cdef.get("required_target_evidence_classes", []))
                if required_target and not any(item["class"] in required_target for item in app_evidence):
                    fail(f"{cid} N/A requires target-specific applicability evidence")
            else:
                app_evidence = []
        elif verdict == "NOT_ASSESSED":
            needed = str(row.get("needed", "")).strip()
            if not needed:
                fail(f"{cid} NOT_ASSESSED requires non-empty needed")
            normalized_evidence = []
            evidence_quality = None
            points = None
            distribution = None
        else:
            normalized_evidence, evidence_quality = validate_evidence(row.get("evidence"), evidence_classes, cid)
            required_target = set(cdef.get("required_target_evidence_classes", []))
            if required_target and not any(item["class"] in required_target for item in normalized_evidence):
                fail(f"{cid} scored verdict requires target-specific evidence from: {', '.join(sorted(required_target))}")
            distribution = validate_distribution(row, cid)
            points = distribution["points"] if distribution else VERDICT_POINTS[verdict]
            if cdef.get("requires_fresh_policy"):
                triggers = cdef.get("freshness_trigger_surfaces")
                should_check_freshness = not triggers or bool(set(triggers) & set(target_surfaces))
                if should_check_freshness:
                    state = validate_freshness(
                        cdef["platform_source_group"], source_registry,
                        audit.get("freshness_overrides", {}), as_of
                    )
                    freshness_used[cdef["platform_source_group"]] = state

        merged = dict(cdef)
        merged.update(row)
        merged["evidence"] = normalized_evidence
        merged["evidence_quality"] = evidence_quality
        merged["points"] = points
        if verdict == "N/A" and na_policy == "conditional":
            merged["applicability_evidence"] = app_evidence
        if distribution:
            merged["distribution"] = distribution
        rows.append(merged)

    required_ids = {c["id"] for c in registry["checks"] if c["pillar"] in active}
    missing_ids = sorted(required_ids - seen)
    extra_inactive = sorted(cid for cid in seen if check_defs[cid]["pillar"] not in active)
    if missing_ids:
        fail("Missing check ids for active pillars: " + ", ".join(missing_ids))
    if extra_inactive:
        fail("Checks supplied for inactive pillars: " + ", ".join(extra_inactive))

    if "custom_weights" in audit:
        weights = validate_weights(audit["custom_weights"], active, custom=True)
        profile = "custom"
    else:
        profile = audit.get("profile", "balanced")
        if profile not in registry["profiles"]:
            fail(f"Unknown profile: {profile}")
        weights = validate_weights(registry["profiles"][profile], active)

    coverage_rules = registry.get("coverage_rules", {})
    withhold_below = float(coverage_rules.get("withhold_below", 50.0))
    provisional_below = float(coverage_rules.get("provisional_below", 75.0))

    pillar_results = {}
    total_assessed_weight = 0.0
    total_applicable_weight = 0.0
    eq_num = 0.0
    eq_den = 0.0

    for pillar in active:
        relevant = [r for r in rows if r["pillar"] == pillar]
        assessed = [r for r in relevant if r["verdict"] in VERDICT_POINTS]
        not_assessed = [r for r in relevant if r["verdict"] == "NOT_ASSESSED"]
        applicable_weight = sum(float(r["weight"]) for r in assessed + not_assessed)
        assessed_weight = sum(float(r["weight"]) for r in assessed)
        score = None
        if assessed_weight > 0:
            earned = sum(float(r["weight"]) * float(r["points"]) for r in assessed)
            score = round(100.0 * earned / assessed_weight, 1)
        coverage = None if applicable_weight <= 0 else round(100.0 * assessed_weight / applicable_weight, 1)
        p_eq_den = sum(float(r["weight"]) for r in assessed if r["evidence_quality"] is not None)
        p_eq = None
        if p_eq_den > 0:
            p_eq = round(100.0 * sum(float(r["weight"]) * float(r["evidence_quality"]) for r in assessed) / p_eq_den, 1)
        pillar_results[pillar] = {
            "score": score,
            "coverage": coverage,
            "evidence_quality": p_eq,
            "evidence_grade": evidence_grade(p_eq),
            "provisional": coverage is not None and coverage < provisional_below,
            "publishable": coverage is not None and coverage >= withhold_below and score is not None,
            "assessed_checks": len(assessed),
            "not_assessed_checks": len(not_assessed),
            "na_checks": len([r for r in relevant if r["verdict"] == "N/A"])
        }
        total_assessed_weight += assessed_weight
        total_applicable_weight += applicable_weight
        for r in assessed:
            if r["evidence_quality"] is not None:
                eq_num += float(r["weight"]) * float(r["evidence_quality"])
                eq_den += float(r["weight"])

    gates_applied = []
    maxx_cap = None
    gate_seen = set()
    gates = audit.get("gates", [])
    if not isinstance(gates, list):
        fail("gates must be a list")
    for gate in gates:
        if not isinstance(gate, dict):
            fail("Each gate must be an object with id and evidence")
        gid = gate.get("id")
        if gid not in registry["gates"]:
            fail(f"Unknown gate: {gid}")
        if gid in gate_seen:
            fail(f"Duplicate gate: {gid}")
        gate_seen.add(gid)
        evidence, _ = validate_evidence(gate.get("evidence"), evidence_classes, f"gate {gid}")
        allowed = set(registry["gates"][gid].get("allowed_evidence_classes", []))
        if allowed and not any(item["class"] in allowed for item in evidence):
            fail(f"Gate {gid} requires direct/reproducible/connected site evidence")
        gdef = registry["gates"][gid]
        row_state = {r["id"]: r["verdict"] for r in rows}
        for required_id in gdef.get("requires_nonpass_check_ids", []):
            if required_id in row_state and row_state[required_id] not in {"WEAK", "FAIL"}:
                fail(
                    f"Gate {gid} conflicts with {required_id} verdict {row_state[required_id]}; "
                    "a gate must agree with its related scored finding"
                )
        gates_applied.append({"id": gid, "evidence": evidence})
        if "foundation_cap" in gdef and "foundation" in pillar_results and pillar_results["foundation"]["score"] is not None:
            pillar_results["foundation"]["score"] = min(pillar_results["foundation"]["score"], float(gdef["foundation_cap"]))
        if "maxx_cap" in gdef:
            cap = float(gdef["maxx_cap"])
            maxx_cap = cap if maxx_cap is None else min(maxx_cap, cap)

    missing_active = [p for p in active if pillar_results[p]["score"] is None]
    unpublishable_pillars = [p for p in active if pillar_results[p]["score"] is not None and not pillar_results[p]["publishable"]]
    composite = None
    if not missing_active and not unpublishable_pillars:
        denom = sum(weights[p] for p in active)
        composite = round(sum(pillar_results[p]["score"] * weights[p] for p in active) / denom, 1)
        if maxx_cap is not None:
            composite = min(composite, maxx_cap)

    is_full_matrix = set(active) == set(PILLARS)
    maxx = composite if is_full_matrix else None
    focused_score = None if is_full_matrix else composite
    overall_coverage = None if total_applicable_weight <= 0 else round(100.0 * total_assessed_weight / total_applicable_weight, 1)
    overall_evidence_quality = None if eq_den <= 0 else round(100.0 * eq_num / eq_den, 1)
    provisional = bool(missing_active or unpublishable_pillars) or any(v["provisional"] for v in pillar_results.values())
    raw_tier = tier_for(maxx, registry["tiers"])
    tier = None if provisional else raw_tier
    indicative_tier = raw_tier if provisional and maxx is not None else None
    score_withheld_reason = None
    if missing_active:
        score_withheld_reason = "One or more active pillars have no assessable checks."
    elif unpublishable_pillars:
        score_withheld_reason = (
            "Evidence coverage is below the minimum publishable threshold "
            f"({withhold_below:.0f}%) for: " + ", ".join(unpublishable_pillars)
        )

    check_results = []
    for r in rows:
        item = {
            "id": r["id"],
            "pillar": r["pillar"],
            "verdict": r["verdict"],
            "points": r.get("points"),
            "weight": r["weight"],
            "evidence_quality": None if r.get("evidence_quality") is None else round(100 * r["evidence_quality"], 1)
        }
        if r.get("distribution"):
            item["distribution"] = r["distribution"]
        if r.get("applicability_evidence"):
            item["applicability_evidence"] = r["applicability_evidence"]
        check_results.append(item)

    audit_fingerprint = hashlib.sha256(
        json.dumps(audit, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()

    return {
        "scoring_engine_version": ENGINE_VERSION,
        "audit_fingerprint": audit_fingerprint,
        "registry_version": registry["version"],
        "subject": audit.get("subject"),
        "site_archetypes": audit.get("site_archetypes", []),
        "scope": audit.get("scope", {}),
        "as_of": str(as_of),
        "mode": mode,
        "profile": profile,
        "active_pillars": active,
        "target_surfaces": target_surfaces,
        "weights": weights,
        "maxx": maxx,
        "focused_score": focused_score,
        "score_name": "MAXX" if is_full_matrix else "Focused readiness",
        "tier": tier,
        "indicative_tier": indicative_tier,
        "maxx_cap": maxx_cap,
        "provisional": provisional,
        "overall_coverage": overall_coverage,
        "overall_evidence_quality": overall_evidence_quality,
        "overall_evidence_grade": evidence_grade(overall_evidence_quality),
        "missing_active_pillars": missing_active,
        "unpublishable_pillars": unpublishable_pillars,
        "coverage_rules": {"withhold_below": withhold_below, "provisional_below": provisional_below},
        "score_withheld_reason": score_withheld_reason,
        "pillars": pillar_results,
        "gates_applied": gates_applied,
        "freshness_used": list(freshness_used.values()),
        "check_results": check_results
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Score an SEO/GEO/AEO MAXX audit JSON deterministically.")
    parser.add_argument("audit", help="Path to audit JSON")
    parser.add_argument("--as-of", dest="as_of", help="Override current date for testing, YYYY-MM-DD")
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    audit = load_json(Path(args.audit).resolve())
    result = score_audit(audit, root, get_as_of(args.as_of))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, json.JSONDecodeError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
