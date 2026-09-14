"""ZIP admission regressions using entirely synthetic skill payloads."""
import copy
import io
import json
from pathlib import Path
import sys
import zipfile

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import package_skill as mod


def sample():
    entries={"SKILL.md":b"---\nname: demo\ndescription: A synthetic fixture for package validation.\n---\n# Demo\n", "VERSION":b"1.0.0\n", "LICENSE":b"Synthetic fixture license.\n"}
    manifest={"schema":"cometweb.package/v1","skill":"demo","version":"1.0.0", "policy_sha256":"a"*64, "files":{p:mod.digest(b) for p,b in entries.items()},"runtime_acceptance":"not_assessed"}
    manifest["payload_sha256"]=mod.digest(mod.canonical({"files":manifest["files"],"policy_sha256":manifest["policy_sha256"]}))
    return entries,manifest


def forged(entries,manifest):
    manifest["files"]={p:mod.digest(b) for p,b in entries.items()}
    manifest["payload_sha256"]=mod.digest(mod.canonical({"files":manifest["files"],"policy_sha256":manifest["policy_sha256"]}))
    return mod.archive(entries,manifest)


@pytest.mark.parametrize("field,value",[("skill","other"),("version","2.0.0"),("runtime_acceptance","passed"),("runtime_acceptance",True),("policy_sha256","not-a-hash")])
def test_hashed_payload_does_not_bless_false_manifest_claims(field,value):
    entries,manifest=sample();manifest[field]=value
    with pytest.raises(ValueError):mod.inspect_archive(forged(entries,manifest))


def test_synthetic_well_formed_manifest_still_not_authenticated():
    entries,manifest=sample()
    assert mod.inspect_archive(mod.archive(entries,manifest))["runtime_acceptance"]=="not_assessed"


@pytest.mark.parametrize("entry",["SKILL.md","VERSION","LICENSE"])
def test_required_identity_files_cannot_disappear(entry):
    entries,manifest=sample();entries.pop(entry)
    with pytest.raises(ValueError):mod.inspect_archive(forged(entries,manifest))


@pytest.mark.parametrize("name",["C:drive.txt","x//y.txt","x/./y.txt","./README.md","folder/","x\ny.txt",".env","skill.md"])
def test_nonportable_or_unsafe_names_rejected(name):
    entries,manifest=sample();entries[name]=b"synthetic"
    with pytest.raises(ValueError):mod.inspect_archive(forged(entries,manifest))


def test_unknown_manifest_claims_are_not_admitted():
    entries,manifest=sample();manifest["all_hosts_verified"]=True
    with pytest.raises(ValueError):mod.inspect_archive(mod.archive(entries,manifest))


@pytest.mark.parametrize("source",[
 {"source_revision":"abc","source_tree":"clean"},
 {"source_revision":None,"source_tree":"clean"},
 {"source_revision":"a"*40,"source_tree":"unavailable"},
 {"source_revision":"a"*40},
 {"source_tree":"dirty"},
])
def test_inconsistent_source_provenance_rejected(source):
    entries,manifest=sample();manifest.update(source)
    with pytest.raises(ValueError):mod.inspect_archive(mod.archive(entries,manifest))


def test_duplicate_json_manifest_keys_rejected():
    entries,manifest=sample()
    raw=mod.canonical(manifest).decode().replace('"skill": "demo"','"skill": "other", "skill": "demo"')
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w') as z:
        for n,b in entries.items():z.writestr(n,b)
        z.writestr(mod.MANIFEST,raw)
    with pytest.raises(ValueError):mod.inspect_archive(stream.getvalue())


def test_special_unix_file_mode_rejected():
    entries,manifest=sample();stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w') as z:
        for n,b in {**entries,mod.MANIFEST:mod.canonical(manifest)}.items():
            info=zipfile.ZipInfo(n);info.create_system=3;info.external_attr=0o010644<<16
            z.writestr(info,b)
    with pytest.raises(ValueError):mod.inspect_archive(stream.getvalue())
