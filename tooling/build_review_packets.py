#!/usr/bin/env python3
"""Bridge frozen runner requests/results into matched, initially unreviewed packets.

No model calls, generated grades or implicit promotion of recorded evidence.
"""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path

from audit_contracts import require
from review_skill_evals import CONDITIONS, compare, experiment_fingerprint

DIMENSIONS = ["correctness", "semantic-fidelity", "scope", "usefulness"]


def stable(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                   separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def build_packets(suite: dict, requests: dict, records: list[dict], repetitions: int = 1) -> list[dict]:
    from package_skill import canonical, digest
    from run_model_evals import validate_suite, validate_response
    validate_suite(suite)
    cases = {c["id"]: c for c in suite["cases"]}
    require(len(cases) == len(suite["cases"]), "duplicate suite cases")
    require(type(repetitions) is int and repetitions > 0, "invalid repetitions")
    expected = {(cid, r, condition) for cid in cases for r in range(repetitions) for condition in CONDITIONS}
    by_cell = {}
    for record in records:
        require(record.get("status") == "executed", "incomplete runs must not produce reviewed packets")
        cell = (record["case"], record["repeat"], record["condition"])
        require(cell in expected and cell not in by_cell, "unexpected or duplicate run cell")
        response = record["response"]
        validate_response(response)
        elapsed = record.get("elapsed_seconds")
        require(type(elapsed) in {int, float} and math.isfinite(elapsed) and elapsed >= 0,
                "elapsed time must be a finite nonnegative number, not a boolean")
        require(response.get("execution_kind") == "model" and response.get("status") == "completed", "mocks or unfinished responses are not model evidence")
        request = requests[(record["case"], record["condition"])]
        require(record["input_sha256"] == digest(canonical(request)), "frozen runner request mismatch")
        require(record["output_sha256"] == digest(response["output"].encode()), "runner output fingerprint mismatch")
        require(response["capabilities"] == request["capabilities"], "capability mismatch")
        by_cell[cell] = record
    require(by_cell.keys() == expected, "incomplete experimental cells")
    require(len({r["blind_id"] for r in records}) == len(records), "blind output ID reused")
    require(len({r["response"]["response_id"] for r in records}) == len(records), "response ID reused across cohorts")
    require(len({(r["response"]["host"], r["response"]["model"]) for r in records}) == 1,
            "cross-host/model records cannot be silently partitioned into a matched experiment")
    # Different resource bundles are separate cohorts, not silently averaged together.
    groups = {}
    for cid, case in cases.items():
        hashes = {condition: stable(requests[(cid, condition)]["instructions"]) for condition in CONDITIONS}
        cap = requests[(cid, "candidate")]["capabilities"]
        group_id = stable({"skill":case["skill"], "hashes":hashes, "capabilities":cap})
        groups.setdefault(group_id, {"ids":[], "hashes":hashes, "capabilities":cap})["ids"].append(cid)
    packets = []
    for group_id, group in groups.items():
        if group["hashes"]["current"] == group["hashes"]["candidate"]:
            packets.append({"id":group_id, "status":"no_instruction_change", "case_ids":group["ids"]})
            continue
        selected = [r for r in records if r["case"] in group["ids"]]
        identity = selected[0]["response"]
        fixtures = {}
        for cid in group["ids"]:
            fingerprints = {stable({k: requests[(cid, condition)][k] for k in ("prompt", "fixture", "capabilities", "max_output_tokens")}) for condition in CONDITIONS}
            require(len(fingerprints) == 1, "conditions received different task/budget/capabilities")
            fixtures[cid] = fingerprints.pop()
        exp = {"id":group_id, "suite_sha256":digest(canonical(suite)), "instruction_sha256":group["hashes"],
               "host":identity["host"], "model":identity["model"], "capabilities":group["capabilities"],
               "dimensions":DIMENSIONS, "cases":[{"id":cid,"fixture_sha256":fixtures[cid]} for cid in group["ids"]],
               "repetitions":repetitions,
               "case_rubrics":{cid:cases[cid]["rubric"] for cid in group["ids"]}}
        bundle = {"schema":"cometweb.skill-comparison/v1", "experiment":exp, "runs":[], "reviews":[]}
        templates, reviewer_tasks = [], []
        for record in selected:
            response, condition = record["response"], record["condition"]
            usage = response["usage"]
            tokens = usage.get("total_tokens")
            if tokens is None and all(type(usage.get(k)) is int for k in ("input_tokens", "output_tokens")):
                tokens = usage["input_tokens"] + usage["output_tokens"]
            bundle["runs"].append({"id":record["blind_id"], "case_id":record["case"], "repetition":record["repeat"],
                                   "condition":condition, "execution_kind":"model", "host":response["host"], "model":response["model"],
                                   "capabilities":response["capabilities"], "response_id":response["response_id"],
                                   "fixture_sha256":fixtures[record["case"]], "instructions_sha256":group["hashes"][condition],
                                   "output":response["output"], "output_sha256":record["output_sha256"],
                                   "tokens":tokens, "duration_ms":round(record["elapsed_seconds"]*1000)})
            case = cases[record["case"]]
            reviewer_tasks.append({"id":record["blind_id"], "case_id":record["case"],
                                   "prompt":case["prompt"], "fixture":case["fixture"], "rubric":case["rubric"],
                                   "output":response["output"], "output_sha256":record["output_sha256"]})
            templates.append({"run_id":record["blind_id"], "output_sha256":record["output_sha256"], "reviewer":None,
                              "review_kind":None, "scores":{d:None for d in DIMENSIONS},
                              "evidence":{d:"" for d in DIMENSIONS}, "flags":[]})
        # Validate identities/coverage now. Pending reviews must remain incomplete.
        require(compare(bundle)["comparison_status"] == "incomplete", "unexpected review completion")
        packets.append({"id":group_id, "status":"pending_reviews", "experiment_sha256":experiment_fingerprint(exp),
                        "bundle":bundle, "reviewer_tasks":reviewer_tasks, "review_template":{"schema":"cometweb.skill-reviews/v1","reviews":templates}})
    return packets


def write_packets(packets: list[dict], output: Path) -> list[dict]:
    from package_skill import canonical
    target = output / "comparison-packets"
    target.mkdir(exist_ok=False)
    inventory = []
    for packet in packets:
        item = {k:packet[k] for k in ("id","status")}
        if packet["status"] == "pending_reviews":
            directory = target / packet["id"]
            directory.mkdir()
            (directory/"comparison.json").write_bytes(canonical(packet["bundle"]))
            (directory/"review-template.json").write_bytes(canonical(packet["review_template"]))
            (directory/"experiment.sha256").write_text(packet["experiment_sha256"]+"\n")
            from reviewer_bundle import write_reviewer_zip
            reviewer_hash = write_reviewer_zip(directory/"reviewer.zip", packet["reviewer_tasks"], packet["review_template"])
            item.update(experiment_sha256=packet["experiment_sha256"], path=str(directory.relative_to(output)),
                        reviewer_archive=str((directory/"reviewer.zip").relative_to(output)),
                        reviewer_sha256=reviewer_hash, metadata_blinding="operator_fields_excluded")
        else:
            item["case_ids"] = packet["case_ids"]
        inventory.append(item)
    (target/"inventory.json").write_bytes(canonical(inventory))
    return inventory
