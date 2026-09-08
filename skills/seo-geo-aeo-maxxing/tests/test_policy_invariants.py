#!/usr/bin/env python3
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = (ROOT / "SKILL.md").read_text(encoding="utf-8")
REGISTRY = json.loads((ROOT / "references" / "check-registry.json").read_text(encoding="utf-8"))
LIVE_JSON = json.loads((ROOT / "references" / "live-source-registry.json").read_text(encoding="utf-8"))
LIVE_MD = (ROOT / "references" / "live-source-registry.md").read_text(encoding="utf-8")
GEO = (ROOT / "references" / "pillar-geo.md").read_text(encoding="utf-8")
DATA = (ROOT / "references" / "data-collection.md").read_text(encoding="utf-8")


def test_registry_ids_unique_and_complete():
    ids = [c["id"] for c in REGISTRY["checks"]]
    assert len(ids) == 41
    assert len(ids) == len(set(ids))
    for c in REGISTRY["checks"]:
        assert c.get("required_target_evidence_classes") == ["E2_SITE_DIRECT", "E3_REPRODUCIBLE_TEST", "E4_CONNECTED_DATA"]
        assert c.get("aggregation") == "single_or_distribution"


def test_platform_source_groups_resolve():
    groups = {g["id"] for g in LIVE_JSON["groups"]}
    for c in REGISTRY["checks"]:
        if c.get("platform_source_group"):
            assert c["platform_source_group"] in groups


def test_critical_platform_separations_are_documented():
    text = LIVE_MD + "\n" + GEO
    for token in ["OAI-SearchBot", "GPTBot", "Google-Extended", "Claude-SearchBot", "PerplexityBot", "Preferred Sources", "Citation Share"]:
        assert token in text
    assert "No AI-specific Search Console reporting" not in text


def test_schema_detection_false_negative_guard_exists():
    assert "text extractor" in DATA
    assert "not proof" in DATA
    assert "Rich Results Test" in DATA


def test_skill_references_exist():
    refs = re.findall(r'`((?:references|scripts)/[^` ]+)', SKILL)
    for ref in refs:
        assert (ROOT / ref).exists(), ref



def test_registry_math_and_refs_are_structurally_sane():
    ids = {c["id"] for c in REGISTRY["checks"]}
    for gid, gate in REGISTRY["gates"].items():
        assert set(gate.get("requires_nonpass_check_ids", [])) <= ids, gid
    rules = REGISTRY["coverage_rules"]
    assert 0 < rules["withhold_below"] < rules["provisional_below"] <= 100
    for name, weights in REGISTRY["profiles"].items():
        assert set(weights) == {"foundation", "relevance", "authority", "geo", "aeo"}, name
        assert all(v >= 0 for v in weights.values()) and sum(weights.values()) > 0
    tiers = REGISTRY["tiers"]
    assert tiers[0]["min"] == 0 and tiers[-1]["max"] == 100
    for a, b in zip(tiers, tiers[1:]):
        assert a["max"] < b["min"] and round(b["min"] - a["max"], 3) <= 0.001


def test_long_reference_files_have_contents_section():
    for p in (ROOT / "references").glob("*.md"):
        if len(p.read_text(encoding="utf-8").splitlines()) > 100:
            assert "## Contents" in p.read_text(encoding="utf-8")[:1200], p.name


def test_live_sources_are_https_and_have_positive_ttl():
    assert LIVE_JSON["default_ttl_days"] > 0
    for group in LIVE_JSON["groups"]:
        assert group["ttl_days"] > 0
        assert group["official_sources"]
        assert all(x.startswith("https://") for x in group["official_sources"])


def test_skill_frontmatter_is_compact_and_only_name_description():
    assert SKILL.startswith("---\n")
    front = SKILL.split("---", 2)[1]
    top_keys = []
    for line in front.splitlines():
        if line and not line.startswith(" ") and ":" in line:
            top_keys.append(line.split(":", 1)[0])
    assert set(top_keys) == {"name", "description"}
    desc = re.search(r"description:\s*>\n(.*?)\n---", SKILL, re.S).group(1)
    flattened = " ".join(x.strip() for x in desc.splitlines())
    assert len(flattened) <= 1024


def test_no_obvious_old_geo_antipatterns():
    all_text = "\n".join(p.read_text(encoding="utf-8") for p in (ROOT / "references").glob("*.md"))
    assert "40-60 word" not in all_text
    assert "blocking it means that platform can't cite you" not in all_text
    assert "Google-Extended - Google Gemini and AI Overviews" not in all_text


if __name__ == "__main__":
    tests = [name for name, obj in sorted(globals().items()) if name.startswith("test_") and callable(obj)]
    for name in tests:
        globals()[name]()
        print("PASS", name)
