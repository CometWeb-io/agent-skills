"""CW-AIP conformance suite: spec, JSON Schema, validators and fixtures agree.

Every case under fixtures/cwaip-v{1,2}/conformance is listed in its cases.json
with the expected outcome. v2 cases run through tooling/validate_envelope.py
twice, with jsonschema and with the standard library only (``python -S``), and
both runs must reach the same verdict: a host without the optional dependency
must not accept a document that CI rejects. v1 cases run against the canonical
v1 schemas and the orchestrator's between-step gate, which applies the v1 kind
schemas; without jsonschema the gate fails closed, so it never accepts a case
either way.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[2]
V1 = ROOT / "fixtures" / "cwaip-v1" / "conformance"
V2 = ROOT / "fixtures" / "cwaip-v2" / "conformance"
VALIDATOR = ROOT / "tooling" / "validate_envelope.py"
GATE = ROOT / "skills" / "skill-orchestrator-multiagent" / "scripts" / "validate_envelope.py"
V1_SCHEMAS = ROOT / "protocol" / "cw-aip-v1" / "schemas"
V1_KIND_SCHEMAS = {
    "EvidenceEnvelope": "evidence-envelope.schema.json",
    "DecisionHandoff": "decision-handoff.schema.json",
}
V2_DRAFTS = ROOT / "protocol" / "cw-aip-v2" / "draft"
V2_DRAFT_EXAMPLES = ROOT / "fixtures" / "cwaip-v2" / "draft"
V2_DRAFT_KINDS = {
    "SpecialistHandoff": "specialist-handoff",
    "ArtifactEnvelope": "artifact",
    "SnapshotMetadata": "snapshot",
}


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def cases(base: Path) -> list[dict]:
    return json.loads((base / "cases.json").read_text(encoding="utf-8"))["cases"]


def case_id(case: dict) -> str:
    return case["file"].removesuffix(".json")


@pytest.mark.parametrize("base", [V1, V2], ids=["v1", "v2"])
def test_every_fixture_is_listed_exactly_once(base: Path) -> None:
    listed = [case["file"] for case in cases(base)]
    on_disk = sorted(str(p.relative_to(base)) for p in base.glob("*/*.json"))
    assert sorted(listed) == on_disk
    assert len(listed) == len(set(listed))
    for case in cases(base):
        assert case["file"].startswith("valid/" if case["expect"] == "accept" else "invalid/")
        assert case["expect"] == "accept" or case.get("error"), case["file"]


def run_v2(path: Path, final: bool, stdlib_only: bool) -> subprocess.CompletedProcess:
    command = [sys.executable, *(["-S"] if stdlib_only else []), str(VALIDATOR), str(path)]
    if final:
        command.append("--final")
    return subprocess.run(command, capture_output=True, text=True, timeout=60, cwd=ROOT)


@pytest.mark.parametrize("stdlib_only", [False, True], ids=["jsonschema", "stdlib"])
@pytest.mark.parametrize("case", cases(V2), ids=case_id)
def test_v2_case(case: dict, stdlib_only: bool) -> None:
    proc = run_v2(V2 / case["file"], case["final"], stdlib_only)
    if case["expect"] == "accept":
        assert proc.returncode == 0, proc.stderr
        assert proc.stdout.startswith("OK:")
    else:
        assert proc.returncode == 1, proc.stdout
        assert "Traceback" not in proc.stderr
        assert case["error"] in proc.stderr


def test_v2_payload_hash_canonical_form() -> None:
    """Pin the canonical serialization documented in protocol/cw-aip-v2/README.md."""
    mod = load(VALIDATOR, "_cwaip_validate_envelope")
    payload = {"b": [1, 2.5, None, True], "a": {"z": "za\u017c\u00f3\u0142\u0107", "\u00e9": "\u2028"}, "A": "\x01\n\"\\"}
    canonical = '{"A":"\\u0001\\n\\\"\\\\","a":{"z":"za\u017c\u00f3\u0142\u0107","\u00e9":"\u2028"},"b":[1,2.5,null,true]}'
    expected = "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    assert mod.payload_hash(payload) == expected
    gate = load(GATE, "_cwaip_gate")
    assert gate.payload_hash(payload) == expected


def test_v2_payload_hash_rejects_non_finite_numbers() -> None:
    mod = load(VALIDATOR, "_cwaip_validate_envelope")
    with pytest.raises(ValueError):
        mod.payload_hash({"score": float("nan")})


def test_stdlib_fallback_refuses_unknown_schema_keywords() -> None:
    """A keyword the fallback cannot enforce must fail loudly, not be skipped."""
    mod = load(VALIDATOR, "_cwaip_validate_envelope")
    with pytest.raises(ValueError, match="pattern"):
        mod.validate_schema_subset({"type": "string", "pattern": "^x$"}, "y", "payload")
    with pytest.raises(ValueError, match="additionalProperties"):
        mod.validate_schema_subset({"type": "object", "additionalProperties": {"type": "string"}}, {}, "payload")


def test_stdlib_fallback_covers_every_typed_payload_schema() -> None:
    """Payload types without their own validator module are schema-driven in the fallback."""
    mod = load(VALIDATOR, "_cwaip_validate_envelope")
    for envelope_type, schema_path in mod.PAYLOAD_SCHEMAS.items():
        if envelope_type in mod.OWN_FALLBACK:
            continue
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        with pytest.raises(ValueError, match="required property"):
            mod.validate_schema_subset(schema, {}, "payload")


def v1_validator(envelope_type: object) -> Draft202012Validator:
    resources = []
    for path in V1_SCHEMAS.glob("*.schema.json"):
        schema = json.loads(path.read_text(encoding="utf-8"))
        resources.append((schema["$id"], Resource.from_contents(schema)))
    registry = Registry().with_resources(resources)
    name = V1_KIND_SCHEMAS.get(envelope_type, "envelope.core.schema.json") if isinstance(envelope_type, str) else (
        "envelope.core.schema.json"
    )
    schema = json.loads((V1_SCHEMAS / name).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, registry=registry)


@pytest.mark.parametrize("case", cases(V1), ids=case_id)
def test_v1_case_against_canonical_schemas(case: dict) -> None:
    data = json.loads((V1 / case["file"]).read_text(encoding="utf-8"))
    errors = list(v1_validator(data.get("type")).iter_errors(data))
    if case["expect"] == "accept":
        assert errors == []
    else:
        assert errors, "schema accepted an invalid document"
        reported = [f"{error.json_path}: {error.message}" for error in errors]
        assert any(case["error"] in line for line in reported), reported


@pytest.mark.parametrize("case", cases(V1), ids=case_id)
def test_v1_case_through_orchestrator_gate(case: dict) -> None:
    """The gate applies the kind schemas, so it rejects core and kind cases alike."""
    proc = subprocess.run(
        [sys.executable, str(GATE), str(V1 / case["file"])],
        capture_output=True, text=True, timeout=60,
    )
    if case["expect"] == "accept":
        assert proc.returncode == 0, proc.stderr
    else:
        assert proc.returncode == 1, proc.stdout
        assert proc.stderr.startswith("FAIL:")
        assert "Traceback" not in proc.stderr
        assert case["error"] in proc.stderr


@pytest.mark.parametrize(
    "path",
    [*(V1 / c["file"] for c in cases(V1) if c["expect"] == "reject"),
     *(V2 / c["file"] for c in cases(V2) if c["expect"] == "reject")],
    ids=lambda p: f"{p.parent.parent.parent.name}/{p.stem}",
)
def test_orchestrator_gate_never_accepts_invalid_case_without_jsonschema(path: Path) -> None:
    """Stdlib-only hosts fail closed rather than accept what the full gate rejects."""
    proc = subprocess.run([sys.executable, "-S", str(GATE), str(path)], capture_output=True, text=True, timeout=60)
    assert proc.returncode == 1
    assert "Traceback" not in proc.stderr


@pytest.mark.parametrize("case", [c for c in cases(V2) if c["expect"] == "accept"], ids=case_id)
def test_orchestrator_gate_accepts_valid_v2_envelopes(case: dict) -> None:
    command = [sys.executable, str(GATE), str(V2 / case["file"])]
    if case["final"]:
        command.append("--final")
    proc = subprocess.run(command, capture_output=True, text=True, timeout=60)
    assert proc.returncode == 0, proc.stderr
    assert "protocol_version=2.0" in proc.stdout


@pytest.mark.parametrize(
    "name,final,marker",
    [
        ("pending-hash-under-final", True, "pending"),
        ("hash-mismatch", False, "payload_hash mismatch"),
        ("core-unknown-property", False, "schema:"),
        ("core-protocol-version-1", False, "schema:"),
        ("core-missing-payload-hash", False, "payload_hash"),
        ("release-go-with-blockers", False, "GO cannot have blockers"),
        ("release-go-with-controls-with-blockers", False, "GO_WITH_CONTROLS cannot have blockers"),
        ("decision-go-with-blockers", False, "GO cannot have blockers"),
        ("decision-go-blocked-by-gate", False, "GO blocked by gate"),
        ("decision-go-awaiting-human-approval", False, "human_approval=required"),
        ("release-go-with-block-gate", False, "GO blocked by gate security status=BLOCK"),
        ("release-go-with-controls-with-block-gate", False, "GO_WITH_CONTROLS blocked by gate security status=BLOCK"),
        ("release-go-with-lowercase-block-gate", False, "GO blocked by gate privacy status=block"),
        ("release-go-with-counsel-required-gate", False, "GO_WITH_CONTROLS blocked by gate legal status=COUNSEL_REQUIRED"),
    ],
)
def test_orchestrator_gate_rejects_bad_v2_envelope_shapes(name: str, final: bool, marker: str) -> None:
    command = [sys.executable, str(GATE), str(V2 / "invalid" / f"{name}.json")]
    if final:
        command.append("--final")
    proc = subprocess.run(command, capture_output=True, text=True, timeout=60)
    assert proc.returncode == 1
    assert marker in proc.stderr


@pytest.mark.parametrize(
    "expected,fixture,ok",
    [
        ("DecisionHandoff", "valid/decision-test.json", True),
        ("DecisionHandoff", "valid/release-go-with-controls.json", True),
        ("EvidenceEnvelope", "valid/evidence-ready.json", True),
        ("EvidenceEnvelope", "valid/decision-test.json", False),
        ("DecisionHandoff", "valid/finding-open.json", False),
    ],
)
def test_orchestrator_gate_maps_planned_v1_kinds_to_v2_kinds(expected: str, fixture: str, ok: bool) -> None:
    gate = load(GATE, "_cwaip_gate")
    data = json.loads((V2 / fixture).read_text(encoding="utf-8"))
    errors = gate.validate_envelope(data, expected_type=expected)
    assert (errors == []) is ok, errors


def test_orchestrator_gate_does_not_map_v1_documents_to_v2_kinds() -> None:
    gate = load(GATE, "_cwaip_gate")
    data = json.loads((V1 / "valid" / "decision-handoff.json").read_text(encoding="utf-8"))
    assert gate.validate_envelope(data, expected_type="DecisionEnvelope")


def test_orchestrator_gate_rejects_unknown_protocol_version() -> None:
    gate = load(GATE, "_cwaip_gate")
    data = json.loads((V1 / "valid" / "finding-envelope.json").read_text(encoding="utf-8"))
    data["protocol_version"] = "3.0"
    assert any("unsupported protocol_version" in e for e in gate.validate_envelope(data))


def test_v1_spec_mirrors_match_canonical_copies() -> None:
    """protocol/cw-interchange-v1.md and protocol/schemas/ are legacy mirror paths."""
    canonical = ROOT / "protocol" / "cw-aip-v1"
    assert (ROOT / "protocol" / "cw-interchange-v1.md").read_bytes() == (
        canonical / "cw-interchange-v1.md"
    ).read_bytes()
    mirrored = sorted(p.name for p in (ROOT / "protocol" / "schemas").glob("*.json"))
    assert mirrored == sorted(p.name for p in V1_SCHEMAS.glob("*.json"))
    for name in mirrored:
        assert (ROOT / "protocol" / "schemas" / name).read_bytes() == (V1_SCHEMAS / name).read_bytes(), name


def test_v1_spec_documents_every_core_schema_field() -> None:
    spec = (ROOT / "protocol" / "cw-aip-v1" / "cw-interchange-v1.md").read_text(encoding="utf-8")
    core = json.loads((V1_SCHEMAS / "envelope.core.schema.json").read_text(encoding="utf-8"))
    for field in core["properties"]:
        assert f"| `{field}` |" in spec, field
    for kind in core["properties"]["type"]["enum"]:
        assert f"### `{kind}`" in spec, kind
    for field in ("authority", "freshness"):
        for value in core["properties"][field]["enum"]:
            assert f"`{value}`" in spec, value


def test_v2_readme_documents_core_fields_and_payload_types() -> None:
    readme = (ROOT / "protocol" / "cw-aip-v2" / "README.md").read_text(encoding="utf-8")
    core = json.loads((ROOT / "protocol" / "cw-aip-v2" / "core.schema.json").read_text(encoding="utf-8"))
    for field in core["required"]:
        assert f"`{field}`" in readme, field
    for kind in core["properties"]["type"]["enum"]:
        assert kind in readme, kind


def test_v1_kind_schemas_require_payload_and_gate_bundles_them() -> None:
    """Spec revision 1.0.1: a kind with a kind schema must carry its payload."""
    for name in V1_KIND_SCHEMAS.values():
        schema = json.loads((V1_SCHEMAS / name).read_text(encoding="utf-8"))
        assert "payload" in schema["allOf"][1]["required"], name
        bundled = GATE.parents[1] / "references" / name
        assert bundled.read_bytes() == (V1_SCHEMAS / name).read_bytes(), name
    gate = load(GATE, "_cwaip_gate")
    assert set(gate.V1_KIND_SCHEMAS) == set(V1_KIND_SCHEMAS)


def test_valid_v1_fixtures_carry_payload() -> None:
    """Making payload required in the kind schemas broke no shipped valid document."""
    for case in cases(V1):
        if case["expect"] == "accept":
            data = json.loads((V1 / case["file"]).read_text(encoding="utf-8"))
            assert isinstance(data.get("payload"), dict), case["file"]


@pytest.mark.parametrize("kind,stem", sorted(V2_DRAFT_KINDS.items()))
def test_v2_draft_payload_schemas_are_well_formed_and_not_enforced(kind: str, stem: str) -> None:
    schema = json.loads((V2_DRAFTS / f"{stem}.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    assert schema["title"].startswith("DRAFT ") and "not enforced" in schema["title"]
    assert schema["properties"]["schema"]["const"].endswith("/v2-draft")
    assert schema["$id"].endswith(f"/v2/draft/{stem}.schema.json")
    example = json.loads((V2_DRAFT_EXAMPLES / f"{stem}.json").read_text(encoding="utf-8"))
    assert list(Draft202012Validator(schema).iter_errors(example)) == []
    mod = load(VALIDATOR, "_cwaip_validate_envelope")
    # Promotion-ready for the stdlib fallback: only keywords it can enforce.
    mod.validate_schema_subset(schema, example, "draft")
    with pytest.raises(ValueError, match="required property"):
        mod.validate_schema_subset(schema, {}, "draft")
    # Still reserved: no validator maps the kind to a payload schema.
    assert kind not in mod.PAYLOAD_SCHEMAS
    core = json.loads((ROOT / "protocol" / "cw-aip-v2" / "core.schema.json").read_text(encoding="utf-8"))
    assert kind in core["properties"]["type"]["enum"]


def test_v2_draft_directory_matches_reserved_kinds() -> None:
    assert sorted(p.name for p in V2_DRAFTS.glob("*.json")) == sorted(
        f"{stem}.schema.json" for stem in V2_DRAFT_KINDS.values()
    )
    assert sorted(p.name for p in V2_DRAFT_EXAMPLES.glob("*.json")) == sorted(
        f"{stem}.json" for stem in V2_DRAFT_KINDS.values()
    )


def test_v2_reserved_kind_with_draft_payload_is_still_rejected() -> None:
    """A draft payload must not make a reserved kind pass the enforcing validator."""
    mod = load(VALIDATOR, "_cwaip_validate_envelope")
    payload = json.loads((V2_DRAFT_EXAMPLES / "specialist-handoff.json").read_text(encoding="utf-8"))
    envelope = json.loads((V2 / "valid" / "finding-open.json").read_text(encoding="utf-8"))
    envelope.update(type="SpecialistHandoff", payload=payload, payload_hash=mod.payload_hash(payload))
    with pytest.raises(ValueError, match="SpecialistHandoff"):
        mod.validate_envelope(envelope)


def test_spec_documents_revisions() -> None:
    spec = (ROOT / "protocol" / "cw-aip-v1" / "cw-interchange-v1.md").read_text(encoding="utf-8")
    readme = (ROOT / "protocol" / "cw-aip-v2" / "README.md").read_text(encoding="utf-8")
    assert "## Spec revisions" in spec and "1.0.1" in spec
    assert "## Spec revisions" in readme and "2.0.1" in readme and "2.0.2" in readme
    for stem in V2_DRAFT_KINDS.values():
        assert f"draft/{stem}.schema.json" in readme
