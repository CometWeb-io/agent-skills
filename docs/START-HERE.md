# Start here: one QA task, not 33 skills

CometWeb Agent Skills are experimental `SKILL.md` packages for bounded workflows. The first workflow to try is **reproduce → repair → retest** on a disposable, synthetic web app. You do not need to install all 33 skills to evaluate it.

**What you should get:** a record of the observed defect, a scoped change, fresh checks after the change, and an honest list of anything not tested. A passing package test or a completed demo is **not** evidence that the skill improves real-agent task success.

## 1. Run the no-agent control first

Prerequisites: Node.js 22+ and Python 3, locally. Review the [demo instructions](../examples/qa-repair-retest/README.md) and the files you will execute first. The demo contains synthetic plan data, not credentials or real customer records.

From the repository root:

```bash
cd examples/qa-repair-retest
node --test policy.test.mjs
python3 -m http.server 8765 --bind 127.0.0.1
```

In another browser, visit `http://127.0.0.1:8765`. Check the plan recommendation, save, reload, read it back and clear it. Stop the server afterward. Browser interaction is a **manual step** unless you separately configure a browser-capable host.

This establishes a known-good control, not a benchmark result.

## 2. Reproduce a defect in a disposable copy

Follow the exact regression injection in the [QA → repair → retest example](../examples/qa-repair-retest/README.md): in a **disposable copy**, change `if (!plan) return null;` to return a fictitious `portfolio` plan. The incorrect recommendation should appear for 26 sites and one run. Record a failing test and observed UI behavior **before** repairing it. Never perform this exercise against a real service or production data.

## 3. Use one skill when it adds something

Choose the installer for your host. The installers are local scripts, not a remotely hosted agent service. Review them before running.

```bash
# From the repository root; choose ONE host:
./scripts/install-claude.sh --skill web-app-auditor
# OR
./scripts/install-codex.sh --skill web-app-auditor
# OR
./scripts/install-cursor.sh --skill web-app-auditor
```

Use `--dry-run` first if you want to preview changes. Keep your clone in place because installation uses symlinks. To use the specialist repair contract, install `repair-operator` separately via the same host's script and `--skill repair-operator`. Details and uninstall instructions are in [INSTALL.md](../INSTALL.md). These examples do **not** establish live compatibility on every host or model.

Use a prompt like this in a host with the required file and browser access:

> Inspect the disposable QA demo. Reproduce the wrong recommendation at 26 sites and one run, record the failing check, repair only the local copy, rerun the same tests and browser interaction, then verify save → reload → read → clear. Report exactly what you observed and what remains untested. Do not touch other projects or external services.

The host decides what tools it can actually use. Skills provide instructions and validation resources; they do not grant browser access, permission to modify files, or a guarantee of a correct result. Approve writes only to your disposable copy.

## 4. Decide whether the skill was worth using

Compare the same task against the **same model and tools without the skill**. Capture the task success, unsupported completion claims, rework, time and usage cost. The full procedure is in [PROVE-IT.md](PROVE-IT.md).

If the native model succeeds as reliably with less cost, **prefer the native model**. A CometWeb skill should only be retained for a demonstrated benefit in a specified task and host.

For a bounded external pilot and a private feedback template, see [USER-PILOT.md](USER-PILOT.md). Do not share credentials, customer data, full private chat histories or unreviewed model transcripts in public issues.
