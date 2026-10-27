"""Real disposable HTTP/SQLite effects; no model, production or OS-sandbox claim."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4

import pytest

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "examples/qa-repair-retest"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


fixture_module = load("qa_controlled_fixture", EXAMPLE / "controlled_fixture.py")
ledger = load("qa_workflow_ledger", ROOT / "skills/skill-orchestrator/scripts/workflow_ledger.py")
QUOTE = {"plan": "team", "sites": 3, "runs": 12, "displayedMonthly": 46, "annualTotal": 550}


def request(fixture, method, record, owner="owner", value=None, raw=None):
    headers = {} if owner is None else {"Authorization": f"Bearer {fixture.token(owner)}"}
    data = raw if raw is not None else json.dumps(value).encode() if method == "PUT" else None
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = Request(f"{fixture.url}/records/{record}", data=data, headers=headers, method=method)
    try:
        response = urlopen(req, timeout=5)
    except HTTPError as error:
        response = error
    with response:
        return response.status, json.load(response)


def rows(fixture):
    with fixture.connect() as db:
        return db.execute("SELECT COUNT(*), SUM(CASE WHEN deleted = 0 THEN 1 ELSE 0 END) FROM records").fetchone()


def checkpoint(run, step, attempt, observation):
    ledger.complete_step(run, step, f"{run.name}-{step}", ledger.sha256(ledger.canonical(observation)), attempt)


# Kill a separate worker process at the application-write/checkpoint boundary.
WORKER = '''
import importlib.util, json, os, sys
from pathlib import Path
from urllib.request import Request, urlopen
config=json.load(sys.stdin)
spec=importlib.util.spec_from_file_location("worker_ledger",config["ledger"])
ledger=importlib.util.module_from_spec(spec);spec.loader.exec_module(ledger)
if config["crash"]=="before-save": os._exit(71)
req=Request(config["url"]+"/records/"+config["record"],data=json.dumps(config["quote"]).encode(),method="PUT",
            headers={"Authorization":"Bearer "+config["token"],"Content-Type":"application/json"})
with urlopen(req,timeout=5) as response: result=json.load(response)
if config["crash"]=="after-save": os._exit(72)
ledger.complete_step(Path(config["run"]),"save",config["record"],ledger.sha256(ledger.canonical(result)),config["attempt"])
if config["crash"]=="after-checkpoint": os._exit(73)
'''


@pytest.mark.parametrize("crash,exit_code", [("before-save", 71), ("after-save", 72), ("after-checkpoint", 73)])
def test_crash_retry_resume_without_duplicate_write(tmp_path, crash, exit_code):
    with fixture_module.disposable_fixture() as fixture:
        record = uuid4().hex
        plan = {"execution_mode": "single_thread", "record_id": record,
                "fixture_hash": ledger.sha256((EXAMPLE / "controlled_fixture.py").read_bytes()),
                "steps": [{"step_id": name, "skill": "web-app-auditor", "retry_limit": 2}
                          for name in ("save", "read", "boundary", "cleanup")]}
        run = ledger.create_run(tmp_path / "runs", record, plan)
        attempt = ledger.claim_next(run, plan)["data"]["attempt_id"]
        config = {"ledger": str(ROOT / "skills/skill-orchestrator/scripts/workflow_ledger.py"),
                  "url": fixture.url, "token": fixture.token(), "record": record, "quote": QUOTE,
                  "run": str(run), "attempt": attempt, "crash": crash}
        result = subprocess.run([sys.executable, "-c", WORKER], input=json.dumps(config),
                                text=True, capture_output=True, timeout=20)
        assert result.returncode == exit_code, result.stderr
        assert rows(fixture)[0] == (0 if crash == "before-save" else 1)
        if crash != "after-checkpoint":
            with pytest.raises(ValueError, match="orphaned running"):
                ledger.claim_next(run, plan)
            ledger.fail_step(run, "save", "worker exited before checkpoint", attempt)
            retry = ledger.claim_next(run, plan)
            assert retry["data"]["attempt_number"] == 2
            config.update(attempt=retry["data"]["attempt_id"], crash=None)
            retried = subprocess.run([sys.executable, "-c", WORKER], input=json.dumps(config),
                                     text=True, capture_output=True, timeout=20)
            assert retried.returncode == 0, retried.stderr
        # A fresh server/SQLite connection reopens the exact key after worker death.
        fixture.stop()
        fixture.start()
        read = ledger.claim_next(run, plan)
        assert read["data"]["step_id"] == "read"
        assert rows(fixture) == (1, 1)
        observation = request(fixture, "GET", record)
        assert observation == (200, {"id": record, "quote": QUOTE})
        checkpoint(run, "read", read["data"]["attempt_id"], observation)
        boundary = ledger.claim_next(run, plan)
        denied = [request(fixture, method, record, "other")[0] for method in ("GET", "DELETE", "PUT")]
        assert denied == [404, 404, 404]
        assert request(fixture, "GET", record)[1]["quote"] == QUOTE
        checkpoint(run, "boundary", boundary["data"]["attempt_id"], denied)
        cleanup = ledger.claim_next(run, plan)
        assert request(fixture, "DELETE", record)[0] == 200
        assert request(fixture, "GET", record)[0] == 404
        assert rows(fixture) == (1, 0)
        checkpoint(run, "cleanup", cleanup["data"]["attempt_id"], {"record": record, "read_status": 404})
        assert ledger.claim_next(run, plan)["status"] == "COMPLETED"
        events = [json.loads(line) for line in (run / "events.jsonl").read_text().splitlines()]
        assert sum(e["event_type"] == "step_completed" and e["data"]["step_id"] == "save" for e in events) == 1
        assert ledger.replay(run)["steps"]["save"]["completion_class"] == "RECEIPT_ONLY"
        database = fixture.database
    assert not database.exists()  # Including idempotency tombstones.


def test_conflicts_validation_auth_and_cleanup_tombstone():
    with fixture_module.disposable_fixture() as fixture:
        record = uuid4().hex
        assert request(fixture, "PUT", record, None, QUOTE)[0] == 401
        for raw in (b"not-json", b"{}", b"{\"plan\":true}", b"x" * 2049,
                    json.dumps({**QUOTE, "sites": True}).encode(),
                    json.dumps({**QUOTE, "extra": "unexpected"}).encode()):
            assert request(fixture, "PUT", record, raw=raw)[0] == 400
        assert rows(fixture)[0] == 0
        assert request(fixture, "PUT", record, value=QUOTE)[0] == 201
        assert request(fixture, "PUT", record, value=dict(reversed(list(QUOTE.items()))))[0] == 200
        assert request(fixture, "PUT", record, value={**QUOTE, "sites": 4})[0] == 409
        assert request(fixture, "GET", "../../outside")[0] == 404
        assert request(fixture, "GET", record, None)[0] == 401
        assert request(fixture, "PUT", record, "other", QUOTE)[0] == 404
        assert request(fixture, "DELETE", record)[0] == 200
        assert request(fixture, "DELETE", record)[0] == 404
        assert request(fixture, "PUT", record, value=QUOTE)[0] == 410
        assert request(fixture, "GET", record)[0] == 404
        assert rows(fixture) == (1, 0)


def test_concurrent_retries_create_one_row_and_null_round_trips():
    with fixture_module.disposable_fixture() as fixture:
        record = uuid4().hex
        with ThreadPoolExecutor(max_workers=6) as pool:
            statuses = list(pool.map(lambda _: request(fixture, "PUT", record, value=QUOTE)[0], range(6)))
        assert sorted(statuses) == [200, 200, 200, 200, 200, 201]
        assert rows(fixture) == (1, 1)
        assert request(fixture, "DELETE", record)[0] == 200
        null_record = uuid4().hex
        assert request(fixture, "PUT", null_record, value=None)[0] == 201
        assert request(fixture, "GET", null_record) == (200, {"id": null_record, "quote": None})
        assert request(fixture, "DELETE", null_record)[0] == 200
        assert rows(fixture) == (2, 0)


def test_cancel_stops_resume_and_requires_explicit_test_data_cleanup(tmp_path):
    with fixture_module.disposable_fixture() as fixture:
        record = uuid4().hex
        plan = {"steps": [{"step_id": "save", "skill": "web-app-auditor"}]}
        run = ledger.create_run(tmp_path / "runs", record, plan)
        ledger.claim_next(run, plan)
        assert request(fixture, "PUT", record, value=QUOTE)[0] == 201
        ledger.cancel_run(run, "operator cancelled disposable run")
        before = (run / "events.jsonl").read_bytes()
        assert ledger.claim_next(run, plan)["status"] == "CANCELLED"
        assert (run / "events.jsonl").read_bytes() == before
        # Cancellation cannot roll back a committed external effect.
        assert request(fixture, "GET", record)[0] == 200
        assert request(fixture, "DELETE", record)[0] == 200
        assert request(fixture, "GET", record)[0] == 404


def test_retry_exhaustion_and_stale_plan_do_not_dispatch_a_write(tmp_path):
    plan = {"steps": [{"step_id": "save", "skill": "web-app-auditor", "retry_limit": 1}]}
    run = ledger.create_run(tmp_path / "runs", "bounded", plan)
    claim = ledger.claim_next(run, plan)
    ledger.fail_step(run, "save", "injected failure", claim["data"]["attempt_id"])
    assert ledger.claim_next(run, plan)["status"] == "BLOCKED"
    with pytest.raises(ValueError, match="blocked"):
        ledger.claim_next(run, plan)
    stale = ledger.create_run(tmp_path / "runs", "stale", plan)
    assert ledger.claim_next(stale, {**plan, "goal": "changed"})["status"] == "STALE_PLAN"
    with pytest.raises(ValueError, match="stale plan"):
        ledger.claim_next(stale, plan)


def test_fixture_directory_is_not_a_system_sandbox(tmp_path):
    sentinel = tmp_path / "disposable-outside-sentinel"
    sentinel.write_text("synthetic outside data")
    with fixture_module.disposable_fixture() as fixture:
        assert fixture.database.parent != sentinel.parent
        assert sentinel.read_text() == "synthetic outside data"
        assert fixture.server.server_address[0] == "127.0.0.1"


@pytest.mark.skipif(not os.environ.get("QA_PLAYWRIGHT_MODULE"), reason="Optional existing Playwright module required; no browser evidence without execution")
def test_browser_save_reload_read_access_boundary_cleanup():
    with fixture_module.disposable_fixture() as fixture:
        record = uuid4().hex
        result = subprocess.run(["node", str(EXAMPLE / "browser_probe.mjs")],
                                input=json.dumps({"url": fixture.url, "token": fixture.token(),
                                                  "otherToken": fixture.token("other"), "record": record}),
                                text=True, capture_output=True, timeout=45)
        assert result.returncode == 0, result.stderr
        receipt = json.loads(result.stdout)
        assert receipt["save_reload_read"] is True
        assert receipt["cleanup_reload_read"] is True
        assert receipt["other_principal_read_delete"] == [404, 404]
        assert receipt["blocked_context_requests"] == 1
        assert receipt["local_storage_control"] is True
        assert rows(fixture) == (1, 0)
        print(json.dumps(receipt, sort_keys=True))
