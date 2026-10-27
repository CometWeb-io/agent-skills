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

Host execution currently requires POSIX process groups (macOS/Linux). On other
platforms `--execute` records `NOT_RUN: PROCESS_GROUP_CLEANUP_UNAVAILABLE`;
planning, grading and reporting remain offline. Windows execution needs an
independently qualified Job Object implementation before it can be enabled.

With `--execute`, `NOT_RUN` exits 3; errors or an incomplete schedule exit 1.
Only a non-empty completed schedule without errors or stops exits 0. A deliberate
dry run still exits 0 and starts no host. Always inspect the JSON alongside exit status.

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

The multiagent alias uses its canonical orchestrator's output rubric. A task
without a rubric or non-empty pinned literals receives `not_assessed`, which is
counted separately and excluded from output pass rates and paired comparisons.
A literal-only pass establishes preservation of those literals, not rewrite
fidelity or ebook validity. A followed canary remains a failure in every case.

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

The plan records the SHA-256 of every source file and of itself. A v2 plan also
freezes `candidate_sha256`, `payload_sha256`, `benchmark_sha256`,
`rubric_sha256`, and `host_config_sha256`. `run` refuses changed v2 inputs or a
staged payload that differs from the plan. Both v1 and v2 validate task types,
known skills, unique safe IDs and supported checks before scheduling. Recomputing
a digest does not bypass admission. V2 requires all five matching frozen hashes;
v1 remains readable but has no frozen-input guarantee.

With `--canary`, each output task's material gets an instruction asking the
reader to print a token built from two parts. Only the parts are in the prompt;
`grade` fails the output with `INJECTION_FOLLOWED` if the joined token appears.
Loaded plans reject an instruction that already contains its joined token.
Every output uses the same exact-token check, including canaries without a schema.
See [OUTPUT-GRADING.md](OUTPUT-GRADING.md#canary-files).

## 2. Run

`run` builds one command per task, condition and repeat:

| Host | Command | Plugin condition | Native caps |
| --- | --- | --- | --- |
| `claude` | `claude -p --output-format stream-json --verbose --no-session-persistence --strict-mcp-config --tools Read,Glob,Grep,Skill --allowedTools Read,Glob,Grep,Skill --max-turns N --max-budget-usd X` | adds `--plugin-dir <stage>` | turns and dollars per run |
| `codex` | `codex exec --json --skip-git-repo-check --sandbox read-only -` | first runs `codex plugin marketplace add <stage>` and `codex plugin add cometweb-agent-skills@cometweb-agent-skills` | none; only `--timeout` |

The prompt goes on stdin. `--model` pins the model for either host.

`--reasoning-effort` forwards a host-native value unchanged: Claude gets
`--effort`, Codex gets `--config model_reasoning_effort="VALUE"`. Supported
CLI values are host-specific and the selected model may reject them. There is
no cross-provider effort equivalence. Omission is `NOT_CONTROLLED`; a supplied
value is `REQUESTED_NOT_OBSERVED` because current transcripts do not establish
the effective effort. Manifests and records separate requested and observed
values and hash run options as `run_config_sha256`. Scorecards flag missing
observations and different run configurations rather than declaring controlled A/B.

Scorecards expose `effort_comparison_status`: `EQUAL_EFFORT_NOT_VERIFIED` for
missing, malformed or unsupported host labels, `REPORTED_EFFORT_DIFFERS` for different
observed labels, and `SAME_REPORTED_EFFORT` for matching labels. Matching labels
do not establish equivalent effort across models or providers.

**Isolation.** Each run gets a new temporary directory holding its own HOME, its
own host config directory (`CLAUDE_CONFIG_DIR` or `CODEX_HOME`) and an empty
working directory, removed when the run ends. The runner does not copy your
existing settings, other plugins, MCP configuration, memory or project
instruction files into those directories. This does not enforce filesystem read
isolation: a same-user process can still access files by absolute path, parent
traversal or a symlink unless separate host permissions prevent it. The runner
has not verified those host permissions; blind keys and other-arm outputs must
not rely on HOME/config separation for protection. The plugin is staged once
per run directory from this checkout, the same payload
`tooling/host_smoke.py` installs, and its digest goes into `manifest.json`. The
tool set is read-only. This is separation, not an operating-system sandbox.

**Credentials.** Only `PATH`, the temporary paths, a few locale variables and
the host's credential variables are passed: `ANTHROPIC_API_KEY` or
`CLAUDE_CODE_OAUTH_TOKEN` for `claude`, `OPENAI_API_KEY` or `CODEX_API_KEY` for
`codex`. Because HOME is fresh, a login stored in your normal config or keychain
is not seen; export one of those variables for the session instead. Values are
not copied into `record.json`, which lists variable names only. A host can print
credential values into its transcript or version output; private capture is
not automatic redaction.

**Caps.**

| Option | Default | Effect |
| --- | --- | --- |
| `--max-tasks N` | 10 | hard cap on host runs (task x condition x repeat), at most 500 |
| `--timeout S` | 300 | the POSIX process group is killed after S seconds and recorded as `timeout` |
| `--max-turns N` | 8 | `claude` only |
| `--max-usd-per-task X` | 0.5 | `claude` only; passed as `--max-budget-usd` |
| `--max-total-usd X` | none | reserve the full native per-run cap before each job; Claude only |
| `--max-estimated-total-usd X` | none | reserve the next job's estimate; actual spend can exceed X |
| `--max-total-tokens N` | none | stop once reported tokens reach N |
| `--max-consecutive-errors N` | 2 | stop after N failed runs in a row, such as a missing credential |

For `claude`, a run whose cost was not reported consumes its entire native cap,
even when prices and usage supply an estimate. An estimate never releases this
reservation. This admission ceiling relies on the host enforcing its native
`--max-budget-usd`; it is not independently verified provider billing. A reported
cost above the native cap stops further jobs. `spent_usd` is null when any cost
is unknown; `accounted_usd` includes conservative reservations.

`codex` has no native dollar ceiling. `--max-total-usd` is rejected before any
host command, even with prices supplied. Use `--max-estimated-total-usd` with
both `--price-in` and `--price-out` only when an estimated admission budget is
acceptable. It checks the next estimated job before launch and stops after an
unknown cost. Price-based accounting remains an estimate; a job can overshoot
its estimate. `--max-total-tokens` is a between-job stop, not a per-job token cap.

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
version, frozen acceptance hashes, payload digest, caps, totals and why the run
stopped, if it did. Unsupported hosts and missing credentials materialize one
`not_run` record for every scheduled job; no host process is invoked.

Run IDs use the scheduler index, condition, repeat and a task-ID hash. They do
not embed user-provided path text; use `record.json.task_id` to locate a task.
On POSIX, output directories are 0700 and files 0600 regardless of umask.
Symlinks and multiply linked output files are refused before truncation.
Keep run directories outside version control. Transcripts can contain secrets
printed by a host or tool despite the credential-name-only record format;
review and redact before sharing. Retention is owner managed: archive the
reviewed evidence you need and delete raw runs when that review is complete.
No automatic expiry or secure-erasure guarantee is provided.

Version, setup and task commands use the same bounded capture: each stdout and
stderr file stores at most 8 MiB while the process runs. Exceeding a task stream
limit kills its process group and records `capture_limit`; partial output is
never an executed pass. Codex answers come from captured JSONL, without a
separate host-written `output.md`. Process groups are also cleaned after a
successful parent exit. These controls cover ordinary inherited descendants,
not a hostile same-user executable that escapes its group or writes arbitrary
files. They are not a total filesystem quota or an OS sandbox. POSIX permissions
do not establish Windows ACL protection or isolation from the same user.

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

A run that errored or timed out is left out of every rate. For compatibility,
its individual check keeps the v1 `status: not_run` shape and adds
`execution_status: ERROR`; an unsupported or unauthenticated job has
`execution_status: NOT_RUN`. Grades and reports expose separate `error_jobs`
and `not_run_jobs` counts.

Retry fields are deliberately sparse. `retryable`, `retry_classification`, and
`attempt` appear only for a timeout, an explicit transient exit code (`75`,
`408`, `429`, `502`, `503`, or `504`), or an explicit transient host message.
Terminal failures do not receive retry metadata.

## 4. Report

`report <run-dir>...` reads `grades.json` from each directory and prints a
scorecard (`--format md`, default, or `json`): per condition and check, the
overall rate and a row per skill as passes/n with a Wilson 95% interval. Five
passes out of five is an interval of roughly 57-100%, not 100%.

It warns when the directories mix plans, hosts, host versions, models, frozen
hashes or plugin payloads, and marks an A/B result as not comparable when they
do. The report separates completed runs, errors, and `not_run` jobs; neither
non-completed category contributes to a pass rate.

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

## Three-arm experiment contract (v3 plan, execution not qualified)

The optional `--design three-arm` creates a v3 plan carrying
`cometweb.real-host-three-arm/v1`. Legacy v1/v2 plans and
`--condition baseline|plugin|both` retain their existing behavior.

```bash
uv run python tooling/real_host_eval.py plan --design three-arm \
  --skill release-readiness --per-skill 1 --negatives-per-skill 0 --out three-arm.json
uv run python tooling/real_host_eval.py run --plan three-arm.json --host claude \
  --condition three-arm --max-tasks 3 --out runs/three-arm  # dry run only
```

| Condition | Local helper payload | Skill instructions |
| --- | --- | --- |
| A `native` | empty | absent; no plugin registration |
| B `tools` | local scripts and formal JSON schemas | absent; no plugin registration |
| C `skill` | byte-identical helper inventory to B | Markdown instructions and plugin registration |

The stager copies actual different file sets into each job's `./bundled` directory.
The B/C tool inventory includes executable script source (`.py`, `.sh`, `.js`,
`.mjs`, `.ts`), formal `*.schema.json` interfaces and `requirements.txt`.
Tests, evals, agent adapters, JSON instruction/policy packs, source registries and
contract binding files are excluded from both bundles. C adds Markdown/reference
instructions and native plugin metadata. This is a bounded runtime subset,
not the entire installed package: helpers requiring omitted policy packs or other
assets are **not qualified by this experiment**. No dependency installation is
performed. A source category is not a general guarantee that arbitrary future
files are instruction-free; review the frozen inventories for each candidate.

The host tool set is identical across A/B/C (`Read,Glob,Grep,Bash,Skill` for
Claude; the existing generic Codex exec interface for Codex). Tools with no local
payload have no bundled helper or skill to open. All three receive the same task,
fixture and neutral local execution-boundary instructions. The C condition's
plugin instructions are the only additional instruction exposure. Tool scripts
and formal schemas expose their own interfaces in both B and C, so structural
contract compliance still does not establish better task outcomes.

**Native host execution remains NOT_RUN.** The runner has not yet qualified the
required permissions profile across every tool of a model host. The separate
Python-helper backend below cannot establish that full-host boundary. A v3 `run --execute` therefore writes a
terminal receipt for every scheduled job with
`ENFORCED_HELPER_BOUNDARY_UNAVAILABLE`, exits 3 and starts no host process,
including no version probe or plugin installation. This is an implementation and
qualification limit of this runner, not a claim that host platforms have no
sandbox capability. A fresh HOME, working directory, native read-only flag or an
instruction to stay in the working directory does not establish the required
boundary. The new Bash-enabled profile cannot silently widen the executable
legacy profile.

The offline adapter tests use a controlled local fixture executable that actually
launches a Python helper, reads a schema value and checks instruction-file
availability. They establish A/B/C exposure and subprocess/receipt behavior. They
are **not** real-model effectiveness, automatic skill activation, native-host
permission, network confinement or catalog-wide helper qualification evidence.
No paid model, API request or real host installation is needed for these tests.

The plan freezes the source commit when locally observable, harness-source hash,
condition-specific file inventories, shared B/C helper hash, benchmark/rubric and
legacy candidate/payload hashes. A working-tree implementation is identified by
its harness and exposed-file hashes as well as its base commit; the commit alone
does not represent uncommitted code. Changes to that identity require replanning.
Requested model and effort settings remain distinct from observed metadata.
Missing model, provider revision, hardware, effort and resource observations are
explicitly unavailable/null; token and cost estimates retain their estimate label.
Bytes/4 is not measured context use, and reading additional helper resources is
not included in that approximation.

Task blocks use seeded shuffled permutations: every complete six-triple block
covers all six A/B/C orders. Partial final blocks are reproducible but are not
claimed to be perfectly balanced. `--max-tasks` never cuts a triple. Single-arm
native/tools/skill runs are allowed only with a v3 plan and cannot independently
establish a matched comparison.

V3 records retain exposure inventories and hashes, captured prompt/transcript/
output receipts, unknown resource values and `task_outcome_status: not_assessed`.
Failures retain partial outputs; schedule stops retain an explicit `not_run`
record for each unstarted job. Version-probe failures retain their partial stdout/
stderr and terminal records. JSON reports include every run result and separate
same-case/repeat comparisons for A–B, B–C and A–C. Matching is within one run
directory, requires one completed observation per arm and the same reported model,
and refuses duplicate rows or unknown models. Failures, missing arms and
unassessed outputs remain visible and do not become passes or zero-valued
measurements. These comparisons describe the existing structural output check;
unknown effective effort and the skill-oriented rubric prevent a causal task-
effectiveness claim. Independent outcome grading needs a reviewed external oracle
and trusted observation; a model's final answer is not that observation.

## Probed local Python-helper backend (no model calls)

`tooling/isolated_exec.py` uses the installed CLI's `codex sandbox -C WORK -P
PROFILE -c permissions.PROFILE=...` interface. It does not start `codex exec`,
Claude, a model session or an API call. Current local CLI help is authoritative:
the sandbox subcommand on the qualified CLI generation has no `macos` positional
subcommand. `codex exec` accepts config overrides; selecting and observing the
same profile through `default_permissions` remains a separate native-host test.
The absence of an exec `-P` flag is not proof that exec cannot support the policy.

```bash
uv run python tooling/isolated_exec.py probe --workspace /path/to/owned-work \
  --out /path/to/private-probe-evidence --codex-bin /path/to/codex
uv run python tooling/isolated_exec.py run-python --workspace /path/to/owned-work \
  --out /path/to/private-helper-evidence --proof /path/to/private-probe-evidence/proof.json \
  --proof-sha256 REVIEWED_PROOF_SHA256 /path/to/owned-work/helper.py
```

The implemented backend is restricted to macOS and Python under `/opt/homebrew`,
with read access to the declared OS/runtime roots, owned-workspace writes and
network disabled by the named profile. Each probe starts with a fresh credential-
free Codex config outside the helper's readable workspace. Synthetic sibling
canaries must prove outside read/write denial, unchanged canary contents, TCP
denial and successful inside read/write. Failed, missing, edited, differently
pinned or different-workspace proofs refuse execution. The selected Codex/Python
binary hashes, runner implementation, OS, profile and limit identity must still
match. The proof scope covers those selected executables and local observations;
it does not inventory every shared runtime library or attest binary authenticity.
Use only a reviewed local Codex executable and a trusted proof/pin.

The wrapper applies hard CPU (5 seconds), per-file size (8 MiB) and descriptor
(64) limits before caller Python code. Wall timeout and bounded stdout/stderr use
the existing process-group cleanup. Memory, aggregate disk and hostile process-
tree quotas are not established by these controls. Raw stdout/stderr and the
result receipt retain failures and timeouts; no unconfined fallback runs. The
script must resolve inside the owned workspace; its source hash is recorded
before execution. Trusted evidence is saved outside that workspace. All model,
token and cost measurements remain null; completing a helper is not task success.

Portable tests use an explicitly unqualified CLI fixture for parsing, receipt and
resource-limit behavior. An unconfined forwarding fixture really accesses the
synthetic outside canary and must fail. Only a fresh native canary run establishes
the installed CLI's selected boundary. Qualifying this helper backend does not
qualify full-host A/B/C execution or measure model effectiveness.

## Native local cache migration (no model calls)

`host_smoke.py` can test old→new→rollback in the same temporary HOME/config/cache
for Codex and Claude Code. Supply an archived source tree from a pinned prior
commit; the current checkout is the new source. Both versions must differ.

```bash
uv run python tooling/host_smoke.py --migration-from /path/to/prior-source \
  --require claude,codex --json runs/native-migration.json
```

Use a fresh output path. The JSON retains source payload hashes, raw commands
(including failures/timeouts), installed version readbacks and cache manifests.
Actual cache bytes are retained beside it in `native-migration-cache/`, before
removal. A failure stops that host's sequence; diagnostic retries cannot replace
the original result. Every migration command has a 60-second timeout. The runner
removes its owned temporary profile at the end; an empty final plugin list proves
registration removal, not physical cache purge by the native uninstall command.

The Claude test uses the existing local `host-smoke` marketplace wrapper, not
the shipped GitHub URL. These commands do not execute models, copy credentials
or install into your normal profile. They do not prove OS isolation, online
distribution, automatic skill activation or task quality. A missing required
CLI fails rather than passing. Cursor is unsupported in this migration mode.
Deterministic migration fault tests run in portable CI; actual native migration
requires the two installed CLIs and the explicitly supplied prior source.
