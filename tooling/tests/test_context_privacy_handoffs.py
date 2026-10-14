"""An outer public wrapper cannot change a context's private classification."""
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("context_privacy_wrapper", ROOT / "tooling/validate_envelope.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


@pytest.mark.parametrize("stdlib", [False, True])
@pytest.mark.parametrize("scope", [None, "workspace_private", "project_context"])
def test_public_wrapper_requires_explicit_public_context_scope(stdlib, scope, monkeypatch):
    data = json.loads((ROOT / "fixtures/cwaip-v2/conformance/valid/context-portfolio-governance.json").read_text())
    if scope is None:
        data["payload"].pop("context_scope", None)
    else:
        data["payload"]["context_scope"] = scope
    if scope == "project_context":
        data["payload"]["project_ref"] = "project-a"
        data["payload"]["sources"][0]["project_ref"] = "project-a"
    data["payload_hash"] = module.payload_hash(data["payload"])
    if stdlib:
        monkeypatch.setattr(module, "validate_jsonschema", lambda *args: False)
    with pytest.raises(ValueError, match="public context wrapper requires public_example"):
        module.validate_envelope(data, final=True)


@pytest.mark.parametrize("stdlib", [False, True])
def test_outer_context_sensitivity_cannot_downgrade_nested_records(stdlib, monkeypatch):
    data = json.loads((ROOT / "fixtures/cwaip-v2/conformance/valid/context-portfolio-governance.json").read_text())
    data.update(sensitivity="internal")
    data["payload"]["context_scope"] = "workspace_private"
    for record in data["payload"]["sources"] + data["payload"]["facts"]:
        record["sensitivity"] = "confidential"
    data["payload_hash"] = module.payload_hash(data["payload"])
    if stdlib:
        monkeypatch.setattr(module, "validate_jsonschema", lambda *args: False)
    with pytest.raises(ValueError, match="context wrapper sensitivity"):
        module.validate_envelope(data, final=True)
    data["sensitivity"] = "confidential"
    module.validate_envelope(data, final=True)
