#!/usr/bin/env python3
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "scripts" / "build_audit_template.py"
SCORE = ROOT / "scripts" / "score_maxx.py"
FRESH = ROOT / "scripts" / "check_freshness.py"
COMPARE = ROOT / "scripts" / "compare_scores.py"


def call(args):
    return subprocess.run(args, capture_output=True, text=True)


def test_template_full_is_complete_and_scoreable():
    p = call([sys.executable, str(BUILD), "--mode", "FULL"])
    assert p.returncode == 0, p.stderr
    audit = json.loads(p.stdout)
    assert len(audit["checks"]) == 41
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(audit, f); path = f.name
    scored = call([sys.executable, str(SCORE), path, "--as-of", "2026-08-25"])
    Path(path).unlink(missing_ok=True)
    assert scored.returncode == 0, scored.stderr
    out = json.loads(scored.stdout)
    assert out["maxx"] is None
    assert set(out["missing_active_pillars"]) == {"foundation", "relevance", "authority", "geo", "aeo"}


def test_template_surface_scope_marks_other_platform_checks_na():
    p = call([sys.executable, str(BUILD), "--mode", "PILLAR", "--pillars", "geo", "--surfaces", "google-ai-search"])
    assert p.returncode == 0, p.stderr
    audit = json.loads(p.stdout)
    rows = {r["id"]: r for r in audit["checks"]}
    assert rows["GEO-09"]["verdict"] == "NOT_ASSESSED"
    for cid in ["GEO-06", "GEO-07", "GEO-08", "GEO-10"]:
        assert rows[cid]["verdict"] == "N/A"


def test_pillar_template_requires_pillars():
    p = call([sys.executable, str(BUILD), "--mode", "PILLAR"])
    assert p.returncode != 0


def test_freshness_strict_current_stale_and_future():
    fresh = call([sys.executable, str(FRESH), "--as-of", "2026-08-25", "--strict"])
    assert fresh.returncode == 0, fresh.stderr
    stale = call([sys.executable, str(FRESH), "--as-of", "2026-10-01", "--groups", "openai_search", "--strict"])
    assert stale.returncode == 1
    out = json.loads(stale.stdout)
    assert out["has_stale"] is True and out["has_issue"] is True
    future = call([sys.executable, str(FRESH), "--as-of", "2026-08-01", "--groups", "openai_search", "--strict"])
    assert future.returncode == 1
    fout = json.loads(future.stdout)
    assert fout["groups"][0]["state"] == "future" and fout["has_issue"] is True


def make_score(score, coverage=100.0, profile="balanced", verdict="PASS"):
    return {
        "scoring_engine_version": "3.0.0",
        "registry_version": "3.0.0",
        "profile": profile,
        "weights": {"geo": 20.0 if profile == "balanced" else 30.0},
        "score_name": "Focused readiness",
        "active_pillars": ["geo"],
        "target_surfaces": ["chatgpt-search"],
        "maxx": None,
        "focused_score": score,
        "overall_coverage": coverage,
        "pillars": {"geo": {"score": score, "coverage": coverage, "evidence_grade": "A"}},
        "check_results": [{"id": "GEO-06", "verdict": verdict, "points": 1.0 if verdict == "PASS" else 0.5}],
        "gates_applied": []
    }


def run_compare(a, b, kind="delta"):
    paths = []
    for data in [a, b]:
        f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        json.dump(data, f); f.close(); paths.append(f.name)
    p = call([sys.executable, str(COMPARE), paths[0], paths[1], "--kind", kind])
    for path in paths: Path(path).unlink(missing_ok=True)
    return p



def test_compare_detects_custom_weight_mismatch():
    a = make_score(80)
    b = make_score(80)
    b["weights"] = {"geo": 99.0}
    p = run_compare(a, b)
    assert p.returncode == 0, p.stderr
    out = json.loads(p.stdout)
    assert out["comparable"] is False
    assert "weights differs" in out["comparability_reasons"]


def test_compare_keeps_maxx_context_when_one_score_withheld():
    a = make_score(80)
    b = make_score(80)
    for x in [a, b]:
        x["active_pillars"] = ["foundation", "relevance", "authority", "geo", "aeo"]
        x["weights"] = {"foundation":25.0,"relevance":25.0,"authority":20.0,"geo":20.0,"aeo":10.0}
        x["score_name"] = "MAXX"
        x["focused_score"] = None
    a["maxx"] = None
    b["maxx"] = 80.0
    p = run_compare(a, b)
    assert p.returncode == 0, p.stderr
    out = json.loads(p.stdout)
    assert out["score_name"] == "MAXX"
    assert out["baseline_score"] is None
    assert out["current_score"] == 80.0


def test_compare_delta_reports_change():
    p = run_compare(make_score(60, verdict="WEAK"), make_score(80, verdict="PASS"))
    assert p.returncode == 0, p.stderr
    out = json.loads(p.stdout)
    assert out["comparable"] is True
    assert out["score_delta"] == 20.0
    assert out["check_verdict_changes"][0]["id"] == "GEO-06"


def test_compare_versus_warns_on_asymmetric_evidence_and_profile():
    p = run_compare(make_score(80, 100, "balanced"), make_score(90, 60, "ai-first"), "versus")
    assert p.returncode == 0, p.stderr
    out = json.loads(p.stdout)
    assert out["comparable"] is False
    assert any("profile differs" in x for x in out["comparability_reasons"])
    assert len(out["warnings"]) >= 2


if __name__ == "__main__":
    tests = [name for name, obj in sorted(globals().items()) if name.startswith("test_") and callable(obj)]
    for name in tests:
        globals()[name]()
        print("PASS", name)
