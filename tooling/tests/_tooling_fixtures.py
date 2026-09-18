"""Fixtures and builders shared by several tooling test modules.

These used to be imported from a sibling test module, which only resolves under
pytest's prepend import mode and made one test file a dependency of another.
Keeping them in a plain module, reached through the same explicit sys.path entry
the tests already use for tooling/, works whichever import mode a runner picks.

Importing a fixture function into a test module registers it there, so
consumers do `from _helpers import root, add` exactly as before.
"""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
from pathlib import Path
import sys

import pytest

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))

import package_skill
import run_model_evals as runner


@pytest.fixture
def root(tmp_path):
    (tmp_path / "registry").mkdir()
    shutil.copyfile(TOOLS.parent / "registry/package-policy.json", tmp_path / "registry/package-policy.json")
    (tmp_path / "registry/public-allowlist.json").write_text(json.dumps({"schema": "cometweb.public-allowlist/v1", "approved": []}))
    (tmp_path / "registry/skills.json").write_text(json.dumps({"schema": "cometweb.skills-registry/v1", "skills": [{"id": "demo", "version": "1.0.0", "lifecycle": "active", "visibility": "private_canonical", "description": "Synthetic fixture"}]}))
    source = tmp_path / "skills/demo"
    source.mkdir(parents=True)
    (source / "SKILL.md").write_text("---\nname: demo\ndescription: Synthetic regression fixture for distribution checks.\n---\n# Demo\n")
    (source / "VERSION").write_text("1.0.0\n")
    (source / "LICENSE").write_text("Synthetic fixture license.\n")
    (tmp_path / "tooling").mkdir()
    shutil.copyfile(TOOLS / "public_safety.py", tmp_path / "tooling/public_safety.py")
    return tmp_path


def add(root, name, data=b"fixture"):
    path = root / "skills/demo" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def records_for(suite,requests):
    result=[]
    for index,(key,request) in enumerate(requests.items()):
        cid,condition=key
        output=f"Synthetic conformance response {index}; NOT a model call"
        response={"schema":"cometweb.eval-response/v1","status":"completed", "execution_kind":"model",
                  "model":"synthetic-label","host":"synthetic-host","response_id":f"synthetic-{index}",
                  "output":output,"usage":{},"tool_trace":[],"capabilities":request["capabilities"]}
        result.append({"case":cid,"repeat":0,"condition":condition,"status":"executed","response":response,
                       "input_sha256":package_skill.digest(package_skill.canonical(request)),
                       "output_sha256":hashlib.sha256(output.encode()).hexdigest(),"elapsed_seconds":0.02,
                       "blind_id":f"output-{index:04d}"})
    return result


@pytest.fixture
def packet_source(tmp_path):
    roots=[]
    for variant in ("current","candidate"):
        root=tmp_path/variant;(root/"skills/demo").mkdir(parents=True)
        (root/"skills/demo/SKILL.md").write_text(f"Synthetic {variant} instructions")
        roots.append(root)
    cases=[{"id":f"case-{i}","skill":"demo","prompt":f"Synthetic task {i}","fixture":{"x":i},"rubric":["Do not invent evidence"]} for i in range(2)]
    suite={"schema":"cometweb.model-evals/v1","cases":cases}
    requests={(c["id"],v):runner.prepare(c,v,*roots,256) for c in cases for v in runner.CONDITIONS}
    return suite,requests,records_for(suite,requests),roots


def response(**changes):
    value={"schema":"cometweb.eval-response/v1","status":"completed","execution_kind":"mock","model":"synthetic-test-model","host":"synthetic-test-host","response_id":"mock-id","output":"Synthetic text 20%","usage":{"input_tokens":1,"output_tokens":2},"tool_trace":[],"capabilities":{"tools":False}}
    value.update(changes)
    return value


def case():
    return {"id":"fixture-case","skill":"demo","prompt":"Edit this sentence.","fixture":{"text":"20% may help"},"rubric":["Preserve uncertainty"],"preserve_literals":["20%"]}
