#!/usr/bin/env python3
"""Real runner-based baseline/current/candidate comparisons, with explicit non-run and human-review states."""
from __future__ import annotations
import argparse
import datetime as dt
import json
import random
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from package_skill import ROOT, canonical, digest, safe_path, identifier
from public_safety import check_blob

CONDITIONS = ("no_skill", "current", "candidate")


def validate_suite(suite: dict) -> list[dict]:
    """Admit a bounded, explicit experiment before reading files or starting a runner."""
    if not isinstance(suite, dict) or suite.get("schema") != "cometweb.model-evals/v1":
        raise ValueError("invalid model suite")
    cases = suite.get("cases")
    if not isinstance(cases, list) or not 1 <= len(cases) <= 500:
        raise ValueError("empty or oversized model suite")
    seen = set()
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("case must be an object")
        for key in ("id", "skill", "prompt"):
            if not isinstance(case.get(key), str) or not case[key].strip():
                raise ValueError(f"case missing {key}")
        identifier(case["skill"])
        if case["id"] in seen or len(case["id"]) > 128 or not re.fullmatch(r"[a-z0-9-]+", case["id"]):
            raise ValueError("duplicate/unsafe case ID")
        if len(case["prompt"]) > 32000 or not isinstance(case.get("fixture"), dict):
            raise ValueError("bounded prompt and object fixture required")
        for field in ("rubric", "resources", "preserve_literals"):
            values = case.get(field, [] if field != "rubric" else None)
            if not isinstance(values, list) or len(values) > 100 or (field == "rubric" and not values):
                raise ValueError(f"{field} must be a bounded list")
            if any(not isinstance(v, str) or not v.strip() or len(v) > 4000 for v in values):
                raise ValueError(f"{field} entries must be nonempty bounded text")
            if len(values) != len(set(values)):
                raise ValueError(f"duplicate {field} entry")
        for resource in case.get("resources", []):
            if (resource.startswith("/") or "\\" in resource or ":" in resource
                    or any(p in {"", ".", ".."} for p in resource.split("/"))):
                raise ValueError("resource must be a relative path within the skill")
        caps = case.get("capabilities", {"tools": False})
        if not isinstance(caps, dict) or type(caps.get("tools")) is not bool:
            raise ValueError("explicit boolean tool capability required")
        if len(canonical(case)) > 256000:
            raise ValueError("case input exceeds budget")
        seen.add(case["id"])
    return cases


def instructions(root: Path, case: dict) -> dict:
    base = safe_path(root, "skills/" + case["skill"])
    names = ["SKILL.md", *case.get("resources", [])]
    if len(names) != len(set(names)):
        raise ValueError("duplicate instruction resource")
    result = {}
    for name in names:
        path = safe_path(base, name)
        text = path.read_text(encoding="utf-8")
        if check_blob(name, text.encode(), public=False):
            raise ValueError("potential credential in outbound instructions")
        result[name] = text
    return result


def prepare(case: dict, condition: str, current: Path, candidate: Path, max_output_tokens: int) -> dict:
    if condition not in CONDITIONS:
        raise ValueError("unknown eval condition")
    bundle = {} if condition == "no_skill" else instructions(current if condition == "current" else candidate, case)
    request = {"schema":"cometweb.eval-request/v1", "prompt":case["prompt"], "fixture":case["fixture"],
               "instructions":bundle, "capabilities":case.get("capabilities", {"tools":False}), "max_output_tokens":max_output_tokens,
               "scope":"loaded_instructions_text_only"}
    if len(canonical(request)) > 256000:
        raise ValueError("input budget exceeded; narrow the declared resources, do not silently truncate")
    if check_blob("request.json", canonical(request), public=False):
        raise ValueError("potential credential in outbound fixture")
    return request


def validate_response(response: dict, *, allow_mock: bool = False) -> None:
    if not isinstance(response, dict):
        raise ValueError("runner response must be an object")
    if response.get("schema") != "cometweb.eval-response/v1" or response.get("status") != "completed":
        raise ValueError("runner did not return a completed response")
    for key in ("output", "model", "host", "response_id"):
        if not isinstance(response.get(key), str) or not response[key].strip():
            raise ValueError(f"runner response missing {key}")
    if response.get("execution_kind") != "model" and not (allow_mock and response.get("execution_kind") == "mock"):
        raise ValueError("mock or unclassified execution cannot count as a model run")
    if response.get("execution_kind") == "mock" and not allow_mock:
        raise ValueError("mock output is not runtime acceptance")
    usage = response.get("usage")
    if not isinstance(usage, dict) or any(type(value) is not int or value < 0 for value in usage.values()):
        raise ValueError("usage values must be non-negative integers, not fabricated null-to-zero metrics")
    if all(k in usage for k in ("input_tokens", "output_tokens", "total_tokens")):
        if usage["total_tokens"] != usage["input_tokens"] + usage["output_tokens"]:
            raise ValueError("inconsistent total token usage")
    if not isinstance(response.get("tool_trace"), list) or not isinstance(response.get("capabilities"), dict):
        raise ValueError("runner must declare capabilities and actual tool trace")
    if type(response["capabilities"].get("tools")) is not bool:
        raise ValueError("runner tool capability must be boolean")
    if response["capabilities"].get("tools") is False and response["tool_trace"]:
        raise ValueError("text-only execution cannot report tool calls")


def execute(request: dict, command: list[str], timeout: int, *, allow_mock: bool = False) -> tuple[dict, float]:
    if not command or not all(isinstance(x, str) and x for x in command):
        raise ValueError("runner command must be a nonempty argv list")
    start = time.monotonic()
    # New process and CWD per run provide context separation, NOT an operating-system sandbox.
    with tempfile.TemporaryDirectory(prefix="cw-eval-run-") as cwd:
        proc = subprocess.run(command, input=canonical(request), capture_output=True, cwd=cwd, timeout=timeout, check=True)
    if len(proc.stdout) > 4 * 1024 * 1024:
        raise ValueError("runner output exceeds bounded record size")
    response = json.loads(proc.stdout)
    validate_response(response, allow_mock=allow_mock)
    if response["capabilities"] != request["capabilities"]:
        raise ValueError("runner capabilities differ from the matched experiment contract")
    return response, time.monotonic() - start


def run(suite: dict, current: Path, candidate: Path, command: list[str], output: Path, *, repeat: int = 1, max_runs: int = 48, timeout: int = 120, max_output_tokens: int = 2048, seed: int = 1) -> dict:
    cases = validate_suite(suite)
    if type(repeat) is not int or repeat < 1 or len(cases) * len(CONDITIONS) * repeat > max_runs:
        raise ValueError("run budget exceeded or invalid repetition count")
    if not 128 <= max_output_tokens <= 8192 or not 1 <= timeout <= 600:
        raise ValueError("output/timeout budget outside permitted range")
    requests = {(c["id"], k):prepare(c, k, current, candidate, max_output_tokens) for c in cases for k in CONDITIONS}
    if all(requests[(c["id"], "current")]["instructions"] == requests[(c["id"], "candidate")]["instructions"] for c in cases):
        raise ValueError("current and candidate instruction bundles are identical; no improvement experiment exists")
    jobs = [(c, k, r) for c in cases for r in range(repeat) for k in CONDITIONS]
    random.Random(seed).shuffle(jobs)
    output.mkdir(parents=True, exist_ok=False)
    (output / "blind").mkdir()
    records, mapping = [], {}
    manifest = {"schema":"cometweb.model-eval-run/v1", "started_at":dt.datetime.now(dt.timezone.utc).isoformat(), "suite_sha256":digest(canonical(suite)),
                "conditions":list(CONDITIONS), "planned_runs":len(jobs), "seed":seed, "runner_argv":command,
                "provenance":"runner_reported_not_cryptographic_attestation", "quality_verdict":"pending_human_review"}
    (output / "manifest.json").write_bytes(canonical(manifest))
    for index, (case, condition, repetition) in enumerate(jobs):
        request = requests[(case["id"], condition)]
        blind_id = f"output-{index+1:04d}"
        record = {"case":case["id"], "condition":condition, "repeat":repetition, "input_sha256":digest(canonical(request)), "blind_id":blind_id}
        try:
            response, elapsed = execute(request, command, timeout)
            checks = [{"assertion":text, "passed":text in response["output"]} for text in case.get("preserve_literals", [])]
            record.update(status="executed", response=response, elapsed_seconds=elapsed, output_sha256=digest(response["output"].encode()), machine_checks=checks, human_review="pending")
            (output / "blind" / (blind_id + ".json")).write_bytes(canonical({"id":blind_id, "prompt":case["prompt"], "fixture":case["fixture"], "rubric":case["rubric"], "output":response["output"]}))
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            record.update(status="error", error_type=type(exc).__name__, human_review="not_applicable")
        records.append(record)
        mapping[blind_id] = {"case":case["id"], "condition":condition, "repeat":repetition}
        (output / "records.json").write_bytes(canonical(records))
        (output / "unblinding.json").write_bytes(canonical(mapping))
        # Fail fast prevents repeated cost after auth/network/model failure; partial evidence is retained.
        if record["status"] == "error":
            break
    models = sorted({r["response"]["model"] for r in records if r["status"] == "executed"})
    hosts = sorted({r["response"]["host"] for r in records if r["status"] == "executed"})
    result = {**manifest, "finished_at":dt.datetime.now(dt.timezone.utc).isoformat(), "completed_runs":sum(r["status"] == "executed" for r in records),
              "errors":sum(r["status"] == "error" for r in records), "model_ids":models, "host_ids":hosts,
              "comparison_status":"unreviewed" if len(models) == len(hosts) == 1 and len(records) == len(jobs) and all(r["status"] == "executed" for r in records) else "incomplete_or_unmatched",
              "quality_verdict":"pending_human_review", "runtime_installation_acceptance":"not_assessed"}
    (output / "summary.json").write_bytes(canonical(result))
    if result["comparison_status"] == "unreviewed":
        try:
            from build_review_packets import build_packets, write_packets
            packets = build_packets(suite, requests, records, repeat)
            result["review_packets"] = write_packets(packets, output)
        except (OSError, ValueError, TypeError, KeyError) as exc:
            result["review_packets"] = {"status":"error", "error_type":type(exc).__name__}
            result["comparison_status"] = "review_packet_export_failed"
        (output / "summary.json").write_bytes(canonical(result))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", type=Path, default=ROOT / "evals/model/suite.json")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--current-root", type=Path)
    parser.add_argument("--candidate-root", type=Path)
    parser.add_argument("--runner-json", help="JSON argv for a trusted runner; shell syntax is not evaluated")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--max-runs", type=int, default=48)
    parser.add_argument("--max-output-tokens", type=int, default=2048)
    args = parser.parse_args()
    suite = json.loads(args.suite.read_text())
    cases = validate_suite(suite)
    if not args.execute:
        print(json.dumps({"status":"not_run", "case_count":len(cases), "planned_conditions":list(CONDITIONS), "model_calls":0, "reason":"Explicit --execute, frozen roots and a configured runner are required"}, indent=2))
        return 0
    if not all((args.current_root, args.candidate_root, args.runner_json, args.output)):
        parser.error("--execute requires current/candidate roots, runner-json and a new output directory")
    result = run(suite, args.current_root.resolve(), args.candidate_root.resolve(), json.loads(args.runner_json), args.output, repeat=args.repeat, max_runs=args.max_runs, max_output_tokens=args.max_output_tokens)
    print(json.dumps(result, indent=2))
    return int(result["comparison_status"] != "unreviewed")


if __name__ == "__main__":
    raise SystemExit(main())
