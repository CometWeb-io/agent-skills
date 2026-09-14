# Skill quality: build, verify, evaluate

## Evidence levels

A source file, valid ZIP, host discovery, session visibility and a successful model
execution are different observations. Never promote one into another. Unit tests
of runner contracts are not LLM evaluations. A text-only API experiment is not a
browser, connector, installation or complete skill-workflow acceptance test.

The canonical skill metadata remains `registry/skills.json`. Admission constraints
live in `registry/routing-policy.json`; it does not duplicate descriptions or
versions. Shared package rules are in `registry/package-policy.json`.

## Local development and CI

```bash
python3 -m pip install -r requirements-dev.txt
python3 tooling/validate_repo.py
python3 tooling/sync_orchestrator.py --check
python3 tooling/compatibility.py
python3 tooling/generate_adapters.py --check
python3 tooling/run_routing_evals.py
python3 tooling/run_routing_evals.py --legacy-signals
python3 tooling/run_behavior_evals.py
python3 tooling/run_model_evals.py
python3 tooling/publish_public_dry_run.py
python3 -m pytest -q tooling/tests skills/*/tests
```

Generate adapters intentionally before committing, not before checking them in CI.
The generator preserves extension fields and existing MCP dependencies; explicitly
set `tool_dependencies` in a registry entry to replace that list. Compatibility
checks validate actual YAML, reject duplicate keys and enforce the common 1-1024
character description range. Optional interface recommendations are warnings;
`compatibility.py --strict` makes warnings blocking. Neither mode tests a host.

The default routing gate enforces explicit invocation, narrow-intent exclusions,
no-skill and ambiguous outcomes. `--legacy-signals` is retained as a clearly labelled
historical keyword-proxy diagnostic, not invocation-policy acceptance. Pass only
the user's task to the classifier, never retrieved page text. Regex routing is not
a security boundary or an evaluation of the host model's own routing.

## Private packages

```bash
python3 tooling/package_skill.py evidence-researcher --versioned
python3 tooling/doctor.py evidence-researcher
```

Every build is versioned; the old `--versioned` option remains compatible. Unexpected
files, secrets, local configuration, symlinks, unsafe paths and unresolved bundled
resources block the build. Explicitly permitted shared `protocol` resources are
vendored into `references/_shared`, with local links checked after relocation.

Each ZIP carries `PACKAGE-MANIFEST.json`: file hashes, payload/policy fingerprints,
source revision when observable and an explicit runtime `not_assessed` status.
The same version cannot be overwritten with different payload bytes. Rebuilding an
identical version reuses its existing archive. Bump VERSION and registry version
when skill contents change. Source/installation checksums are not signatures.

## Public export: default deny

`registry/public-allowlist.json` intentionally starts with no approvals. Active
lifecycle and private-canonical visibility do not authorize public distribution.
A reviewer must approve each exact `{id, version, payload_sha256}` tuple after
reviewing content and license rights. Compute the payload with the private packager;
do not invent the hash or copy a receipt from a different revision.

```bash
python3 tooling/publish_public_dry_run.py
python3 tooling/public_safety.py --root dist/public-mirror
python3 tooling/sync_public_repo.py --public-root /absolute/path/to/agent-skills
```

With no approvals, export reports `disabled` and creates no replacement mirror.
After approval, the staged tree is scanned in full, compared to approved current
source bytes and atomically installed. Any scanner error blocks the operation.
Changing source or revoking approval invalidates the export. Receipt rewriting
cannot bless tampered bytes. There is no safety-skip option.

`sync_public_repo.py` is dry-run by default. `--apply` requires a clean, separate
checkout with the expected public origin, revalidates approvals even with
`--skip-rebuild`, preserves unrelated files and does not push. It deliberately
avoids deleting entire public directories. Review stale files separately.

The shell checker accepts an explicit `--root`; it never silently scans its own
repository instead. `--history` checks reachable historical blobs including deleted
files. Public scans of the private canonical source are expected to flag private
bindings; scan the actual intended public artifact. Findings never echo secrets.

## Diagnose installation without inventing runtime state

```bash
python3 tooling/doctor.py ai-humanize --installed-root /absolute/skills/path
python3 tooling/doctor.py ai-humanize --session-inventory /private/session.json
```

The installed root contains `<skill>/SKILL.md`. The optional session JSON requires
`schema: cometweb.session-inventory/v1`, host, session_id, a timezone-aware observed_at
and an explicit skills list. It remains reported evidence, not authenticated host
telemetry. Without an inventory, discovery and visibility remain unknown. The doctor
detects package corruption, same-version source drift and installed-byte drift;
it does not install plugins or repair sessions automatically.

## Real baseline/current/candidate experiments

`evals/model/suite.json` contains 16 synthetic task scenarios across six skills.
Three conditions require 48 executions per repetition. By default the runner only
validates/inventories cases and reports `not_run`, with zero model calls.

The included OpenAI adapter performs stateless Responses API calls with storage
explicitly disabled and no tools. Configure `OPENAI_API_KEY` privately and set
`COMETWEB_EVAL_MODEL` to an explicitly chosen available model identifier. Never put
credentials or private customer material in tracked fixtures. Running the adapter
sends the selected skill instructions and fixtures to that configured provider.

Prepare separate frozen full repository worktrees for current and candidate, then:

```bash
python3 tooling/run_model_evals.py --execute \
  --current-root /absolute/current \
  --candidate-root /absolute/candidate \
  --runner-json '["python3", "/absolute/candidate/tooling/openai_eval_runner.py"]' \
  --output /private/evals/run-001 --max-runs 48 --max-output-tokens 2048
```

Identical current/candidate instruction bundles are rejected: changing tooling alone
is not evidence of improved skill behavior. Case `resources` selects extra reference
files loaded equally in both skill conditions. The baseline gets the same task,
fixture and capability budget but no skill instructions. Inputs are never silently
truncated. The included experiment covers only loaded text, not dynamic reference
retrieval or tool use; use a separate trusted host adapter for those experiments.

Conditions are shuffled and outputs blinded for review. A fresh process/CWD provides
context separation, not OS sandboxing. A trusted adapter must report actual host,
model, response ID, capabilities, usage and tool trace. Mocks are rejected by the
production runner. Partial failures retain records and stop further spending.
Unmatched models/hosts/capabilities are not a valid matched comparison. Literal
checks supplement, not replace, human assessment of fidelity, evidence, safety,
completeness, naturalness and cost. Keep the unblinding map away from reviewers
until their evaluations are recorded. No automated winner is declared.

## Freshness and evidence-backed rules

```bash
python3 tooling/check_knowledge.py registry/knowledge-rules.json
python3 tooling/check_knowledge.py \
  skills/seo-geo-aeo-maxxing/references/live-source-registry.json
```

The checker consumes the existing SEO source registry without rewriting dates.
It separates within-TTL, stale, future verification, unverified and withdrawn rules.
Calendar validity is not a live source recheck or proof of a proposition. New typed
rules distinguish platform requirements, standards, heuristics, observations and
experiments, and record scope, sources and regression checks. Refresh claims only
after inspecting controlling sources; never update dates merely to pass CI.

## CometWeb-specific work and exhaustive audits

Read `profiles/cometweb/PROFILE.md` for CometWeb publications. It points to one
canonical publication rule document while keeping the existing editorial standard
as supplementary guidance. It does not override another client's branding, alter
edition numbers, install fonts or turn AI Humanize into a graphic-design skill.

`tooling/validate_coverage.py` checks an explicit audit inventory and evidence ledger.
An inspected file is not a tested end-to-end flow. Unsupported, sampled, blocked
and unreviewed items remain visible. Exhaustive claims require an evidenced complete
inventory and the requested bar, not merely a large finding count. Evidence
references remain supplied data, not automatically authenticated test executions.

## Deliberately unresolved integration

`fullstack-contract-auditor` was not found in the inspected canonical main or the
searched branches. Do not recreate an unreviewed competing version: obtain the
actual package, compare its provenance/version and integrate it with regression
cases separately. Preserve the existing independent draft PR #5 rather than merging
its package updates implicitly. Never restore the retired antipattern-writing skill.

## Continuation

See `CONTRACT-TRACE-AND-SKILL-EVALS.md` for pinned path-evidence validation and the runner-to-reviewed-comparison handoff. See `CONTINUATION-2026-09-12.md` for actual scope and non-run integration gates.
