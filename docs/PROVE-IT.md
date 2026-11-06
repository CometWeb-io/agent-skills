# Prove it: comparisons before claims

This is a practitioner-facing experiment plan, **not** a published benchmark or evidence of competitive superiority. The current catalog is marked `EXPERIMENTAL / DEVELOPMENT`; task qualification remains unestablished. See [skill maturity](SKILL-MATURITY.md) and [real-host evaluations](REAL-HOST-EVALS.md).

## The narrow question

For a specified QA/repair task, does the exact `web-app-auditor` / `repair-operator` payload improve the probability of a **verified** outcome over the same host/model under a fair control?

A skill should not get credit for having more tools, access or attempts than its comparator.

## Frozen comparison

1. **A — Native host/model:** same task, no CometWeb skills, same available tools and permissions.
2. **B — Same tools plus skill:** same host/model/configuration, plus the pinned skill package.
3. **C — Tool-matched control (when scripts affect the outcome):** native instructions with equivalent permitted deterministic tools, without the workflow instructions. This separates the value of a script from the value of prose instructions.

Before the first model call, record: a clean commit SHA for each payload, host and model IDs, date, permissions, available tools, task fixtures, scoring rubric, resource caps, retries, exclusion rules and any held-out tasks. Do not tune skills against the held-out set.

## Outcome measures

| Outcome | Definition |
| --- | --- |
| Verified task success | Reproduction and repair satisfy the predeclared acceptance checks, including fresh post-repair evidence |
| False-completion rate | The agent declares success despite a failing or missing required check |
| Regressions | A known-good control is damaged or irrelevant files are changed |
| Human intervention | Number and severity of corrections before acceptance |
| Cost and latency | Reported tokens, provider cost (when available), and elapsed time; missing values stay unknown |
| Scope compliance | No unauthorized side effects or unacknowledged untested paths |

Use a blinded review of raw outputs against a frozen rubric and independently checked ground truth. A correct JSON schema, a green CI badge and a synthetic demo are not substitutes for task success. Report adverse cases rather than only the best samples.

## Minimal feasible run

Start with a small, disclosed diagnostic set. For a promotion decision, increase coverage across distinct tasks, host/model revisions and repetitions; **do not claim statistical certainty from ten similar prompts**. The following documented commands plan and preview a host comparison without spending money:

```bash
uv run python tooling/real_host_eval.py plan --out plan.json
uv run python tooling/real_host_eval.py run --plan plan.json --host claude \
  --out runs/claude-ab --condition both --max-tasks 20 --model <model-id>
```

The documented `--condition both` runner covers A/B, not the optional tool-matched C condition. C requires a separately frozen experiment with equivalent tool access; do not report it as run by this command.

Execution requires the explicit `--execute` flag, host credentials, compatible local tooling and a cost cap. See [REAL-HOST-EVALS.md](REAL-HOST-EVALS.md) before running it. Currently executable adapters cover Claude Code and Codex; do not claim real-host experiments for other hosts until recorded.

## Public scorecard template

For each released comparison, publish:

- Repository revision, skill version, full task definition and fixture provenance.
- Models, hosts, run dates, tools, permissions and per-condition resource caps.
- Number of tasks, successful runs, failed/blocked/missing runs and known-good controls.
- Paired outcome table; adverse cases; reviewers' conflicts and adjudication method.
- Raw reproducible evidence with private data redacted; complete instructions for replay.
- Exact sentence the results support, and at least one conclusion they **do not** support.

A useful result can be negative. If native-with-tools matches or beats the skill at the same cost, narrow the skill's intended use, simplify it or stop promoting that claim.
