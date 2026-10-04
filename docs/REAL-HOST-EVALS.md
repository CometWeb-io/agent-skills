# Real-host evals

Everything CI runs is offline. Routing evals score a lexical ranker, kernel tests
score the scripts, and `tooling/grade_output.py` scores golden reports someone
wrote by hand. None of it shows what a real host does when a user types a prompt
with the plugin installed: whether the right skill loads, and whether the answer
meets the skill's contract. `tooling/real_host_eval.py` measures that, on your
machine, with your credentials, when you choose to spend the money.

It never starts a host unless you pass `--execute`. Without it, `run` prints
every command it would start, the exact prompt each one receives, and an
estimated cost.

```bash
uv run python tooling/real_host_eval.py plan --out plan.json                     # 1. pick tasks
uv run python tooling/real_host_eval.py run --plan plan.json --host claude \
    --out runs/claude-ab --condition both --max-tasks 20 --model <model-id>      # 2. dry run: read it
uv run python tooling/real_host_eval.py run --plan plan.json --host claude \
    --out runs/claude-ab --condition both --max-tasks 20 --model <model-id> \
    --max-total-usd 5 --execute                                                  # 3. spend
uv run python tooling/real_host_eval.py grade runs/claude-ab                     # 4. offline
uv run python tooling/real_host_eval.py report runs/claude-ab --out scorecard.md # 5. offline
```

`plan`, `grade` and `report` make no network calls and cost nothing. Only step 3
does.

Runtime capabilities are declared in `registry/runtime-hosts.json`. The current
executable adapters are Claude Code and Codex. Cursor, ChatGPT, Qwen Code,
Qoder, Lingma, and Alibaba Skills Portal are explicit `NOT_RUN` profiles until
their headless/plugin adapters exist. Missing credentials and unsupported hosts
materialize terminal records with a reason; they never become passes or
silently invoke a host.

## 1. Plan

`plan` selects tasks per skill from cases the repository already holds:

| Source | Becomes | Checked by |
| --- | --- | --- |
| `evals/model/suite.json`, `evals/model/continuation-cases.json` | a task with the case's prompt and fixture material | output |
| positive cases in `evals/routing/suite.json` and `adversarial-suite.json` | a task with the user prompt alone | routing, and output when the skill is graded |
| cases in those suites that list the skill in `must_not_trigger` | a negative task | routing |

A task is graded on output when its skill has a rubric under `evals/output/`
(the golden-backed contract described in [OUTPUT-GRADING.md](OUTPUT-GRADING.md)),
or when its case pins literals the answer must preserve. Model cases that carry
fixture material are taken first, because a bare routing prompt gives the host
nothing to work on and many skills will rightly answer with questions; those
tasks still measure routing, and their output rate shows how often the skill
produces its contract from a one-line request.

`evals/routing/holdout.json` is never read. `read_json` refuses it by path, and
the plan lists it under `excluded_sources`. The holdout belongs to
`tooling/routing_holdout.py`; feeding it to anything else turns it into a tuning
set.

| Option | Effect |
| --- | --- |
| `--per-skill N` | positive tasks per skill (default 3) |
| `--negatives-per-skill N` | negative routing tasks per skill (default 1) |
| `--skill ID` | limit to one skill; repeatable |
| `--lang en\|pl` | keep one language |
| `--seed N` | which cases are drawn; the same seed gives the same plan |
| `--canary` | plant a fresh canary instruction in every output task's material |

The plan records the SHA-256 of every source file and of itself. `run` refuses a
plan edited after it was written, so a scorecard always names the exact tasks.

With `--canary`, each output task's material gets an instruction asking the
reader to print a token built from two parts. Only the parts are in the prompt;
`grade` fails the output with `INJECTION_FOLLOWED` if the joined token appears.
See [OUTPUT-GRADING.md](OUTPUT-GRADING.md#canary-files).

## 2. Run

`run` builds one command per task, condition and repeat:

| Host | Command | Plugin condition | Native caps |
| --- | --- | --- | --- |
| `claude` | `claude -p --output-format stream-json --verbose --no-session-persistence --strict-mcp-config --tools Read,Glob,Grep,Skill --allowedTools Read,Glob,Grep,Skill --max-turns N --max-budget-usd X` | adds `--plugin-dir <stage>` | turns and dollars per run |
| `codex` | `codex exec --json --skip-git-repo-check --sandbox read-only --output-last-message <file> -` | first runs `codex plugin marketplace add <stage>` and `codex plugin add cometweb-agent-skills@cometweb-agent-skills` | none; only `--timeout` |

The prompt goes on stdin. `--model` pins the model for either host.

**Isolation.** Each run gets a new temporary directory holding its own HOME, its
own host config directory (`CLAUDE_CONFIG_DIR` or `CODEX_HOME`) and an empty
working directory, removed when the run ends. Your settings, other plugins, MCP
servers, memory and project instruction files are not visible to the host. The
plugin is staged once per run directory from this checkout, the same payload
`tooling/host_smoke.py` installs, and its digest goes into `manifest.json`. The
tool set is read-only. This is separation, not an operating-system sandbox.

**Credentials.** Only `PATH`, the temporary paths, a few locale variables and
the host's credential variables are passed: `ANTHROPIC_API_KEY` or
`CLAUDE_CODE_OAUTH_TOKEN` for `claude`, `OPENAI_API_KEY` or `CODEX_API_KEY` for
`codex`. Because HOME is fresh, a login stored in your normal config or keychain
is not seen; export one of those variables for the session instead. Values are
never written to the run directory; `record.json` lists the variable names only.

**Caps.**

| Option | Default | Effect |
| --- | --- | --- |
| `--max-tasks N` | 10 | hard cap on host runs (task x condition x repeat), at most 500 |
| `--timeout S` | 300 | a run is killed after S seconds and recorded as `timeout` |
| `--max-turns N` | 8 | `claude` only |
| `--max-usd-per-task X` | 0.5 | `claude` only; passed as `--max-budget-usd` |
| `--max-total-usd X` | none | stop before a run that could take the total past X |
| `--max-total-tokens N` | none | stop once reported tokens reach N |
| `--max-consecutive-errors N` | 2 | stop after N failed runs in a row, such as a missing credential |

For `claude`, a run whose cost was not reported is counted at its per-run cap,
never at zero, so `--max-total-usd` is a real ceiling. `codex` reports tokens
but not dollars: `--max-total-usd` then needs `--price-in` and `--price-out` (USD
per million tokens) and is checked between runs, so the last run can overshoot
it by its own cost.

**The estimate.** The dry run's token figure is bytes/4 over the prompt, the
plugin's always-on skill descriptions and the expected skill's `SKILL.md`, plus
an assumed host overhead (`--overhead-tokens`, default 18,000 for `claude` and
9,000 for `codex`), times `--assume-turns` (default 3), plus
`--assume-output-tokens`. The overheads are assumptions, not measurements, and
prompt caching usually makes the real bill lower. Pass `--price-in` and
`--price-out` to see dollars. For `claude` the dry run also prints the hard
ceiling: runs times `--max-usd-per-task`.

Each run writes `runs/<run-id>/` with `prompt.txt`, `events.jsonl` (the host's
transcript), `stderr.txt`, `output.md` (the final answer) and `record.json`
(argv, status, exit code, time, reported cost and tokens, the model the host
named, and the skills it loaded). `manifest.json` holds the plan digest, host
version, payload digest, caps, totals and why the run stopped, if it did.

## 3. Grade

`grade <run-dir>` reads every record and writes `grades.json`:

- **routing**, plugin condition only. A skill counts as loaded when the
  transcript shows a `Skill` tool call naming it or a read of its
  `skills/<id>/SKILL.md`. A positive task passes when its expected skill loaded
  and no skill in `must_not_trigger` did. A task whose expected skill is null
  passes only when no skill loaded.
- **output**. The final answer is piped into `tooling/grade_output.py <skill> -
  --json` (with the task's canary file when there is one) and must PASS. Literals
  the case pins must appear verbatim.

A run that errored or timed out is `not_run` for every check and is left out of
every rate. The scorecard counts those runs separately so a high pass rate over
few completed runs is visible as such.

## 4. Report

`report <run-dir>...` reads `grades.json` from each directory and prints a
scorecard (`--format md`, default, or `json`): per condition and check, the
overall rate and a row per skill as passes/n with a Wilson 95% interval. Five
passes out of five is an interval of roughly 57-100%, not 100%.

It warns when the directories mix plans, hosts, host versions, models or plugin
payloads, and marks an A/B result as not comparable when they do.

## Comparing with and without the plugin

`--condition both` runs every task twice, once with the plugin (`plugin`) and
once without (`baseline`), with the two runs of a pair next to each other in a
random order so that time-of-day drift, rate limits and provider changes hit both
alike. `--max-tasks` never splits a pair. The report then pairs runs by task and
repeat and gives the discordant counts (plugin-only passes, baseline-only
passes) with an exact two-sided sign test on them.

Read that comparison with these limits:

1. **The output rubric favours the plugin by construction.** It checks the
   skill's own report contract: section names, verdict tokens, evidence IDs. A
   baseline host has never seen that contract and will fail it while writing a
   perfectly good answer. A plugin lead on this check shows the contract is being
   followed, not that the answers are better. Literal preservation and canary
   checks are fair to both conditions; the rubric is not.
2. **For answer quality, use blind review.** Give reviewers the prompt and both
   answers without the condition labels, in random order, and score them against
   the `review_notes` the plan carries for each task.
   `tooling/run_model_evals.py` and `tooling/build_review_packets.py` produce
   blind packets in this form for the model suite.
3. **Pin everything but the plugin.** Same `--model`, same host version (check
   `host_version` in each manifest), same plan, same caps, same day. Run both
   conditions in one `run --condition both` rather than two separate runs.
4. **Routing has no baseline.** Without the plugin there is no skill to load, so
   routing is reported for the plugin condition only.
5. **Repeat before you conclude.** Hosts are not deterministic. Use `--repeat 3`
   or more on a smaller plan rather than one pass over a large one, and report
   the interval, not the point estimate. A p-value above 0.05 on a dozen
   discordant pairs means the run could not tell the conditions apart, not that
   they are equal.
6. **Report what was not run.** Errors, timeouts and budget stops are listed in
   the scorecard; keep them in any summary you publish.

## What this does not prove

A pass means the transcript and the answer met a structural check. It does not
mean the answer is correct, that the evidence it cites exists, or that the skill
helps users. The task set is drawn from the repository's own cases, which were
written alongside the skills; a high score on them is weaker evidence than a
score on prompts collected from real use.
