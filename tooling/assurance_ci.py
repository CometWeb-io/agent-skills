#!/usr/bin/env python3
"""Compare pinned Git candidates and supplied review packets, without executing PR code."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

from audit_contracts import HEX40, MAX_FILE, MAX_JSON, array, local_path, loads, obj, require
from core.git import read_git
from review_skill_evals import compare, experiment_fingerprint

SCHEMA = "cometweb.assurance-ci/v1"
EVIDENCE_SCHEMA = "cometweb.assurance-ci-evidence/v1"
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")


def git(repo: Path, *args: str) -> bytes:
    return read_git(repo, *args).stdout


def tree(repo: Path, revision: str) -> dict:
    rows = git(repo, "ls-tree", "-rz", "--full-tree", revision, "--", "skills", "registry/skills.json")
    result = {}
    for row in rows.split(b"\0"):
        if not row:
            continue
        header, raw_path = row.split(b"\t", 1)
        mode, kind, oid = header.decode().split()
        path = local_path(raw_path.decode())
        result[path] = {"mode": mode, "kind": kind, "oid": oid}
    require(len(result) <= 20000, "candidate file budget exceeded")
    return result


def blob(repo: Path, inventory: dict, path: str) -> bytes:
    item = inventory.get(local_path(path))
    require(item is not None and item["kind"] == "blob" and item["mode"] in {"100644", "100755"},
            "required candidate file missing or not a regular Git blob")
    require(int(git(repo, "cat-file", "-s", item["oid"])) <= MAX_FILE, "candidate blob exceeds budget")
    return git(repo, "cat-file", "blob", item["oid"])


def catalog(repo: Path, inventory: dict) -> dict:
    data = loads(blob(repo, inventory, "registry/skills.json"))
    require(data.get("schema") == "cometweb.skills-registry/v1", "unsupported skill registry")
    rows = array(data.get("skills"), "skill registry")
    result = {}
    for row in rows:
        require(isinstance(row, dict) and isinstance(row.get("id"), str) and SLUG.fullmatch(row["id"]), "invalid registry skill")
        require(row["id"] not in result, "duplicate registry skill")
        require(isinstance(row.get("version"), str) and bool(row["version"].strip()), "missing skill version")
        result[row["id"]] = row
    return result


def instructions(repo: Path, inventory: dict, registry: dict, skill: str, resources: list) -> dict:
    if skill not in registry:
        return {}
    names = ["SKILL.md", *array(resources, "instruction resources")]
    require(len(set(names)) == len(names), "duplicate instruction resource")
    result = {local_path(name): blob(repo, inventory, f"skills/{skill}/{local_path(name)}").decode() for name in names}
    seen = {skill}
    while registry[skill].get("alias_of") is not None:
        target = registry[skill]["alias_of"]
        require(isinstance(target, str) and target in registry and target not in seen, "invalid or cyclic alias")
        seen.add(target)
        result[f"alias-of/{target}/SKILL.md"] = blob(repo, inventory, f"skills/{target}/SKILL.md").decode()
        skill = target
    return result


def validate_evidence(data: dict, identity: dict, changed: set[str], repo: Path,
                      inventories: dict, registries: dict) -> list[dict]:
    obj(data, {"schema", "candidate", "comparisons"}, set(), "CI evidence")
    require(data["schema"] == EVIDENCE_SCHEMA and data["candidate"] == identity, "evidence candidate identity mismatch")
    results, seen, response_ids, run_ids = [], set(), set(), set()
    for packet in array(data["comparisons"], "comparisons"):
        obj(packet, {"skill", "suite", "max_output_tokens", "experiment_sha256", "bundle"}, set(), "comparison packet")
        skill = packet["skill"]
        require(isinstance(skill, str) and skill in changed and skill not in seen, "unexpected or duplicate skill evidence")
        seen.add(skill)
        require(type(packet["max_output_tokens"]) is int and 1 <= packet["max_output_tokens"] <= 32000, "invalid output budget")
        suite = packet["suite"]
        obj(suite, {"schema", "cases"}, {"scope"}, "suite")
        require(suite["schema"] == "cometweb.model-evals/v1", "unsupported suite")
        cases = {}
        for case in array(suite.get("cases"), "suite cases", True):
            obj(case, {"id", "skill", "prompt", "fixture", "rubric"}, {"resources", "capabilities", "preserve_literals"}, "suite case")
            require(isinstance(case.get("id"), str) and case["id"] not in cases, "invalid or duplicate suite case")
            cases[case["id"]] = case
        bundle = packet["bundle"]
        result = compare(bundle, packet["experiment_sha256"])
        exp = bundle["experiment"]
        suite_bytes = (json.dumps(suite, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
        require(exp["suite_sha256"] == hashlib.sha256(suite_bytes).hexdigest(), "suite fingerprint mismatch")
        require({c["id"] for c in exp["cases"]} == {cid for cid, case in cases.items() if case["skill"] == skill}, "comparison omits suite cases for skill")
        for case_ref in exp["cases"]:
            case = cases.get(case_ref["id"])
            require(case is not None and case.get("skill") == skill, "comparison case/skill mismatch")
            require(isinstance(case.get("prompt"), str) and case["prompt"].strip() and isinstance(case.get("fixture"), dict), "missing case stimulus")
            caps = case.get("capabilities", {"tools": False})
            require(caps == exp["capabilities"], "suite capability mismatch")
            stimulus = {"prompt": case["prompt"], "fixture": case["fixture"], "capabilities": caps,
                        "max_output_tokens": packet["max_output_tokens"]}
            require(case_ref["fixture_sha256"] == experiment_fingerprint(stimulus), "case fingerprint mismatch")
            for condition in ("current", "candidate"):
                expected = instructions(repo, inventories[condition], registries[condition], skill, case.get("resources", []))
                require(exp["instruction_sha256"][condition] == experiment_fingerprint(expected), "candidate instruction fingerprint mismatch")
            if "case_rubrics" in exp:
                require(exp["case_rubrics"][case["id"]] == case.get("rubric"), "case rubric mismatch")
        for run in bundle["runs"]:
            require(run["id"] not in run_ids and run["response_id"] not in response_ids, "run or response identity reused across packets")
            run_ids.add(run["id"])
            response_ids.add(run["response_id"])
        results.append({"skill": skill, "comparison": result})
    return results


def assess(repo: Path, base: str, head: str, evidence: dict | None = None, require_evidence: bool = False) -> dict:
    require(isinstance(base, str) and HEX40.fullmatch(base) and isinstance(head, str) and HEX40.fullmatch(head), "base/head must be full commit SHAs")
    for revision in (base, head):
        require(git(repo, "cat-file", "-t", revision).strip() == b"commit", "candidate identity must name commits")
    bases = git(repo, "merge-base", "--all", base, head).decode().splitlines()
    require(len(bases) == 1, "missing or ambiguous merge base")
    ancestor = bases[0]
    identity = {"base_commit": base, "head_commit": head, "diff_base_commit": ancestor,
                "head_tree": git(repo, "rev-parse", f"{head}^{{tree}}").decode().strip()}
    identity["candidate_sha256"] = experiment_fingerprint(identity)
    inventories = {"current": tree(repo, base), "candidate": tree(repo, head)}
    require("skills" not in inventories["candidate"], "skills root must be a directory")
    registries = {key: catalog(repo, inventory) for key, inventory in inventories.items()}
    old = catalog(repo, tree(repo, ancestor))
    paths = [local_path(p.decode()) for p in git(repo, "diff", "--name-only", "--no-renames", "-z", ancestor, head).split(b"\0") if p]
    changed = {p.split("/")[1] for p in paths if p.startswith("skills/")}
    changed.update(s for s in old.keys() | registries["candidate"].keys() if old.get(s) != registries["candidate"].get(s))
    require(all(SLUG.fullmatch(s) for s in changed), "invalid changed package identifier")
    # Alias instructions include their canonical package even if the alias directory did not change.
    for _ in range(len(old) + len(registries["candidate"])):
        dependents = {s for rows in (old, registries["candidate"]) for s, row in rows.items() if row.get("alias_of") in changed}
        if dependents <= changed:
            break
        changed.update(dependents)
    packages, errors = [], []
    for skill in sorted(changed):
        prefix = f"skills/{skill}/"
        present = any(p.startswith(prefix) for p in inventories["candidate"])
        entry = registries["candidate"].get(skill)
        issues = []
        if prefix.rstrip("/") in inventories["candidate"]:
            issues.append("package_root_not_directory")
        if present != (entry is not None):
            issues.append("package_registry_membership_mismatch")
        if entry is not None:
            try:
                for name in ("SKILL.md", "VERSION", "LICENSE"):
                    require(bool(blob(repo, inventories["candidate"], prefix + name).strip()), "empty required package file")
                require(blob(repo, inventories["candidate"], prefix + "VERSION").decode().strip() == entry["version"], "registry/package version mismatch")
                require(all(item["mode"] in {"100644", "100755"} for p, item in inventories["candidate"].items() if p.startswith(prefix)), "non-regular package member")
            except ValueError:
                issues.append("required_package_files_invalid")
        packages.append({"skill": skill, "base_version": registries["current"].get(skill, {}).get("version"),
                         "head_version": entry.get("version") if entry else None, "status": "FAIL" if issues else "PASS", "issues": issues})
        errors.extend(issues)
    comparisons = validate_evidence(evidence, identity, changed, repo, inventories, registries) if evidence is not None else []
    covered = {r["skill"] for r in comparisons if r["comparison"]["comparison_status"] == "reviewed"}
    missing = sorted(changed - covered)
    evidence_status = "NOT_RUN" if not comparisons else "INCOMPLETE" if missing else "REVIEWED_SUPPLIED_RECORDS"
    return {"schema": SCHEMA, "candidate": identity, "changed_paths": paths, "packages": packages,
            "structural_checks": {"status": "FAIL" if errors else "PASS", "scope": "git_package_layout_registry_versions_only", "repository_gates": "NOT_RUN"},
            "comparison_evidence": {"status": evidence_status, "missing_skills": missing, "results": comparisons,
                                    "provenance": "supplied_records_not_authenticated_executions"},
            "task_outcome": "NOT_ASSESSED", "native_integration": "NOT_RUN", "release_authorization": "NOT_PROVIDED",
            "policy": {"require_evidence": require_evidence, "satisfied": not errors and (not require_evidence or (bool(comparisons) and not missing))}}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--require-evidence", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.evidence:
            with args.evidence.open("rb") as handle:
                evidence = loads(handle.read(MAX_JSON + 1))
        else:
            evidence = None
        result = assess(args.repo, args.base, args.head, evidence, args.require_evidence)
    except (OSError, ValueError, TypeError, KeyError, RecursionError, subprocess.SubprocessError):
        print(json.dumps({"schema": SCHEMA, "status": "INVALID", "task_outcome": "NOT_ASSESSED", "native_integration": "NOT_RUN"}))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return 0 if result["policy"]["satisfied"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
