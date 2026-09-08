#!/usr/bin/env python3
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "score_maxx.py"
REGISTRY = json.loads((ROOT / "references" / "check-registry.json").read_text(encoding="utf-8"))
PILLARS = ["foundation", "relevance", "authority", "geo", "aeo"]
DEFAULT_SURFACES = list(REGISTRY["default_surfaces"])


def ev(text="Verified target artifact", cls="E2_SITE_DIRECT", source="https://example.com/"):
    return [{"class": cls, "artifact": text, "source": source}]


def complete_pass_rows(active, surfaces=None, overrides=None):
    surfaces = DEFAULT_SURFACES if surfaces is None else surfaces
    overrides = overrides or {}
    rows = []
    for c in REGISTRY["checks"]:
        if c["pillar"] not in active:
            continue
        if c["id"] in overrides:
            rows.append(overrides[c["id"]])
        elif c.get("na_policy") == "surface" and c.get("surface") not in surfaces:
            rows.append({"id": c["id"], "verdict": "N/A", "reason": "Surface out of scope"})
        else:
            rows.append({"id": c["id"], "verdict": "PASS", "evidence": ev(c["id"] + " target verified")})
    return rows


def payload(active, mode="PILLAR", surfaces=None, overrides=None, **extra):
    surfaces = DEFAULT_SURFACES if surfaces is None else surfaces
    data = {
        "registry_version": REGISTRY["version"],
        "mode": mode,
        "profile": "balanced",
        "active_pillars": active,
        "target_surfaces": surfaces,
        "checks": complete_pass_rows(active, surfaces, overrides),
        "gates": []
    }
    data.update(extra)
    return data


def run(data, as_of="2026-08-25"):
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(data, f)
        path = f.name
    proc = subprocess.run([sys.executable, str(SCRIPT), path, "--as-of", as_of], capture_output=True, text=True)
    Path(path).unlink(missing_ok=True)
    return proc


def test_full_perfect_is_maxx():
    p = run(payload(PILLARS, mode="FULL"))
    assert p.returncode == 0, p.stderr
    out = json.loads(p.stdout)
    assert out["maxx"] == 100.0
    assert out["focused_score"] is None
    assert out["tier"] == "Maxxed"
    assert out["score_name"] == "MAXX"


def test_partial_is_focused_readiness_not_maxx():
    p = run(payload(["geo"]))
    assert p.returncode == 0, p.stderr
    out = json.loads(p.stdout)
    assert out["maxx"] is None
    assert out["focused_score"] == 100.0
    assert out["tier"] is None
    assert out["score_name"] == "Focused readiness"


def test_not_assessed_reduces_coverage_not_score():
    overrides = {"AUT-05": {"id": "AUT-05", "verdict": "NOT_ASSESSED", "needed": "External reputation dataset"}}
    p = run(payload(["authority"], overrides=overrides))
    assert p.returncode == 0, p.stderr
    out = json.loads(p.stdout)
    assert out["pillars"]["authority"]["score"] == 100.0
    assert out["pillars"]["authority"]["coverage"] < 100.0


def test_never_na_is_rejected():
    overrides = {"FND-01": {"id": "FND-01", "verdict": "N/A", "reason": "No reason should make this N/A"}}
    p = run(payload(["foundation"], overrides=overrides))
    assert p.returncode != 0
    assert "cannot be N/A" in p.stderr


def test_conditional_na_requires_applicability_evidence():
    overrides = {"FND-09": {"id": "FND-09", "verdict": "N/A", "reason": "Single-language site"}}
    p = run(payload(["foundation"], overrides=overrides))
    assert p.returncode != 0
    assert "applicability" in p.stderr


def test_conditional_na_with_target_evidence_passes():
    overrides = {"FND-09": {
        "id": "FND-09", "verdict": "N/A", "reason": "Single-language site",
        "applicability_evidence": ev("Site navigation and sampled URLs expose only one language/market")
    }}
    p = run(payload(["foundation"], overrides=overrides))
    assert p.returncode == 0, p.stderr


def test_surface_na_allowed_only_out_of_scope():
    surfaces = ["google-ai-search"]
    p = run(payload(["geo"], surfaces=surfaces))
    assert p.returncode == 0, p.stderr
    bad = payload(["geo"], surfaces=["chatgpt-search"])
    for row in bad["checks"]:
        if row["id"] == "GEO-06":
            row.clear(); row.update({"id": "GEO-06", "verdict": "N/A", "reason": "Tried to skip target"})
    p2 = run(bad)
    assert p2.returncode != 0
    assert "cannot be N/A" in p2.stderr




def test_provisional_full_score_withholds_normal_tier():
    overrides = {
        cid: {"id": cid, "verdict": "NOT_ASSESSED", "needed": "More evidence"}
        for cid in ["AUT-05", "AUT-06", "AUT-07"]
    }
    p = run(payload(PILLARS, mode="FULL", overrides=overrides))
    assert p.returncode == 0, p.stderr
    out = json.loads(p.stdout)
    assert out["maxx"] == 100.0
    assert out["provisional"] is True
    assert out["tier"] is None
    assert out["indicative_tier"] == "Maxxed"


def test_registry_version_is_required():
    data = payload(["foundation"])
    data.pop("registry_version")
    p = run(data)
    assert p.returncode != 0
    assert "registry_version" in p.stderr


def test_unknown_archetype_and_override_group_rejected():
    data = payload(["foundation"], site_archetypes=["made-up-type"])
    p = run(data)
    assert p.returncode != 0
    assert "Unknown site archetypes" in p.stderr
    data2 = payload(["foundation"], freshness_overrides={"typo_group": {"verified_at":"2026-08-25","sources":["https://example.com/"]}})
    p2 = run(data2)
    assert p2.returncode != 0
    assert "Unknown freshness override groups" in p2.stderr


def test_scored_verdict_requires_target_specific_evidence():
    overrides = {"FND-01": {"id": "FND-01", "verdict": "PASS", "evidence": ev("Google says indexability matters", "E1_FIRST_PARTY_LIVE", "https://developers.google.com/")}}
    p = run(payload(["foundation"], overrides=overrides))
    assert p.returncode != 0
    assert "target-specific evidence" in p.stderr


def test_distribution_preserves_fractional_points():
    overrides = {"REL-01": {
        "id": "REL-01", "verdict": "WEAK", "distribution": {"pass": 7, "weak": 0, "fail": 1},
        "evidence": ev("Eight sampled landing pages: seven clear titles, one duplicate title")
    }}
    p = run(payload(["relevance"], overrides=overrides))
    assert p.returncode == 0, p.stderr
    out = json.loads(p.stdout)
    row = next(x for x in out["check_results"] if x["id"] == "REL-01")
    assert row["points"] == 0.875
    assert row["distribution"]["total"] == 8


def test_gate_caps_score_with_direct_evidence():
    overrides = {"FND-01": {"id": "FND-01", "verdict": "FAIL", "evidence": ev("Pricing URL has meta robots noindex", source="https://example.com/pricing")}}
    data = payload(PILLARS, mode="FULL", overrides=overrides)
    data["gates"] = [{"id": "CRITICAL_PAGES_NOINDEX", "evidence": ev("Pricing URL has meta robots noindex", source="https://example.com/pricing") }]
    p = run(data)
    assert p.returncode == 0, p.stderr
    out = json.loads(p.stdout)
    assert out["maxx"] == 45.0
    assert out["pillars"]["foundation"]["score"] == 45.0


def test_gate_rejects_generic_platform_docs_only():
    overrides = {"FND-01": {"id": "FND-01", "verdict": "FAIL", "evidence": ev("Pricing URL has meta robots noindex", source="https://example.com/pricing")}}
    data = payload(PILLARS, mode="FULL", overrides=overrides)
    data["gates"] = [{"id": "CRITICAL_PAGES_NOINDEX", "evidence": ev("Noindex docs", "E1_FIRST_PARTY_LIVE", "https://developers.google.com/") }]
    p = run(data)
    assert p.returncode != 0
    assert "requires direct/reproducible/connected" in p.stderr



def test_gate_rejects_contradictory_pass():
    data = payload(PILLARS, mode="FULL")
    data["gates"] = [{"id": "CRITICAL_PAGES_NOINDEX", "evidence": ev("Pricing URL has meta robots noindex", source="https://example.com/pricing")}]
    p = run(data)
    assert p.returncode != 0
    assert "conflicts with FND-01 verdict PASS" in p.stderr


def test_freshness_override_rejects_nonofficial_host():
    surfaces = ["chatgpt-search"]
    data = payload(["geo"], surfaces=surfaces)
    data["freshness_overrides"] = {
        "openai_search": {"verified_at": "2026-10-01", "sources": ["https://example.com/openai-search-policy"]}
    }
    p = run(data, as_of="2026-10-01")
    assert p.returncode != 0
    assert "official registry host" in p.stderr


def test_stale_platform_group_requires_refresh_override():
    surfaces = ["chatgpt-search"]
    p = run(payload(["geo"], surfaces=surfaces), as_of="2026-10-01")
    assert p.returncode != 0
    assert "openai_search is stale" in p.stderr


def test_freshness_override_allows_scoring():
    surfaces = ["chatgpt-search"]
    data = payload(["geo"], surfaces=surfaces)
    data["freshness_overrides"] = {
        "openai_search": {"verified_at": "2026-10-01", "sources": ["https://help.openai.com/en/articles/12627856-publishers-and-developers-faq"]}
    }
    p = run(data, as_of="2026-10-01")
    assert p.returncode == 0, p.stderr




def test_historical_asof_rejects_future_bundled_policy():
    surfaces = ["chatgpt-search"]
    p = run(payload(["geo"], surfaces=surfaces), as_of="2026-08-01")
    assert p.returncode != 0
    assert "after audit as_of" in p.stderr


def test_historical_asof_accepts_historical_override():
    surfaces = ["chatgpt-search"]
    data = payload(["geo"], surfaces=surfaces)
    data["freshness_overrides"] = {
        "openai_search": {"verified_at": "2026-08-01", "sources": ["https://help.openai.com/en/articles/12627856-publishers-and-developers-faq"]}
    }
    p = run(data, as_of="2026-08-01")
    assert p.returncode == 0, p.stderr


def test_audit_fingerprint_is_stable_and_input_sensitive():
    data = payload(["authority"])
    p1 = run(data); p2 = run(data)
    assert p1.returncode == 0 and p2.returncode == 0
    f1 = json.loads(p1.stdout)["audit_fingerprint"]
    f2 = json.loads(p2.stdout)["audit_fingerprint"]
    assert f1 == f2 and len(f1) == 64
    data["subject"] = "https://example.com/changed"
    p3 = run(data)
    assert json.loads(p3.stdout)["audit_fingerprint"] != f1


def test_low_coverage_withholds_composite_score():
    data = payload(["relevance"])
    for row in data["checks"]:
        cid = row["id"]
        if cid != "REL-02":
            row.clear(); row.update({"id": cid, "verdict": "NOT_ASSESSED", "needed": "More target evidence"})
    p = run(data)
    assert p.returncode == 0, p.stderr
    out = json.loads(p.stdout)
    assert out["pillars"]["relevance"]["score"] == 100.0
    assert out["focused_score"] is None
    assert out["unpublishable_pillars"] == ["relevance"]
    assert "minimum publishable threshold" in out["score_withheld_reason"]


def test_missing_check_rejected():
    data = payload(["geo"])
    data["checks"] = [r for r in data["checks"] if r["id"] != "GEO-10"]
    p = run(data)
    assert p.returncode != 0
    assert "Missing check ids" in p.stderr


def test_duplicate_active_pillars_rejected():
    data = payload(["geo"])
    data["active_pillars"] = ["geo", "geo"]
    p = run(data)
    assert p.returncode != 0
    assert "duplicates" in p.stderr


def test_custom_weights_reject_inactive_extra_key():
    data = payload(["geo"])
    data["custom_weights"] = {"geo": 1, "foundation": 1}
    p = run(data)
    assert p.returncode != 0
    assert "inactive/unknown" in p.stderr


def test_full_requires_all_five_pillars():
    data = payload(["geo"], mode="PILLAR")
    data["mode"] = "FULL"
    p = run(data)
    assert p.returncode != 0
    assert "FULL mode requires all five pillars" in p.stderr



def test_google_schema_support_self_expires_when_google_surface_is_targeted():
    data = payload(["aeo"], surfaces=["google-ai-search"])
    p = run(data, as_of="2026-10-01")
    assert p.returncode != 0
    assert "google_structured_data is stale" in p.stderr


def test_google_schema_freshness_not_forced_when_google_surface_out_of_scope():
    data = payload(["aeo"], surfaces=["chatgpt-search"])
    p = run(data, as_of="2026-10-01")
    assert p.returncode == 0, p.stderr


def test_gptbot_block_does_not_fail_chatgpt_search():
    surfaces = ["chatgpt-search"]
    overrides = {"GEO-06": {
        "id": "GEO-06", "verdict": "PASS",
        "evidence": ev("OAI-SearchBot allowed and fetchable; GPTBot explicitly blocked by separate training policy", source="https://example.com/robots.txt")
    }}
    p = run(payload(["geo"], surfaces=surfaces, overrides=overrides))
    assert p.returncode == 0, p.stderr
    out = json.loads(p.stdout)
    row = next(x for x in out["check_results"] if x["id"] == "GEO-06")
    assert row["verdict"] == "PASS"
    assert out["gates_applied"] == []


if __name__ == "__main__":
    tests = [name for name, obj in sorted(globals().items()) if name.startswith("test_") and callable(obj)]
    for name in tests:
        globals()[name]()
        print("PASS", name)
