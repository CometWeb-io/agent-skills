# QA → repair → retest

A dependency-free example with synthetic plan data and one disposable browser
record. It demonstrates evidence collection and repair verification, not a
measured advantage of skills or production readiness.

Requires Node.js 22 or newer and Python 3 for local serving. Run inside the
directory containing this README and `policy.mjs`: `examples/qa-repair-retest`
in a checkout, or `qa-repair-retest` after extracting the standalone archive.

```bash
node --test policy.test.mjs
python3 -m http.server 8765 --bind 127.0.0.1
```

Open `http://127.0.0.1:8765` in a disposable browser session. Three sites with
four runs each choose `team`; annual billing shows a monthly equivalent of 46
and an annual charge of 550. Twenty-six sites have no fitting plan (`null`).

1. Establish the clean control: run the tests and exercise the UI.
2. In a disposable copy, deliberately replace `if (!plan) return null;` with
   `if (!plan) return { plan: 'portfolio', sites, runs };` in `policy.mjs`.
   This is an injected regression, not a known defect in an external product.
3. Reproduce the false recommendation at 26 sites and one run. Keep the failing
   test output and browser observation. Repair the cause in the disposable copy.
4. Rerun tests and the same browser interaction. Return to three sites, four
   runs and annual billing. Save that result, reload, click **Read**, compare
   its fields, then **Clear** and read again. A save
   message alone does not establish persistence. A page reload is not a browser
   process restart. Stop the local server when finished.

An agent can perform this job directly. If your host needs specialist
instructions, use only `web-app-auditor` and `repair-operator` as needed; follow
the existing [selective installation guide](https://github.com/CometWeb-io/agent-skills/blob/main/INSTALL.md). Neither package
provides a browser or permission to change a real service. Do not install a
second delivery channel merely to run this example.

Retain the source identity, environment, failure, patch, fresh test and browser
results, and remaining untested work. Compare the same workflow with the native
model before attributing improvements to a skill. Keep private run transcripts
and credentials outside this public example. No evidence here establishes a
production release verdict, backend storage, payment, accessibility conformance,
or effectiveness on another host or model.

The repository's `qa_example` gate runs these Node tests through the same
`check_all.py` runner locally and in CI. Node is installed explicitly in the
CI workflow. The gate checks the policy logic; browser interactions above
remain a separate check.

## Controlled write and recovery checks

From the repository root, using its existing Python dev environment:

```bash
uv run python -m pytest -q tooling/tests/test_qa_runtime.py
```

The stdlib `controlled_fixture.py` binds an ephemeral port on `127.0.0.1` and
creates SQLite under a fresh temporary directory. It serves only the three
allowlisted demo files and a bounded JSON record API. Test bearer tokens are
random per fixture; no account, CRM, provider or production database is used.
The original static/localStorage demo still works without this fixture.

The HTTP tests execute writes and reads, restart the server instance with the
same database, compare the exact record, test another principal's read/write/
delete denial, and verify cleanup. Separate worker processes exit before save,
after committed save and after the workflow checkpoint. Tests reuse the stable
record ID on retry and assert one stored row and one save completion. They use
the existing orchestrator ledger: an orphaned RUNNING attempt must be explicitly
failed before retry; completed steps are skipped; cancellation prevents resume
but requires explicit cleanup of an already committed record. Retry exhaustion
and changed plans stop dispatch. A conflicting payload returns 409; cleanup
leaves a test-only tombstone so a delayed retry cannot recreate the record.
The entire temporary database, including tombstones, is deleted on fixture exit.

For an actual browser reload check, point at an **already installed** Playwright
module; no browser or dependency is installed by this example:

```bash
QA_PLAYWRIGHT_MODULE=/absolute/path/to/playwright/index.mjs \
  uv run python -m pytest -q -s tooling/tests/test_qa_runtime.py
```

That optional test launches a fresh Chromium profile, exercises **Save → reload
→ Read**, checks a second principal's denial, then **Clear → reload → Read**,
reruns the original localStorage flow, and asserts a request to a different
loopback origin is intercepted and aborted. `browser_probe.mjs` receives test
tokens on stdin. A missing module configuration is an explicit pytest skip;
a configured module or browser that cannot launch fails. These Python runtime
checks run in the full pytest gate; the existing `qa_example` Node gate remains
a policy-logic check. The standalone static archive does not include the
repository ledger or pytest driver.

These are deterministic fixture checks, not host/model qualification, a skill
lift experiment, a production release verdict, or pilots on three independent
apps. Ledger completions are deliberately `RECEIPT_ONLY`; a content hash cannot
upgrade them into CW-AIP domain acceptance. The tests exercise the existing
ledger without changing its contracts.

**Isolation limit:** a private directory, bearer checks, loopback binding,
request-size/socket time limits and browser route filtering are application
controls. They do not restrict the Python/Node process's filesystem, operating
system network access, CPU or memory. The test explicitly shows that an owned
sentinel outside the fixture directory remains readable. Browser routing only
covers requests intercepted by that context. Server-instance restart is not a
server-process or machine restart; browser reload is not browser restart. This
fixture is not a system sandbox and must not be used with untrusted code,
credentials or user data. It does not complete the runtime sandbox milestone.
