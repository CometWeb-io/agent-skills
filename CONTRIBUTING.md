# Contributing

Thanks for improving CometWeb Agent Skills. This repo optimizes for
**evidence-backed, tested skills** — not prompt volume.

## The flow

```bash
uv sync --group dev                            # 1. once; needs uv and Python 3.12+
# 2. make the change
uv run python tooling/check_all.py --fix --fast    # 3. regenerate derived files, quick gates (~10 s)
uv run python tooling/check_all.py                 # 4. every gate, exactly as CI runs them (~3 min)
```

`tooling/check_all.py` is the only gate list. CI calls it with `--ci`, and a
test fails if the workflow grows a gate of its own, so a green local run means
the same checks CI will run. It runs gates in parallel, prints a summary table,
and exits non-zero if any gate fails or if a gate modified the checkout.

| Option | Effect |
| --- | --- |
| `--fast` | Leave out pytest, eval strength, the plugin-version record, package builds, the history leak scan and `pip-audit` |
| `--fix` | Run the selected gates' generators first: registry sync, adapters and README catalog, shared copies, context table, `uv lock` |
| `--only ids` / `--skip ids` | Comma-separated gate ids; `--list` shows them all |
| `--verbose` | Print the output of passing gates too |

`--fix` never records a baseline. When the context-budget or eval-strength gate
fails because you changed a skill on purpose, the summary prints the command
that accepts the new number; run it and commit the baseline with the change.

A missing `shellcheck` is reported as skipped locally and fails under `--ci`.
To run the fast gates on every commit, install the optional hook:
`uv tool install pre-commit && pre-commit install` (see `.pre-commit-config.yaml`).

`uv.lock` is committed. Change dependencies in `pyproject.toml`, then run
`uv lock` (or `check_all.py --fix --only uv_lock`) and commit both files.

## What belongs here

- Deterministic scripts, validators, kernels
- Tests and eval fixtures (routing, behavior, golden cases)
- `SKILL.md` and references scoped to one skill

## What does not belong here

- GTM / promotion playbooks, outreach calendars, "how to get stars" guides
- Council or product strategy memos intended for a private workspace
- Secrets, Notion UUIDs, customer data
- Paths into a private vault — see the local-binding rule in [`AGENTS.md`](AGENTS.md)
- Bulk-generated skills without tests

## Adding a skill

```bash
uv run python tooling/new_skill.py my-new-skill \
  --description "80-1024 characters; this is what routes it" \
  --summary "One line for the README catalog." --group "Product, research, and partnerships"
uv run python tooling/check_all.py --fast      # passes immediately
```

This writes the package and registers it: the `registry/skills.json` entry, the
README catalog row, three positive and two negative routing cases, and this
skill's rows in the context and eval-strength baselines (no other skill's rows
are re-recorded). Generated adapters are rebuilt by `generate_adapters.py`.

Everything it writes is a placeholder that works. Replace, in this order:
`SKILL.md` and `references/output-contract.md` (copy a changed description
into the registry entry too); the validator in
`scripts/output_contract.py` with one case per rule in `evals/cases.json`
(pin the exact `errors` list); and the `my-new-skill-scaffold-*` routing cases,
`routing_signals`, `owns` and trigger examples. Then run the flow above.
`--no-register` writes the package only.

## Adding a routing eval case

Add the case to `evals/routing/suite.json`. Routing signals are read from
`registry/skills.json` only — there is no second signal list in the runner. Use
`"expected_primary_skill": null` to assert that **no** skill should claim a
prompt. Every active skill needs at least three positive cases and two that
forbid it.

## Registry and generated files

`registry/skills.json` is the source of truth for descriptions, versions,
ownership boundaries and routing signals. Entries for the skills listed in
`OVERRIDES` in `tooling/sync_skill_registry.py` are generated from that table:
edit `OVERRIDES`, not the registry. Never hand-edit generated output: the
adapters, the `docs/generated-*` tables, the host routing files
(`extras/cursor-routing.mdc`, `extras/AGENTS.snippet.md`), each skill's
`agents/openai.yaml` interface block (its `short_description` is built to fit
the 25-64 characters Codex shows), the README skill catalog and skill count,
and the package list in the host plugin manifests all come from the registry
and `registry/readme-catalog.json` via `--fix`.

## Skill quality bar

| Expectation | CometWeb bar |
| --- | --- |
| `SKILL.md` only | + scripts and/or schemas where claims are enforceable |
| No tests | pytest for kernels and validators, or a `skills/<name>/scripts/run_evals.py` harness |
| Vague routing | Explicit negatives in the description + a routing eval case |
| Silent handoffs | CW-AIP envelope fields in the output contract |

Harnesses in `scripts/run_evals.py` run under pytest through
`tooling/tests/test_skill_eval_harnesses.py`; the eval-strength baseline is the list
of skills that must ship one.

**A green suite proves nothing on its own.** `eval_strength.py` copies each
package to a temporary directory, replaces one `if` guard at a time with
`if False:`, and reruns that package's harness. A guard the harness still passes
without is a rule nothing pins. `registry/eval-strength.json` records today's
held counts, which may rise freely; a fall fails the gate, as does strength under
the floor in `registry/eval-strength-policy.json`. A case that asserts only
`status: INVALID` holds no single rule — pin the exact `errors` list. Treat the
number as a floor, not a target: some guards are genuinely unobservable.

**Context cost.** A host pays for SKILL.md whenever the skill is loadable;
references are paid only when opened. `registry/context-baseline.json` records
each front door, and the gate fails when one grows more than 10% without the
baseline being updated, so growth is a decision rather than a drift. The useful
signal is `deferred` in
[`docs/generated-context-budget.md`](docs/generated-context-budget.md): the
share of a skill held behind its front door.

## Linting

`ruff.toml` enables only rules whose violation is plausibly a defect —
undefined names, dead assignments, silent `zip` truncation, naive datetimes.
Large mechanical migrations are deliberately off: a diff that touches every
file hides the changes that matter. If a rule fires on something intentional,
prefer a narrow `# noqa: <RULE>` with a comment saying why.

## Tests import rule

Test modules must not import each other. Shared fixtures and builders live in
`tooling/tests/_tooling_fixtures.py` and
`skills/cometweb-context/tests/_context_fixtures.py`. The suite runs under
pytest's `importlib` import mode, so test basenames do not have to be unique
across skills — but a test module that imports a sibling will not collect.

## Plugin version

Claude Code and Codex cache an installed plugin under the `version` in its
manifest. `claude plugin update` replaces the cached copy only when that
version changes; with the same version it keeps the old skills and says the
plugin is already up to date. A skill change merged without a plugin version
bump therefore never reaches anyone who installed the plugin.

The rule: any change to the **shipped skill set** (a package added, removed or
renamed under `skills/`) or to **any skill's `VERSION`** bumps the plugin
version in the same pull request.

- Patch for fixes only; minor when a skill gains behaviour or a skill is added;
  major when a skill is removed or renamed, or a contract breaks.
- One value everywhere: `VERSION`, `pyproject.toml` (then `uv lock`),
  `plugin.json`, `.claude-plugin/plugin.json` and `.cursor-plugin/plugin.json`.
- Record the shipped set for that version:

```bash
uv run python tooling/plugin_release.py --record   # after bumping VERSION
uv run python tooling/plugin_release.py --check    # check_all runs it with --require-base under --ci
```

`registry/plugin-release.json` holds the plugin version and every shipped skill
with its `VERSION`. `--check` fails when the tree differs from that record, and
also compares against the merge base with `origin/main`: if the shipped set
changed there, the plugin version must be greater than the base's, so editing
the record in place does not get around it. `--record` refuses to record a
different skill set under a version that was already recorded.

## Releases

`check_all.py` already runs the history leak scan and the all-package
installation acceptance. For a recorded evidence report (per-check logs, JUnit,
source fingerprints) use `tooling/validate_local.py`; see
[docs/LOCAL-VALIDATION.md](docs/LOCAL-VALIDATION.md). Build a deterministic,
scanned package for a skill with:

```bash
uv run python tooling/package_skill.py <skill-id>
```

Publication is approval-gated per skill and has no safety-scan bypass; see
`tooling/publish_public_dry_run.py`. A file removed from `HEAD` stays in history
until that history is rewritten.

Longer-form background lives in [`docs/`](docs/README.md).
