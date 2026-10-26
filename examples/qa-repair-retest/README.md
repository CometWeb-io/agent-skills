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
