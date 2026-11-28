# Prove it: comparisons before claims

This is a practitioner-facing experiment plan, **not** a published benchmark or evidence of competitive superiority. The current catalog is marked `EXPERIMENTAL / DEVELOPMENT`; task qualification remains unestablished. See [skill maturity](SKILL-MATURITY.md) and [real-host evaluations](REAL-HOST-EVALS.md).

## The narrow question

For a specified QA/repair task, does the exact `web-app-auditor` / `repair-operator` payload improve the probability of a **verified** outcome over the same host/model under a fair control?

A skill should not get credit for having more tools, access or attempts than its comparator.

## Frozen comparison

1. **A — `native`:** same host, model, tools and permissions; no CometWeb skill and no bundled helpers.
2. **B — `tools`:** the same, plus the skill's local scripts and formal JSON schemas, without its Markdown instructions. This separates the value of a script from the value of the written workflow.
3. **C — `skill`:** the same helper inventory as B, plus the skill's instructions and plugin registration.

If the skill ships no scripts that affect the outcome, A against C is enough. These labels match the runner's three-arm design in [REAL-HOST-EVALS.md](REAL-HOST-EVALS.md#three-arm-experiment-contract-v3-plan-execution-not-qualified).

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

Start with a small, disclosed diagnostic set. For a promotion decision, increase coverage across distinct tasks, host/model revisions and repetitions; **do not claim statistical certainty from ten similar prompts**. The following documented commands plan and preview a comparison without spending money.

Two arms (native against skill, the legacy `baseline`/`plugin` pair):

```bash
uv run python tooling/real_host_eval.py plan --out plan.json
uv run python tooling/real_host_eval.py run --plan plan.json --host claude \
  --out runs/claude-ab --condition both --max-tasks 20 --model <model-id>
```

All three arms (`native`, `tools`, `skill`) need a separate v3 plan:

```bash
uv run python tooling/real_host_eval.py plan --design three-arm \
  --skill web-app-auditor --per-skill 1 --negatives-per-skill 0 --out three-arm.json
uv run python tooling/real_host_eval.py run --plan three-arm.json --host claude \
  --out runs/three-arm --condition three-arm --max-tasks 3 --model <model-id>
```

The three-arm bundle is a bounded runtime subset of the package, not the whole installed skill, and that design is not yet qualified; read its contract before reporting a result from it.

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
