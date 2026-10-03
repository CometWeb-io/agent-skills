# Contributing

Thanks for improving CometWeb Agent Skills. This repo optimizes for
**evidence-backed, tested skills** — not prompt volume.

## The flow

```bash
uv sync --group dev                            # 1. once; needs uv and Python 3.12+
# 2. make the change
uv run python tooling/check_all.py --fix --fast    # 3. the inner loop: regenerate, quick gates (~10 s)
uv run python tooling/check_all.py                 # 4. before you push: every gate, as CI runs them (~3 min)
```

Run step 3 after every change; it is the loop that is meant to be fast. It
includes the per-skill slice of the test suite (eval harnesses, the front-door
and untrusted-content rules, script CLIs, manifest versions), so a skill change
that passes it rarely fails step 4. To run one skill's own tests as well:
`uv run pytest skills/<skill-id>`.

`tooling/check_all.py` is the only gate list. CI calls it with `--ci`, and a
test fails if the workflow grows a gate of its own, so a green local run means
the same checks CI will run. It runs gates in parallel, prints a summary table,
and exits non-zero if any gate fails or if a gate modified the checkout.

| Option | Effect |
| --- | --- |
| `--fast` | Leave out the full pytest suite (its per-skill slice still runs), eval strength, the plugin-version record, package builds, the history leak scan, semgrep (`sast`) and `pip-audit` |
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
README catalog row, three positive and two negative routing cases, an eval
harness that pins a small output-contract validator, and this skill's rows in
the context and eval-strength baselines (no other skill's rows are
re-recorded). `--no-register` writes the package only. Everything it writes is
a placeholder that works. Replace it in this order:

1. **Write the skill.** Replace the template text in `skills/my-new-skill/SKILL.md`
   and `references/output-contract.md`; keep `SKILL.md` short, depth goes in
   `references/`. A changed description goes into `registry/skills.json` as
   well; `validate_repo.py` compares the two.
2. **Make the evals real.** Replace `scripts/output_contract.py` and
   `evals/cases.json` with the skill's real rules, one case per rule, pinning
   the exact error list. `eval_strength.py` replaces each `if` guard in the
   modules the harness imports with `if False:`, one at a time, and fails a
   harness that still passes; rules written inside `run_evals.py` itself are
   never measured, and a harness that holds no guard fails the suite. Keep
   `references/contract.json` in step: it lists every payload field and enum
   once, and `tooling/skill_contracts.py` fails when the validator, the
   reference or an eval case disagrees with it.
3. **Make routing real.** Replace the `my-new-skill-scaffold-*` cases in
   `evals/routing/suite.json` and the `routing_signals`, `owns` and trigger
   examples in `registry/skills.json`. Each skill needs three prompts it must
   claim and two it must not; [docs/ROUTING.md](docs/ROUTING.md) explains how
   they are scored.
4. **Bump the plugin version.** A new skill changes what the plugin ships:
   `uv run python tooling/plugin_release.py --bump minor`. See
   [Plugin version](#plugin-version).
5. **Regenerate and run every gate** with the [flow](#the-flow) above. A grown
   front door or a changed eval-strength count is accepted deliberately; the
   summary prints the command that records it.

## Adding a routing eval case

Add the case to `evals/routing/suite.json`. Routing signals are read from
`registry/skills.json` only — there is no second signal list in the runner. Use
`"expected_primary_skill": null` to assert that **no** skill should claim a
prompt. Every active skill needs at least three positive cases and two that
forbid it. [docs/ROUTING.md](docs/ROUTING.md#adding-a-case) covers reproducing a
route and where each kind of case belongs.

## Registry and generated files

`registry/skills.json` is the source of truth for descriptions, versions,
ownership boundaries and routing signals. Entries for the skills listed in
`OVERRIDES` in `tooling/sync_skill_registry.py` are generated from that table:
edit `OVERRIDES`, not the registry. Never hand-edit generated output: the
adapters, the `docs/generated-*` tables, the host routing files
(`extras/cursor-routing.mdc`, `extras/AGENTS.snippet.md`,
`rules/cometweb-agent-skills.mdc`), `.cursor-plugin/plugin.json` (the Claude
manifest restricted to Cursor's documented keys), each skill's
`agents/openai.yaml` interface block (its `short_description` is built to fit
the 25-64 characters Codex shows, and its `default_prompt` is one sentence that
invokes the skill as `$skill-id`), the README skill catalog and every skill
count in the README, and the package list in the host plugin manifests all
come from the registry and `registry/readme-catalog.json` via `--fix`. When
wording that carries a generated number is rewritten so the generator can no
longer find it, `generate_adapters.py` stops with an error rather than leaving
a stale number behind.

## Skill quality bar

| Expectation | CometWeb bar |
| --- | --- |
| `SKILL.md` only | + scripts and/or schemas where claims are enforceable |
| No tests | pytest for kernels and validators, or a `skills/<name>/scripts/run_evals.py` harness |
| Vague routing | Explicit negatives in the description + a routing eval case |
| Silent handoffs | CW-AIP envelope fields in the output contract |

**Offline behavior suite.** Every skill that ships a script also has
`evals/behavior/<skill>/suite.json` (schema `cometweb.behavior-suite/v1`):
cases that run the skill's scripts the way its references tell a user to, or
call a documented library function with `"call"` and `"args"`, and pin the exit
code plus exact JSON values or output text. Each case states the behaviour it
holds and is tagged `accept`, `refuse` or `boundary`; a suite needs at least
three cases, one accepted and one refused. `tooling/run_behavior_evals.py`
fails for a skill without one (`--coverage` lists counts, `--skill ID` runs one).

Harnesses in `scripts/run_evals.py` run under pytest through
`tooling/tests/test_skill_eval_harnesses.py`; the eval-strength baseline is the list
of skills that must ship one.

**One contract per skill.** A skill that ships a script declares its payload in
`references/contract.json`: every field, every enum bound to the script constant
that enforces it, the reference that documents it, and the eval corpora whose
inputs must conform. `tooling/skill_contracts.py --check` fails when a script
reads an undeclared key, an enum drifts, the reference names a field the
contract lacks (or omits one it has, or spells an enum value differently), or an
eval case expects a pass on off-contract input. A key a script reads that is
not a payload field goes under `internal` with the reason (`{"name": "why"}`);
when one key carries different enums in rows passed whole by argument, declare
each row set under `lists` and qualify the field by it (`forecasts.outcome`).
Start one with `tooling/skill_contracts.py --draft <skill>`; its module
docstring lists the keys.

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

Hosts cache an installed plugin under the `version` in its manifest and
replace it only when that version changes ([INSTALL.md](INSTALL.md#plugin-marketplaces)
shows what a user sees). A skill change merged without a plugin version bump
therefore never reaches anyone who installed the plugin.

The rule: any change to the **shipped skill set** (a package added, removed or
renamed under `skills/`) or to **any skill's `VERSION`** bumps the plugin
version in the same pull request.

- Patch for fixes only; minor when a skill gains behaviour or a skill is added;
  major when a skill is removed or renamed, or a contract breaks.
- One value everywhere: `VERSION`, `pyproject.toml`, `uv.lock`, `plugin.json`,
  `.claude-plugin/plugin.json` and `.cursor-plugin/plugin.json`. One command
  writes all six and records the shipped set:

```bash
uv run python tooling/plugin_release.py --bump patch   # or minor / major
uv run python tooling/plugin_release.py --check        # check_all runs it with --require-base under --ci
```

`--bump` counts from the version at the merge base with `origin/main`, so
rerunning it on a branch does not bump twice, and `--bump minor` after an
earlier `--bump patch` on the same branch lands on the minor version.
`--record` alone re-records the shipped set without touching any version.

`registry/plugin-release.json` holds the plugin version and every shipped skill
with its `VERSION`. `--check` fails when the tree differs from that record, and
also compares against the merge base with `origin/main`: if the shipped set
changed there, the plugin version must be greater than the base's, so editing
the record in place does not get around it. `--record` refuses to record a
different skill set under a version that was already recorded.

## Releases

A release is a `v*` tag on `main`. Pushing the tag runs
[`attest-packages.yml`](.github/workflows/attest-packages.yml), which refuses a
tag that does not equal `v` + `VERSION`, revalidates the tree, builds one
deterministic `skill.zip` per skill, writes a CycloneDX SBOM of the plugin,
attests both with Sigstore build provenance and uploads them as a workflow
artifact. Nothing is published to a registry.

1. Merge the pull request that bumped the plugin version (see
   [Plugin version](#plugin-version)) and passed every gate.
2. Rehearse the packaging locally on a clean checkout of that commit. These are
   the workflow's own build steps; they write only under `dist/`, which is
   ignored:

   ```bash
   uv run python tooling/check_all.py --ci        # every gate; the tag workflow reruns them
   for skill in skills/*/SKILL.md; do
     uv run python tooling/package_skill.py "$(basename "$(dirname "$skill")")"
   done
   uv run python tooling/sbom.py --dist dist --output dist/agent-skills.cdx.json
   ```

3. Tag and push: `git tag "v$(cat VERSION)" && git push origin "v$(cat VERSION)"`.
4. When the workflow finishes, download the `agent-skills-packages` artifact
   and verify a package: `gh attestation verify skill.zip --repo CometWeb-io/agent-skills`.

Packages built with `package_skill.py --dev` go under `dist/<skill>/dev/` and
are never attested. For a recorded evidence report of a local run (per-check
logs, JUnit, source fingerprints) use `tooling/validate_local.py`; see
[docs/LOCAL-VALIDATION.md](docs/LOCAL-VALIDATION.md). A file removed from `HEAD`
stays in history until that history is rewritten, which is why `check_all.py`
scans every reachable commit for leaks.

Longer-form background lives in [`docs/`](docs/README.md).
