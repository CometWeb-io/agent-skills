"""Bounded tests of diagnostics, metadata preservation and freshness semantics."""
import datetime as dt
import json
import sys
import zipfile
from pathlib import Path
import pytest
import yaml

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
from adapter_metadata import merge_openai
from check_knowledge import audit
from compatibility import parse_frontmatter
from doctor import inspect
import generate_adapters as adapters
import package_skill as package
from test_distribution_hardening import root, add


def test_dependency_and_unknown_metadata_survive_generation():
    previous = 'interface:\n  brand_color: "#123456"\npolicy:\n  products: [codex]\n  custom_flag: true\ndependencies:\n  tools:\n    - type: mcp\n      value: example\n      transport: streamable_http\n      url: https://example.invalid/mcp\ncustom: preserved\n'
    data = yaml.safe_load(merge_openai({"explicit_only":False}, previous, {"display_name":"Example"}))
    assert data["dependencies"]["tools"][0]["value"] == "example"
    assert data["policy"]["products"] == ["codex"]
    assert data["policy"]["custom_flag"] is True
    assert data["interface"]["brand_color"] == "#123456"
    assert data["custom"] == "preserved"


def test_explicit_registry_policy_wins():
    data = yaml.safe_load(merge_openai({"explicit_only":True}, 'policy:\n  allow_implicit_invocation: true\n', {}))
    assert data["policy"]["allow_implicit_invocation"] is False


def test_metadata_roundtrip_quotes_and_multiline():
    text = 'quote: "word"\nsecond line # not a comment'
    assert yaml.safe_load(merge_openai({}, None, {"default_prompt":text}))["interface"]["default_prompt"] == text


def test_registry_tool_dependencies_can_be_explicitly_updated():
    data = yaml.safe_load(merge_openai({"tool_dependencies":[{"type":"mcp","value":"new"}]}, 'dependencies:\n  tools: [{type: mcp, value: old}]\n', {}))
    assert data["dependencies"]["tools"] == [{"type":"mcp","value":"new"}]


@pytest.mark.parametrize("text", ['[]','interface: text','policy: false','dependencies: []','dependencies: {tools: nope}','dependencies: {tools: [{type: unknown, value: x}]}'])
def test_bad_adapter_metadata_blocks(text):
    with pytest.raises(ValueError):
        merge_openai({}, text, {})


def test_semantically_identical_adapter_preserves_format():
    old='interface:\n  display_name: "Demo"\npolicy:\n  products: [codex]\n  allow_implicit_invocation: true\n'
    assert merge_openai({}, old, {"display_name":"Demo"}) == old


def test_adapter_check_does_not_repair_before_check(root, monkeypatch):
    monkeypatch.setattr(adapters, "ROOT", root)
    monkeypatch.setattr(adapters, "REGISTRY", root / "registry/skills.json")
    monkeypatch.setattr(adapters, "SKILLS", root / "skills")
    monkeypatch.setattr(adapters, "OUT_DOCS", root / "docs/table.md")
    monkeypatch.setattr(adapters, "OUT_CURSOR", root / "docs/routing.mdc")
    monkeypatch.setattr(sys, "argv", ["generate_adapters.py", "--check"])
    before = {p.relative_to(root):p.read_bytes() for p in root.rglob("*") if p.is_file()}
    with pytest.raises(SystemExit):
        adapters.main()
    after = {p.relative_to(root):p.read_bytes() for p in root.rglob("*") if p.is_file()}
    assert before == after


@pytest.mark.parametrize("length,valid", [(0,False),(1,True),(1024,True),(1025,False)])
def test_frontmatter_description_limit(root, length, valid):
    add(root, "SKILL.md", ('---\nname: demo\ndescription: "' + 'x'*length + '"\n---\n').encode())
    if valid:
        assert len(parse_frontmatter(root / "skills/demo/SKILL.md")["description"]) == length
    else:
        with pytest.raises(ValueError):
            parse_frontmatter(root / "skills/demo/SKILL.md")


@pytest.mark.parametrize("body", ["name: demo\nname: other\ndescription: text", "name: other\ndescription: text", "name: demo\ndescription: [text]", "name: demo\ndescription: true", "name: demo\ndescription: ' '"])
def test_invalid_frontmatter_cannot_pass_minimal_parser(root, body):
    add(root, "SKILL.md", ('---\n'+body+'\n---\n').encode())
    with pytest.raises(ValueError):
        parse_frontmatter(root / "skills/demo/SKILL.md")


def test_doctor_does_not_invent_installation_or_session(root):
    result = inspect(root, "demo")
    assert result["source"] == "present"
    assert result["installed"] == "not_checked"
    assert result["session_visibility"] == "unknown"
    assert result["runtime_acceptance"] == "not_assessed"


def test_doctor_detects_installed_content_drift(root):
    built = package.build(root, "demo")
    installed = root / "installed"
    with zipfile.ZipFile(root / built["path"]) as zf:
        zf.extractall(installed / "demo")
    assert inspect(root, "demo", installed)["installed"] == "matches_package"
    (installed / "demo/LICENSE").write_text("changed")
    assert inspect(root, "demo", installed)["installed"] == "drifted"


def test_reported_session_is_not_authenticated_runtime(root):
    inventory={"schema":"cometweb.session-inventory/v1","observed_at":"2026-09-12T12:00:00Z","session_id":"fixture-session","host":"fixture-host","skills":["demo"]}
    result=inspect(root,"demo",session_inventory=inventory)
    assert result["session_visibility"] == "reported_visible"
    assert result["runtime_acceptance"] == "not_assessed"


def test_session_inventory_requires_provenance(root):
    with pytest.raises(ValueError):
        inspect(root,"demo",session_inventory={"skills":["demo"]})


@pytest.mark.parametrize("as_of,status", [("2026-08-01","future_verification"),("2026-09-12","within_ttl"),("2026-10-20","stale")])
def test_existing_seo_freshness_registry_is_consumed_without_date_rewriting(as_of,status):
    data={"default_ttl_days":30,"groups":[{"id":"fixture","last_verified":"2026-09-01","official_sources":["https://example.invalid"],"claims":["claim"]}]}
    before=json.dumps(data)
    result=audit(data,dt.date.fromisoformat(as_of))
    assert result["results"][0]["status"] == status
    assert result["external_verification"] == "not_run"
    assert json.dumps(data) == before


def rule(**changes):
    value={"id":"r1","state":"active","kind":"heuristic","statement":"fixture","scope":"fixture","verified_at":"2026-09-12","ttl_days":30,"sources":["https://example.invalid"],"regression_tests":["fixture-test"]}
    value.update(changes)
    return {"schema":"cometweb.knowledge-rules/v1","rules":[value]}


@pytest.mark.parametrize("changes", [{"ttl_days":True},{"ttl_days":0},{"kind":"ranking-guarantee"},{"sources":[]},{"regression_tests":[]},{"state":"verified"},{"verified_at":"bad-date"}])
def test_active_rule_requires_typed_evidence(changes):
    with pytest.raises(ValueError):
        audit(rule(**changes),dt.date(2026,9,12))


@pytest.mark.parametrize("state", ["unverified","withdrawn"])
def test_rule_can_be_withdrawn_without_reverifying_entire_skill(state):
    result=audit(rule(state=state,verified_at=None,sources=[]),dt.date(2026,9,12))
    assert result["results"][0]["status"] == state
    assert result["results"][0]["claim_truth"] == "not_reverified"


def test_doctor_corrupt_archive_is_invalid_not_crash(root):
    p=root / "dist/demo/skill.zip"
    p.parent.mkdir(parents=True)
    p.write_bytes(b"not a zip")
    assert inspect(root,"demo")["package"] == "invalid"


def test_doctor_detects_same_version_source_drift(root):
    package.build(root,"demo")
    add(root,"LICENSE",b"different source")
    assert "source_package_content_mismatch" in inspect(root,"demo")["issues"]


@pytest.mark.parametrize("date", ["bad", "2026-01-01T01:00:00", "2999-01-01T00:00:00Z"])
def test_doctor_rejects_invalid_observation_time(root,date):
    with pytest.raises(ValueError):
        inspect(root,"demo",session_inventory={"schema":"cometweb.session-inventory/v1","observed_at":date,"session_id":"s","host":"h","skills":[]})


def test_packager_duplicate_frontmatter_rejected(root):
    add(root,"SKILL.md",b"---\nname: other\nname: demo\ndescription: Test\n---\n")
    with pytest.raises(ValueError):
        package.build(root,"demo")


def test_wrong_package_identity_cannot_verify_installation(root):
    entries,manifest=package.payload(root,"demo")
    manifest["skill"]="other"
    target=root / "dist/demo/skill.zip"
    target.parent.mkdir(parents=True)
    target.write_bytes(package.archive(entries,manifest))
    installed=root / "installed/demo"
    installed.mkdir(parents=True)
    for name,data in entries.items():
        p=installed/name
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_bytes(data)
    result=inspect(root,"demo",root / "installed")
    assert result["package"] == "invalid"
    assert result["installed"] == "present_unverified"


def test_adapter_merge_rejects_duplicate_keys():
    with pytest.raises(ValueError):
        merge_openai({},"policy: {}\npolicy: {}\n",{})
