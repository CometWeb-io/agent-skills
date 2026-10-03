#!/usr/bin/env python3
"""Hold every skill's scripts, docs and eval cases to one declared contract.

An agent loading a skill cold builds its payload from the references, not from
the kernel source. When the two drift, the agent writes a field the kernel never
reads, or a value the kernel rejects, and nothing complains: repair-operator
documented `dependencies[]` while its kernel read `depends_on`, web-app-auditor
documented the verdict "do not ship" while its validator accepts only
`do_not_ship`, and longform-publisher documented an UNRESOLVED material claim as
allowed while its kernel rejects it.

Every skill that ships a script declares its contract in one machine-readable
file, `references/contract.json` (schema `cometweb.skill-contract/v1`):

    {
      "schema": "cometweb.skill-contract/v1",
      "docs": ["references/output-contract.md"],   # where the contract is written down
      "json_schemas": ["assets/report.schema.json"],  # optional: fields and enums imported
      "scripts": {                                  # every .py under scripts/ is covered
        "scripts/kernel.py": {"input": "json", "enums": {"VALID_STATUS": "status",
                                                         "STATES": ["github", "notion"]}},
        "scripts/run_evals.py": {"input": "none", "role": "eval-harness"}
      },
      "fields": {"repair_id": {}, "items.status": {"enum": ["OPEN", "CLOSED"]}},
      "outputs": {"status": {"enum": ["VALID", "INVALID"]}, "errors": {}},
      "internal": ["errors"],         # keys a script reads that are not payload fields
      "doc_terms": ["run_evals"],     # backticked snake_case words in docs that are not fields
      # status: dotted path to the expected status; or errors: dotted path to an
      # expected error list ([] means "pass"); or expect: one fixed status.
      "evals": [{"path": "evals/cases.json", "cases": "", "input": "input",
                 "status": "expect.status", "pass": ["VALID"],
                 "exempt": {"case-id": "why this case may break the contract and still pass"},
                 "conform": "pass"}]   # or "always": every input must conform, whatever it expects
    }

Checks, each failing with the skill and the offending names:

1. scripts: every `.py` file under `scripts/` is covered by a declared path.
2. kernel -> contract: every literal key a non-harness script reads
   (`x.get("k")`, `x["k"]`) is a contract field or listed as internal.
3. contract -> kernel: every declared field and internal key occurs as a string
   literal in a script or an imported JSON Schema; nothing is declared that no
   code knows about.
4. enums: each mapped module constant equals the field's declared enum, and a
   JSON Schema enum for the same property equals it too.
5. contract -> docs: every field name and every enum value appears verbatim in
   the declared docs or SKILL.md.
6. docs -> contract: every key in a fenced JSON block, every leading name in a
   fenced text/yaml schema block, and every backticked snake_case word in the
   declared docs is a field, an enum value, internal, or a doc term.
7. evals: every key of every eval input is a field (or sits under a field
   declared `"map": true`), every expected status is a declared status, and a
   case whose input breaks the contract never expects a passing status. With
   `"conform": "always"` every input must conform whatever it expects (unless
   exempt), for corpora that pin something other than a pass/fail status.

Run `python3 tooling/skill_contracts.py --check` (also run under pytest by
`tooling/tests/test_contract_docs_match_kernels.py`), or `--draft SKILL` to
print a starting contract for a package that has none.
"""
from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterator

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
CONTRACT = "references/contract.json"
SCHEMA = "cometweb.skill-contract/v1"

FIELD_GET = re.compile(r"""\.get\(\s*['"]([A-Za-z_][\w-]*)['"]""")
FIELD_SUB = re.compile(r"""(?<=[\w)\]])\[\s*['"]([A-Za-z_][\w-]*)['"]\s*\](?!\s*(?:=[^=]|\+=|-=|\|=))""")
STRING_LITERAL = re.compile(r"""['"]([A-Za-z_][\w.-]*)['"]""")
BACKTICK = re.compile(r"`([a-z][a-z0-9]*(?:_[a-z0-9]+)+)(?:\[\])?\??`")
FENCE = re.compile(r"^```([\w-]*)[^\n]*\n(.*?)^```", re.M | re.S)
SCHEMA_LINE = re.compile(r"^\s*(?:-\s+)?([a-z][a-z0-9]*(?:_[a-z0-9]+)*)(\[\])?(\?)?\s*(:|$|\s{2,}|\s#)")
# enum: the accepted values. enforced: false marks an enum the scripts do not
# check (otherwise a script constant must be mapped to it). map: an object keyed
# by ids whose values are records. opaque: free-form content, not walked.
# unread: a documented payload field the scripts deliberately do not read.
FIELD_KEYS = {"enum", "enforced", "map", "opaque", "unread"}
INPUT_KINDS = {"json", "text", "files", "args", "none"}
ROLES = {"kernel", "validator", "helper", "eval-harness"}
TOP_KEYS = {"schema", "docs", "json_schemas", "scripts", "fields", "outputs", "internal", "doc_terms", "evals"}


def skills_with_scripts() -> list[str]:
    return sorted(p.parent.parent.name for p in SKILLS.glob("*/scripts/*.py"))


def unique_skills() -> list[str]:
    return sorted(set(skills_with_scripts()))


def load_contract(skill: str) -> dict[str, Any]:
    return json.loads((SKILLS / skill / CONTRACT).read_text(encoding="utf-8"))


def script_files(skill: str) -> list[Path]:
    return sorted(p for p in (SKILLS / skill / "scripts").rglob("*.py") if "__pycache__" not in p.parts)


def covered(rel: str, declared: dict[str, Any]) -> str | None:
    for key in declared:
        if rel == key or rel.startswith(key.rstrip("/") + "/"):
            return key
    return None


def reads(text: str) -> set[str]:
    return set(FIELD_GET.findall(text)) | set(FIELD_SUB.findall(text))


def literals(text: str) -> set[str]:
    return set(STRING_LITERAL.findall(text))


def schema_vocabulary(schema: Any, under: str | None = None) -> tuple[set[str], dict[str, set[str]]]:
    """Property names, and enums keyed `parent.name` (or `name` at the root).

    `under` names the payload key a schema is mounted at, so a finding schema
    referenced from `findings[]` yields `findings.kind`, apart from
    `environment.kind` in the report schema.
    """
    names: set[str] = set()
    enums: dict[str, set[str]] = {}

    def walk(node: Any, prop: str | None, parent: str | None) -> None:
        if isinstance(node, dict):
            if prop is not None and isinstance(node.get("enum"), list):
                key = f"{parent}.{prop}" if parent else prop
                enums.setdefault(key, set()).update(str(v) for v in node["enum"])
            for key, value in node.items():
                if key == "properties" and isinstance(value, dict):
                    for name, sub in value.items():
                        names.add(name)
                        walk(sub, name, prop if prop is not None else parent)
                elif key == "required" and isinstance(value, list):
                    names.update(v for v in value if isinstance(v, str))
                elif key in {"items", "additionalProperties", "then", "else"}:
                    # `if` and `not` hold conditions, not the values a field accepts.
                    walk(value, prop, parent)
                elif key in {"allOf", "anyOf", "oneOf"} and isinstance(value, list):
                    for sub in value:
                        walk(sub, prop, parent)
                elif key in {"$defs", "definitions"} and isinstance(value, dict):
                    for sub in value.values():
                        walk(sub, None, None)
        elif isinstance(node, list):
            for sub in node:
                walk(sub, prop, parent)

    walk(schema, None, under)
    return names, enums


def schema_entries(contract: dict[str, Any]) -> list[tuple[str, str | None]]:
    """`json_schemas` entries as (path, mount key); an entry is a path or {path, under}."""
    out = []
    for entry in contract.get("json_schemas", []):
        out.append((entry, None) if isinstance(entry, str) else (entry["path"], entry.get("under")))
    return out


def bare(name: str) -> str:
    """`items.status` -> `status`: the key as it appears in a payload."""
    return name.rsplit(".", 1)[-1]


def vocabulary(skill: str, contract: dict[str, Any]) -> tuple[dict[str, dict], set[str]]:
    """Declared input fields plus JSON-Schema properties, and the schema property names.

    A field key is either a bare payload key (`repair_id`) or one qualified by
    its parent key (`items.status`) when the same key carries a different enum
    at another level.
    """
    fields: dict[str, dict] = {k: dict(v) for k, v in contract.get("fields", {}).items()}
    schema_names: set[str] = set()
    for rel, under in schema_entries(contract):
        names, schema_enums = schema_vocabulary(json.loads((SKILLS / skill / rel).read_text(encoding="utf-8")), under)
        schema_names |= names
        for name in names:
            fields.setdefault(name, {})
        for name, values in schema_enums.items():
            if name in contract.get("fields", {}) and "enum" in contract["fields"][name]:
                continue
            # Several schemas may define one property (versioned envelopes): accept the union.
            merged = set(fields.get(name, {}).get("enum", [])) | values
            fields.setdefault(name, {})["enum"] = sorted(merged)
    return fields, schema_names


def all_specs(skill: str, contract: dict[str, Any]) -> dict[str, dict]:
    fields, _ = vocabulary(skill, contract)
    return {**fields, **{f"output:{k}": v for k, v in contract.get("outputs", {}).items()}}


def known_names(skill: str, contract: dict[str, Any]) -> set[str]:
    fields, _ = vocabulary(skill, contract)
    return ({bare(k) for k in fields} | {bare(k) for k in contract.get("outputs", {})}
            | set(contract.get("internal", [])))


def enum_values(skill: str, contract: dict[str, Any]) -> set[str]:
    return {str(v) for spec in all_specs(skill, contract).values() for v in spec.get("enum", [])}


def documentation(skill: str, contract: dict[str, Any]) -> tuple[str, str]:
    """(declared docs text, declared docs plus SKILL.md text)."""
    base = SKILLS / skill
    declared = "\n".join((base / rel).read_text(encoding="utf-8") for rel in contract.get("docs", []))
    return declared, declared + "\n" + (base / "SKILL.md").read_text(encoding="utf-8")


def word_in(word: str, text: str) -> bool:
    return re.search(rf"(?<![\w-]){re.escape(word)}(?![\w-])", text) is not None


def documented_terms(text: str) -> set[str]:
    """Field-like names a reader would take as part of the contract."""
    terms: set[str] = set(BACKTICK.findall(text))
    for lang, body in FENCE.findall(text):
        if lang == "json":
            try:
                terms |= json_keys(json.loads(body))
            except json.JSONDecodeError:
                terms |= set(re.findall(r'"([A-Za-z_][\w-]*)"\s*:', body))
        elif lang in {"text", "yaml", "yml", ""}:
            for line in body.splitlines():
                match = SCHEMA_LINE.match(line)
                if match and ("_" in match.group(1) or match.group(2) or match.group(3) or match.group(4) == ":"):
                    terms.add(match.group(1))
    return terms


def json_keys(value: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            keys.add(key)
            keys |= json_keys(child)
    elif isinstance(value, list):
        for child in value:
            keys |= json_keys(child)
    return keys


def get_path(obj: Any, path: str) -> Any:
    if not path:
        return obj
    current = obj
    for part in path.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        elif isinstance(current, list) and part.isdigit() and int(part) < len(current):
            current = current[int(part)]
        else:
            return None
    return current


def nonconforming(value: Any, fields: dict[str, dict], parent: str | None = None) -> list[str]:
    """Contract breaches inside one eval input: unknown keys and off-enum values."""
    problems: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            name = f"{parent}.{key}" if parent and f"{parent}.{key}" in fields else key
            if name not in fields:
                problems.append(f"unknown field {key!r}")
                continue
            spec = fields[name]
            if "enum" in spec:
                if isinstance(child, list):
                    values = child
                elif spec.get("map") and isinstance(child, dict):
                    values = list(child.values())  # an enum on a map constrains each value
                else:
                    values = [child]
                for value in values:
                    if isinstance(value, (str, bool, int)) and value not in spec["enum"]:
                        problems.append(f"{name}={value!r} not in enum")
            if spec.get("opaque"):
                continue
            if spec.get("map") and isinstance(child, dict):
                for sub in child.values():
                    problems += nonconforming(sub, fields, key)
            else:
                problems += nonconforming(child, fields, key)
    elif isinstance(value, list):
        for child in value:
            problems += nonconforming(child, fields, parent)
    return problems


def eval_cases(skill: str, spec: dict[str, Any]) -> Iterator[tuple[str, Any]]:
    base = SKILLS / skill
    paths = sorted(base.glob(spec["path"])) if any(c in spec["path"] for c in "*?[") else [base / spec["path"]]
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        cases = get_path(data, spec["cases"]) if "cases" in spec else [data]
        for index, case in enumerate(cases if isinstance(cases, list) else []):
            name = (case.get("id") or case.get("name")) if isinstance(case, dict) else None
            yield f"{path.relative_to(base)}#{name or index}", case


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location(f"_contract_{path.parent.parent.name}_{path.stem}".replace("-", "_"), path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    # Registered first so dataclasses under `from __future__ import annotations` resolve.
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(spec.name, None)
        raise
    return module


def check_structure(skill: str, contract: dict[str, Any]) -> list[str]:
    errors = []
    if contract.get("schema") != SCHEMA:
        errors.append(f"schema must be {SCHEMA}")
    errors += [f"unknown top-level key {k!r}" for k in sorted(set(contract) - TOP_KEYS)]
    base = SKILLS / skill
    for rel in contract.get("docs", []) + [path for path, _ in schema_entries(contract)]:
        if not (base / rel).is_file():
            errors.append(f"declared file missing: {rel}")
    if not contract.get("docs"):
        errors.append("docs must name at least one file that documents the contract")
    for rel, spec in contract.get("scripts", {}).items():
        if not (base / rel).exists():
            errors.append(f"declared script missing: {rel}")
        if spec.get("input") not in INPUT_KINDS:
            errors.append(f"{rel}: input must be one of {sorted(INPUT_KINDS)}")
        if spec.get("role", "kernel") not in ROLES:
            errors.append(f"{rel}: role must be one of {sorted(ROLES)}")
        if set(spec) - {"input", "role", "enums"}:
            errors.append(f"{rel}: unknown keys {sorted(set(spec) - {'input', 'role', 'enums'})}")
    for group in ("fields", "outputs"):
        for name, spec in contract.get(group, {}).items():
            if set(spec) - FIELD_KEYS:
                errors.append(f"{group}.{name}: unknown keys {sorted(set(spec) - FIELD_KEYS)}")
            if "enum" in spec and (not isinstance(spec["enum"], list) or not spec["enum"]):
                errors.append(f"{group}.{name}: enum must be a non-empty list")
    names = {bare(k) for k in contract.get("fields", {})} | {bare(k) for k in contract.get("outputs", {})}
    overlap = set(contract.get("internal", [])) & names
    if overlap:
        errors.append(f"both a contract name and internal: {sorted(overlap)}")
    for spec in contract.get("evals", []):
        if set(spec) - {"path", "cases", "input", "status", "errors", "expect", "pass", "exempt", "conform"}:
            errors.append(f"eval {spec.get('path')}: unknown keys")
        if spec.get("conform", "pass") not in {"pass", "always"}:
            errors.append(f"eval {spec.get('path')}: conform must be 'pass' or 'always'")
    return errors


def check_scripts_covered(skill: str, contract: dict[str, Any]) -> list[str]:
    declared = contract.get("scripts", {})
    base = SKILLS / skill
    return [f"script not declared in {CONTRACT}: {p.relative_to(base)}"
            for p in script_files(skill) if covered(str(p.relative_to(base)), declared) is None]


def code_text(skill: str, contract: dict[str, Any], harness: bool) -> str:
    """Source of the declared scripts; harness=False leaves eval harnesses out."""
    declared = contract.get("scripts", {})
    base = SKILLS / skill
    chunks = []
    for path in script_files(skill):
        key = covered(str(path.relative_to(base)), declared)
        if key is None:
            continue
        if not harness and declared[key].get("role") == "eval-harness":
            continue
        chunks.append(path.read_text(encoding="utf-8"))
    return "\n".join(chunks)


def check_kernel_reads(skill: str, contract: dict[str, Any]) -> list[str]:
    unknown = sorted(reads(code_text(skill, contract, harness=False)) - known_names(skill, contract))
    return [f"scripts read keys the contract does not declare: {unknown}"] if unknown else []


def check_declared_are_used(skill: str, contract: dict[str, Any]) -> list[str]:
    _, schema_names = vocabulary(skill, contract)
    code = literals(code_text(skill, contract, harness=False))
    declared = ({bare(k) for k, v in contract.get("fields", {}).items() if not v.get("unread")}
                | {bare(k) for k in contract.get("outputs", {})} | set(contract.get("internal", [])))
    stale = sorted(n for n in declared if n not in code and n not in schema_names)
    return [f"declared names no script or schema knows: {stale}"] if stale else []


def check_enums(skill: str, contract: dict[str, Any]) -> list[str]:
    errors = []
    fields, _ = vocabulary(skill, contract)
    # A name that is both a field and an output binds to whichever declares
    # the enum, preferring the payload field.
    outputs = contract.get("outputs", {})
    specs = {name: fields[name] if "enum" in fields.get(name, {}) or name not in outputs else outputs[name]
             for name in set(fields) | set(outputs)}
    for rel, spec in contract.get("scripts", {}).items():
        mapping = spec.get("enums") or {}
        if not mapping:
            continue
        module = load_module(SKILLS / skill / rel)
        for constant, targets in mapping.items():
            for field in [targets] if isinstance(targets, str) else targets:
                if "enum" not in specs.get(field, {}):
                    errors.append(f"{rel}:{constant} maps to {field!r}, which declares no enum")
                    continue
                if not hasattr(module, constant):
                    errors.append(f"{rel} has no constant {constant}")
                    continue
                accepted = {str(v) for v in getattr(module, constant)}
                if accepted != {str(v) for v in specs[field]["enum"]}:
                    errors.append(f"{rel}:{constant} accepts {sorted(accepted)} but the contract declares "
                                  f"{field!r} as {sorted(specs[field]['enum'])}")
    mapped = {f for spec in contract.get("scripts", {}).values() for v in (spec.get("enums") or {}).values()
              for f in ([v] if isinstance(v, str) else v)}
    unbound = sorted(name for name, spec in contract.get("fields", {}).items()
                     if "enum" in spec and spec.get("enforced", True) and not spec.get("unread") and name not in mapped)
    if unbound:
        errors.append(f"enums no script constant enforces (map one, or declare enforced: false): {unbound}")
    for rel, under in schema_entries(contract):
        _, schema_enums = schema_vocabulary(json.loads((SKILLS / skill / rel).read_text(encoding="utf-8")), under)
        for name, values in schema_enums.items():
            declared = contract.get("fields", {}).get(name, {})
            if "enum" in declared and values != {str(v) for v in declared["enum"]}:
                errors.append(f"{rel} enum for {name!r} is {sorted(values)} but the contract declares "
                              f"{sorted(declared['enum'])}")
    return errors


def check_docs_cover_contract(skill: str, contract: dict[str, Any]) -> list[str]:
    _, docs = documentation(skill, contract)
    specs = all_specs(skill, contract)
    missing_fields = sorted({bare(k.removeprefix("output:")) for k in specs} - {
        n for n in {bare(k.removeprefix("output:")) for k in specs} if word_in(n, docs)})
    missing_values = sorted({f"{k.removeprefix('output:')}={v}" for k, s in specs.items()
                             for v in s.get("enum", []) if not word_in(str(v), docs)})
    errors = []
    if missing_fields:
        errors.append(f"fields not documented: {missing_fields}")
    if missing_values:
        errors.append(f"enum values not documented verbatim: {missing_values}")
    return errors


def check_docs_within_contract(skill: str, contract: dict[str, Any]) -> list[str]:
    declared_docs, _ = documentation(skill, contract)
    known = known_names(skill, contract) | enum_values(skill, contract) | set(contract.get("doc_terms", []))
    unknown = sorted(documented_terms(declared_docs) - known)
    return [f"docs name fields the contract does not declare: {unknown}"] if unknown else []


def check_evals(skill: str, contract: dict[str, Any]) -> list[str]:
    errors = []
    fields, _ = vocabulary(skill, contract)
    statuses = set(contract.get("outputs", {}).get("status", {}).get("enum", []))
    for spec in contract.get("evals", []):
        passing = set(spec.get("pass", []))
        unknown_pass = passing - statuses
        if spec.get("status") and statuses and unknown_pass:
            errors.append(f"eval {spec['path']}: pass statuses {sorted(unknown_pass)} are not declared outputs")
        count = 0
        for name, case in eval_cases(skill, spec):
            count += 1
            problems = nonconforming(get_path(case, spec.get("input", "")), fields)
            if spec.get("errors"):
                errors_expected = get_path(case, spec["errors"])
                expected = "pass" if errors_expected == [] else "fail"
            else:
                expected = get_path(case, spec["status"]) if spec.get("status") else spec.get("expect")
            if not isinstance(expected, (str, int, bool, type(None))):
                expected = None
            if spec.get("status") and expected is not None and statuses and expected not in statuses:
                errors.append(f"{name}: expected status {expected!r} is not a declared output status")
            exempt = spec.get("exempt", {})
            if name.split("#", 1)[1] in exempt:
                if not problems:
                    errors.append(f"{name}: exempted from the contract but its input conforms; drop the exemption")
                continue
            if problems and spec.get("conform") == "always":
                errors.append(f"{name}: input breaks the contract (conform: always): {problems[:5]}")
            elif problems and expected in passing:
                errors.append(f"{name}: expects {expected!r} but its input breaks the contract: {problems[:5]}")
        if count == 0:
            errors.append(f"eval source {spec['path']} yielded no cases")
    return errors

CHECKS = (check_structure, check_scripts_covered, check_kernel_reads, check_declared_are_used,
          check_enums, check_docs_cover_contract, check_docs_within_contract, check_evals)


def check(skill: str) -> list[str]:
    path = SKILLS / skill / CONTRACT
    if not path.is_file():
        return [f"{skill}: ships scripts but has no {CONTRACT}"]
    contract = load_contract(skill)
    errors = check_structure(skill, contract)
    if errors:
        return [f"{skill}: {e}" for e in errors]
    out = []
    for fn in CHECKS[1:]:
        out += [f"{skill}: {e}" for e in fn(skill, contract)]
    return out


def module_enums(path: Path) -> dict[str, list[str]]:
    """Module-level constants that are collections of upper-case string literals."""
    found: dict[str, list[str]] = {}
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return found
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            value = node.value
            if isinstance(value, ast.Call) and value.args:
                value = value.args[0]
            if isinstance(value, (ast.Set, ast.Tuple, ast.List)) and value.elts and all(
                    isinstance(e, ast.Constant) and isinstance(e.value, str) for e in value.elts):
                found[node.targets[0].id] = sorted({e.value for e in value.elts})
    return found


def draft(skill: str) -> dict[str, Any]:
    """A starting contract: names the docs mention become fields, the rest internal.

    Every name still needs a decision: a payload key the docs never mention is
    usually a documentation gap, not an internal key.
    """
    base = SKILLS / skill
    scripts: dict[str, dict] = {}
    names: set[str] = set()
    candidates: dict[str, dict[str, list[str]]] = {}
    for path in script_files(skill):
        rel = str(path.relative_to(base))
        harness = path.name == "run_evals.py"
        scripts[rel] = {"input": "json", "role": "eval-harness" if harness else "kernel"}
        if not harness:
            names |= reads(path.read_text(encoding="utf-8"))
            if module_enums(path):
                candidates[rel] = module_enums(path)
    refs = base / "references"
    docs = sorted(str(p.relative_to(base)) for p in refs.glob("*.md")) if refs.is_dir() else []
    doc_text = "\n".join((base / d).read_text(encoding="utf-8") for d in docs)
    doc_text += (base / "SKILL.md").read_text(encoding="utf-8")
    return {
        "schema": SCHEMA,
        "docs": docs,
        "scripts": scripts,
        "fields": {n: {} for n in sorted(names) if word_in(n, doc_text)},
        "outputs": {"status": {}},
        "internal": sorted(n for n in names if not word_in(n, doc_text)),
        "doc_terms": [],
        "evals": [],
        "_candidate_enums": candidates,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true", help="check every skill that ships scripts")
    group.add_argument("--draft", metavar="SKILL", help="print a starting contract for SKILL")
    parser.add_argument("--skill", action="append", help="limit --check to these skills")
    args = parser.parse_args(argv)
    if args.draft:
        if args.draft not in unique_skills():
            parser.error(f"{args.draft} ships no scripts")
        print(json.dumps(draft(args.draft), indent=2, sort_keys=False))
        return 0
    errors = []
    for skill in args.skill or unique_skills():
        errors += check(skill)
    for error in errors:
        print(error)
    print(f"skill contracts: {len(args.skill or unique_skills())} skills, {len(errors)} problems")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
