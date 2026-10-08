# Repository tooling

Every script under `tooling/`, what it is for, which `check_all.py` gate runs
it, and what it reads and writes. `tooling/tests/test_tooling_inventory.py`
fails when a script is added or removed without its row here, and when the
**Gate** column disagrees with `GATES` in `tooling/check_all.py`. A gate is
listed when the script appears in that gate's command or its `--fix`
generator. "—" means no gate runs the script directly: it is a library other
tools import, or an operator tool run by hand.

Run every gate with `uv run python tooling/check_all.py` (`--fast` while
iterating, `--ci` before a pull request); `--list` prints them.

## Gate runner and local validation

| Tool | What it does | Gate | Reads → writes |
| --- | --- | --- | --- |
| `check_all.py` | The one list of gates. CI runs `check_all.py --ci`; `--fast` drops the slow and networked gates; `--fix` runs the generators first. Gates run in parallel, longest first, and the run fails if any gate changes the working tree. | — | `GATES` in the script → a pass/fail table on stdout |
| `validate_local.py` | A recorded, report-producing run of a subset of the gates without GitHub Actions; the release workflow runs it before attesting packages. | — | checkout → a report directory given by `--output` |

## Supply chain and static analysis

| Tool | What it does | Gate | Reads → writes |
| --- | --- | --- | --- |
| `audit_deps.py` | Proves skill `RUNTIME.json` dependencies are in `uv.lock` (`--coverage`), then runs pip-audit over every locked group with hashes. | `runtime_deps_locked`, `pip_audit` | `uv.lock`, `skills/*/RUNTIME.json`, the vulnerability database (network) → stdout |
| `sast.py` | Semgrep with the local rules over tracked Python and shell files, engine pinned in `uv.lock` and run in an isolated environment. Rule self-test first, then the scan. A clean result is recorded under `dist/.cache/sast/` by the SHA-256 of every input and reused while nothing changes; `--no-cache` (passed under `--ci`) always scans. | `sast` | tracked `*.py`/`*.sh`, `tooling/sast/`, `uv.lock` → stdout, `dist/.cache/sast/<key>` |
| `sbom.py` | CycloneDX 1.6 SBOM of the shipped skills and their declared runtime dependencies; `--check` builds and validates it only. | `sbom` | `skills/`, `plugin.json` (and `dist/*/skill.zip` with `--dist`) → `--output` JSON |
| `public_safety.py` | Fail-closed leak scanner for secrets, private paths and forbidden file names; `--history` walks every reachable commit. Never echoes a matched value. | `public_safety`, `public_safety_history` | working tree or Git history → findings on stdout |
| `public-safety-check.sh` | Shell wrapper around `public_safety.py` that propagates its exit code; named in the pull request template. | — | `--root` → exit code |

## Registry, generated files and shared copies

| Tool | What it does | Gate | Reads → writes |
| --- | --- | --- | --- |
| `sync_skill_registry.py` | Syncs every registered package VERSION and the routing fields owned by its `OVERRIDES` table. | `registry_sync` | package VERSION files and `registry/skills.json` → the same registry (`--apply`) |
| `sync_orchestrator.py` | Keeps the multiagent orchestrator's planner and bundled CW-AIP schemas byte-identical to their canonical copies. | `orchestrator_sync` | `skills/skill-orchestrator/`, `protocol/` → `skills/skill-orchestrator-multiagent/` |
| `sync_roaster_shared.py` | Keeps the scripts and references the three roaster skills share byte-identical. | `roaster_shared` | one roaster package → the other two (`--sync`) |
| `generate_adapters.py` | Generates host adapters, routing rules, compatibility tables and the README catalog from the registry. | `adapters` | `registry/` → `docs/generated-*`, `extras/`, `rules/`, `skills/*/agents/openai.yaml`, `README.md`, plugin manifests |
| `adapter_metadata.py` | Lossless merge of host metadata: registry-owned fields win, unknown extensions survive. Imported by `generate_adapters.py`. | — | library |
| `context_budget.py` | Measures each skill's front-door and reference cost in context against a recorded baseline; `--update` accepts a deliberate change. | `context_budget` | `skills/*/SKILL.md`, `registry/context-baseline.json` → `docs/generated-context-budget.md` |
| `plugin_release.py` | Refuses a change to the shipped skill set without a plugin version bump; `--bump` bumps and records in one step. | `plugin_release` | `skills/*/VERSION`, `VERSION`, the merge base → plugin version fields and `registry/plugin-release.json` (`--record`, `--bump`) |
| `skill_change_history.py` | Requires changed skill instructions/scripts to have a newer package VERSION and matching updated CHANGELOG. | `skill_change_history` | merge base and package sources → errors on stdout; no writes |
| `new_skill.py` | Scaffolds and registers a skill package that passes every fast gate on day one. | — | a skill id and description → `skills/<id>/`, registry, routing cases, baselines |

## Package validation and packaging

| Tool | What it does | Gate | Reads → writes |
| --- | --- | --- | --- |
| `validate_repo.py` | Registry, skill packages, protocol files and eval suites agree with each other. | `validate_repo` | `registry/`, `skills/`, `protocol/`, `evals/` → stdout |
| `validate_skill.py` | Validates one skill package directory; used by `new_skill.py`. | — | a skill directory → stdout |
| `skill_contracts.py` | Holds each skill's scripts, documentation and eval cases to its `references/contract.json`; `--draft` proposes one. | `skill_contracts` | `skills/*/references/contract.json`, scripts, docs, evals → stdout |
| `compatibility.py` | Host compatibility profiles and the frontmatter parser other tools share. | `compatibility` | `skills/*/SKILL.md`, `registry/hosts.json` → stdout |
| `validate_openai_plugin.py` | Checks the ChatGPT/Codex marketplace and plugin manifest contract. | `openai_plugin` | `.agents/plugins/marketplace.json`, `plugin.json` → stdout |
| `markdown_resources.py` | Bounded Markdown link and image discovery for bundle linting. Imported by `package_skill.py` and the docs tests. | — | library |
| `package_skill.py` | Builds a deterministic, scanned, immutable `skill.zip` for one skill; refuses a dirty tree. | — | `skills/<id>/` in a clean checkout → `dist/<id>/<version>/skill.zip` and its checksum |
| `installation_acceptance.py` | Builds every package from one clean committed copy of the checkout, installs each zip into its own directory and runs the bundled offline helpers. Structural only: host and model acceptance stay `not_assessed`. | `installation_acceptance` | checkout → a JSON report on stdout (temporary directories only) |
| `doctor.py` | Read-only diagnosis of one skill: registry entry, source, built package and, when given, an installed copy and a host's session inventory export. Exit 0 healthy, 1 issues found, 2 bad input. A directory on disk is reported as present, never as discovered by a host session. | — | `registry/skills.json`, `skills/<id>/`, `dist/<id>/skill.zip`, optional `--installed-root` and `--session-inventory` JSON → a `cometweb.skill-doctor/v1` report |
| `host_smoke.py` | Loads the plugin in the real host CLIs that are installed (manifest validation and listing commands only, no model calls), each against a staged copy with a temporary home directory. | — | host CLIs on PATH → a report on stdout or `--json` |

## Routing evaluation

| Tool | What it does | Gate | Reads → writes |
| --- | --- | --- | --- |
| `route_skill.py` | Deterministic router with a lexical ranker; `--explain` shows why a prompt routes where it does. Used by every routing tool below. | — | a prompt, `registry/skills.json`, `registry/routing-policy.json` → the routed skill |
| `run_routing_evals.py` | Runs the routing suite against `route_skill.py`. | `routing_evals` | `evals/routing/suite.json` → stdout |
| `routing_coverage.py` | Per-skill positive and negative case floors and suite defects such as duplicates and unknown skill names. | `routing_coverage` | `evals/routing/`, registry → stdout |
| `routing_holdout.py` | Integrity of the frozen routing holdout and aggregate-only accuracy. | `routing_holdout` | `evals/routing/holdout.json` and its lock → totals on stdout |
| `run_policy_evals.py` | Routing policy admission, including the injection-style adversarial suite. | `policy_evals`, `routing_adversarial` | `evals/routing/policy-suite.json` or `--suite` → stdout |

## Behaviour and output evaluation

| Tool | What it does | Gate | Reads → writes |
| --- | --- | --- | --- |
| `run_behavior_evals.py` | Runs each skill's scripts the way its references tell a user to and pins exit codes and output; suites run side by side, each case in its own temporary directory. A case whose script needs a `RUNTIME.json` package this interpreter lacks is skipped with the reason; `--require-runtime` (passed under `--ci`) fails it instead. | `behavior_evals` | `evals/behavior/*/suite.json`, `skills/*/scripts/` → stdout |
| `run_blind_eval_harness.py` | Checks that behaviour suites are well formed and records fixture inventories for operator-run comparisons. | `blind_eval_harness` | `evals/behavior/` → stdout, `dist/eval-reports/` with `--write-report` |
| `grade_output.py` | Grades a skill's actual output against its output contract, offline; `--self-test` runs the golden good and broken cases. | `output_grading` | an output file or stdin, `evals/output/` → a verdict on stdout |
| `eval_strength.py` | Disables one `if` guard at a time in a private copy of each kernel and counts the guards its harness still catches; mutants of a package run side by side. | `eval_strength` | `skills/*/scripts/`, `registry/eval-strength.json` → `docs/generated-eval-strength.md` (`--table`), the baseline (`--update`) |
| `kernel_error_envelope.py` | Holds every payload-taking skill kernel to one error envelope: any JSON value is answered with an object, a non-object is refused with exactly one `<name>:not-object` error and a non-passing status, refusals carry the keys the skill's other refusals carry, and scripts with a behaviour suite refuse `null`, a list or a string without a traceback. Runs under pytest as `tooling/tests/test_kernel_error_envelope.py`. | — | `skills/*/scripts/`, `skills/*/references/contract.json`, eval corpora, `evals/behavior/` → stdout, exit 1 on any violation |

## Model comparisons (operator-run, never in CI)

| Tool | What it does | Gate | Reads → writes |
| --- | --- | --- | --- |
| `run_model_evals.py` | Baseline, current and candidate runs of a suite through a runner command you supply (`--runner-json`); without `--execute` it reports `not_run`. | — | a suite, two skill roots, a runner argv → a new `--output` directory of run records |
| `openai_eval_runner.py` | A runner for `run_model_evals.py`: reads one `cometweb.eval-request/v1` on stdin, sends it text-only to the OpenAI Responses API, prints a `cometweb.eval-response/v1`. Needs `OPENAI_API_KEY` and `COMETWEB_EVAL_MODEL`; refuses tool-using requests; never stores the response. | — | stdin request, environment credentials → stdout response |
| `build_review_packets.py` | Turns frozen runner requests and results into matched, unreviewed review packets. | — | `run_model_evals.py` output → review packets |
| `reviewer_bundle.py` | Exports only reviewer-facing fields, never the unblinding map. Imported by `build_review_packets.py`. | — | library |
| `review_skill_evals.py` | Compares reviewed, matched runs and reports per-case deltas; no averages until every run is reviewed. | — | a `cometweb.skill-comparison/v1` file → a comparison on stdout |
| `audit_contracts.py` | Checks declared UI, API, auth and storage paths against the evidence records supplied for them. | — | a contract trace and artifacts root → a report on stdout |
| `real_host_eval.py` | Plans tasks from the repository's own eval cases (never the frozen holdout), freezes candidate/payload/benchmark/rubric/host identities in v2 plans, runs them through a host CLI in headless mode with the plugin staged or absent, grades routing and output from the transcripts, and reports pass rates with Wilson intervals while separating errors from `not_run`. `run` is a dry run that prints commands and an estimated cost unless `--execute` is given with task and spend caps; see [REAL-HOST-EVALS.md](REAL-HOST-EVALS.md). | — | eval suites and rubrics, host CLI on PATH (only with `--execute`) → a plan JSON, a runs directory, grades and a Markdown scorecard |
| `real_host_adapters.py` | Loads the runtime-host capability registry and fails closed for unsupported hosts or missing credentials before a model process starts. | — | `registry/runtime-hosts.json`, environment and optional binary override → READY/NOT_RUN capability result |

## Protocol (CW-AIP) and knowledge freshness

| Tool | What it does | Gate | Reads → writes |
| --- | --- | --- | --- |
| `validate_envelope.py` | Validates a full CW-AIP v2 envelope: core fields, typed payload, hash and, with `--final`, finality. | `envelope` | an envelope JSON → stdout |
| `validate_evidence_envelope.py` | Evidence payload validator used by `validate_envelope.py`. | — | an envelope JSON → stdout |
| `validate_decision_envelope.py` | Decision payload validator used by `validate_envelope.py`. | — | an envelope JSON → stdout |
| `validate_coverage.py` | Validates audit coverage ledgers: source inspection is never counted as executed testing. | — | a coverage ledger JSON → stdout |
| `whykit_draft.py` | Renders a validated final evidence or decision envelope as an unreviewed WhyKit draft. | — | an envelope JSON → a Markdown draft (`--output` or stdout) |
| `check_knowledge.py` | Freshness of recorded knowledge rules against their TTL, without fetching any source: a rule inside its TTL is still `not_reverified`. `--strict` exits 1 on any stale or future-dated rule. Not a gate, because the result depends on the date. | — | `registry/knowledge-rules.json` or a skill's `live-source-registry.json`, `--as-of` → a JSON report |

## Shared modules in `tooling/core/`

| Tool | What it does | Gate | Reads → writes |
| --- | --- | --- | --- |
| `core/__init__.py` | Package marker, so the tools can import `core.*`. | — | library |
| `core/evidence.py` | Evidence kind labels (static, unit, deterministic behaviour, model eval) that keep a green harness apart from runtime acceptance. | — | library |
| `core/git.py` | Read-only Git calls with hooks, pager, fsmonitor and global configuration shut out. | — | library |
| `core/paths.py` | Path canonicalisation that refuses a path that is itself a symlink. | — | library |
| `core/subprocess_env.py` | Minimal environment for child processes, so helper scripts do not inherit secrets. | — | library |
