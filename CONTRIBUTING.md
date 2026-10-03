# Contributing

Thanks for improving CometWeb Agent Skills. This repo optimizes for
**evidence-backed, tested skills** — not prompt volume.

## What belongs here

- Deterministic scripts, validators, kernels
- Tests and eval fixtures (routing, behavior, golden cases)
- `SKILL.md` and references scoped to one skill
- Changes that keep every gate below green

## What does not belong here

- GTM / promotion playbooks, outreach calendars, "how to get stars" guides
- Council or product strategy memos intended for a private workspace
- Secrets, Notion UUIDs, customer data
- Paths into a private vault — see the local-binding rule in [`AGENTS.md`](AGENTS.md)
- Bulk-generated skills without tests

## Setup

```bash
uv sync --group dev
```

Requires [uv](https://docs.astral.sh/uv/) and Python 3.12+. The lockfile is
`uv.lock` (committed). Do not hand-edit it — change dependencies in
`pyproject.toml`, then run `uv lock` and commit both files.

## Before a PR

Run the local repository gate. It writes per-check logs and a JUnit report
outside the checkout, and refuses to pass if the working tree changes underneath it:

```bash
uv run python tooling/validate_local.py --trusted-checkout --output ../agent-skills-validation-run-01 --timeout 900
```

Choose a new output directory outside the checkout for each run. The report is
`../agent-skills-validation-run-01/report.json`. A check is only `passed` when it
exits zero **and** nothing was skipped — an unproven test is not a green one.
The GitHub Actions workflow has a small number of additional checks; run the
public-safety scan below locally as well. Before a release, exercise the actual
ZIPs with the locked development environment:

```bash
uv run python tooling/installation_acceptance.py --all --run-helpers --trusted-checkout
```

This builds and extracts all packages, then runs bundled `run_evals.py` and
`self_check.py` entrypoints from a separate working directory. The multiagent
validator additionally must accept a valid envelope, reject malformed data,
and fail closed without `jsonschema`. Packages without those offline checks
report helper execution as `not_assessed`; no result proves live host/model
acceptance. This executes trusted repository code, not a security sandbox.

To run pieces individually while iterating:

```bash
uv run ruff check .                         # lint: defect rules, not house style
uv run pytest -q                            # full suite
uv run python tooling/validate_repo.py            # registry is the source of truth
uv run python tooling/compatibility.py            # host capability contract
uv run python tooling/generate_adapters.py        # regenerate adapters and tables
uv run python tooling/generate_adapters.py --check
uv run python tooling/run_routing_evals.py        # routing signals from the registry
uv run python tooling/run_behavior_evals.py       # executable behavior assertions
uv run python tooling/public_safety.py --root .   # leak gate over the working tree
```

Before tagging a release, also run the history pass:

```bash
uv run python tooling/public_safety.py --history --root .
```

It applies the same leak rules to every reachable commit, not just the working
tree. A file removed from `HEAD` stays in history until that history is
rewritten.

## Skill quality bar

| Expectation | CometWeb bar |
| --- | --- |
| `SKILL.md` only | + scripts and/or schemas where claims are enforceable |
| No tests | pytest for kernels and validators, or a `skills/<name>/scripts/run_evals.py` harness |
| Vague routing | Explicit negatives in the description + a routing eval case |
| Silent handoffs | CW-AIP envelope fields in the output contract |

Every skill's coverage runs under `pytest`. A skill that keeps its cases in
`skills/<name>/scripts/run_evals.py` instead of a `tests/` directory is still executed —
`tooling/tests/test_skill_eval_harnesses.py` discovers and runs those harnesses,
so coverage cannot quietly stop running.

Longer-form background lives in [`docs/`](docs/README.md).

## Linting

`ruff.toml` enables only rules whose violation is plausibly a defect —
undefined names, dead assignments, silent `zip` truncation, naive datetimes.
Large mechanical migrations (annotation syntax, import ordering) are
deliberately off: a diff that touches every file hides the changes that matter.

If a rule fires on something intentional, prefer a narrow `# noqa: <RULE>` with
a comment saying why, over widening the ignore list for the whole repo.

## Context cost

A host pays for SKILL.md whenever the skill is loadable at all — before any work
happens, and for every skill it can route to. References are paid only when the
skill opens one. So the front door is the expensive part, and detail belongs
behind it.

```bash
uv run python tooling/context_budget.py                 # the current table
uv run python tooling/context_budget.py --check         # gate: unexplained growth fails
uv run python tooling/context_budget.py --update        # accept a new cost deliberately
```

`registry/context-baseline.json` records what each front door costs today. The
gate fails when one grows more than 10% without that baseline being updated,
which forces the growth to be a decision rather than a drift. There is no
absolute token ceiling: the right ceiling depends on the host, and this
repository does not assert numbers it cannot evidence.

The useful signal is `deferred` in
[`docs/generated-context-budget.md`](docs/generated-context-budget.md) — the
share of a skill held behind its front door. A large skill with a high deferred
ratio is well built; a small one with a low ratio is carrying detail it should
have moved. `evidence-researcher` is the current exemplar: ~1,300 estimated
tokens of front door in front of 34 KB of references.

## What a test suite is worth

A green suite proves nothing on its own. Inverting the priority-score comparator
in `portfolio_kernel` left all ten of its golden cases passing, because every
ranking case was already decided by the gate order before the score was
consulted. Counting cases would not have shown that.

The three packages that ship `scripts/run_evals.py` are already executed by
`tooling/tests/test_skill_eval_harnesses.py`, in-process so their coverage is
visible. What was missing is whether those runs hold anything.

```bash
uv run python tooling/eval_strength.py                  # the current table
uv run python tooling/eval_strength.py --check          # gate: a rule that stopped being pinned fails
uv run python tooling/eval_strength.py --update --table docs/generated-eval-strength.md
```

`eval_strength.py` copies each package to a temporary directory, replaces one
`if` guard at a time with `if False:`, and runs that package's own harness. A
guard the harness still passes without is a guard nothing is holding. One-line
guards (`if not ok: errors.append(...)`) and `elif` branches count too; the
compact kernels write most of their rules that way. The working tree is never
touched.

A case that asserts only `status: INVALID` holds no single rule: removing any
one check still leaves another error, and the status stays the same. Pin the
exact `errors` list instead.

Treat the number as a floor, not a target. A guard can be unheld because it is
genuinely unobservable — the same value either way, or masked by an earlier gate
— and writing a case to chase the percentage in those spots buys nothing. Write
the case when a real rule is unpinned.

`registry/eval-strength.json` records today's floor. Held counts may rise
freely; a fall fails the gate.

## Registry and generated files

`registry/skills.json` is the source of truth for descriptions, versions,
ownership boundaries and routing signals. Do not hand-edit generated adapters
or tables; change the registry (or the skill's `SKILL.md` and `VERSION`) and
regenerate. The README skill catalog is generated too: the block between the
`BEGIN GENERATED` / `END GENERATED` markers takes versions and the skill set
from the registry, and grouping and one-line summaries from
`registry/readme-catalog.json`. Generation fails if the two files name
different skills.

```bash
uv run python tooling/generate_adapters.py
```

`tooling/sync_skill_registry.py` refreshes the entries for the skills listed in
its own `OVERRIDES` table (version and description from the package, routing
metadata from the table). Run it with `--check` first: `--apply` overwrites
those entries' `routing_signals` and ownership fields with the table's copy, so
review the diff of `registry/skills.json` before keeping it.

`validate_repo.py` fails when a registry entry and its package disagree, so the
two cannot drift apart silently.

## Adding a skill

```bash
uv run python tooling/new_skill.py my-new-skill --description "80-1024 characters; this is what routes it"
```

That writes a package which already satisfies the shared surface, carries the
icon the generated adapters need, and ships an eval harness. The harness fails
until you implement `run_case()` — deliberately, because a harness that passes
while asserting nothing is a decoration. The command prints the remaining steps;
the full walk-through, with every command, is in
[README → Write and evaluate a new skill](README.md#write-and-evaluate-a-new-skill).

It does not write the registry itself: the entry for a new skill is added to
`registry/skills.json` by hand, and `generate_adapters.py` derives everything
else from it. A second writer would be a second source of truth.

## Adding a routing eval case

Add the case to `evals/routing/suite.json`. Routing signals are read from
`registry/skills.json` only — there is no second signal list in the runner. Use
`"expected_primary_skill": null` to assert that **no** skill should claim a
prompt.

## Tests import rule

Test modules must not import each other. Shared fixtures and builders live in
`tooling/tests/_tooling_fixtures.py` and
`skills/cometweb-context/tests/_context_fixtures.py`. The suite runs under
pytest's `importlib` import mode, so test basenames do not have to be unique
across skills — but a test module that imports a sibling will not collect.

## Releases

Build a deterministic, scanned package for a skill:

```bash
uv run python tooling/package_skill.py <skill-id>
```

Publication is approval-gated per skill and has no safety-scan bypass; see
`tooling/publish_public_dry_run.py`.
