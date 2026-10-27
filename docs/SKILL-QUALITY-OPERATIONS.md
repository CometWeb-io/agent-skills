# Skill quality and evaluation

The repository separates deterministic repository evidence from runtime claims.

## What CI proves

The default checks cover:

- registry ↔ package identity and version consistency;
- portable skill frontmatter and host compatibility metadata;
- relative resources and generated adapters;
- routing and deterministic behavior fixtures;
- Python compilation, unit tests, and public-safety scanning.

These checks do not prove that every model, host, connector, or full workflow
will produce a correct result. Provider-backed and human-reviewed evaluations
must be reported separately with the exact host, model, inputs, capabilities,
and review scope.

## Local validation

```bash
python3 tooling/validate_repo.py
python3 tooling/sync_orchestrator.py --check
python3 tooling/compatibility.py
python3 tooling/generate_adapters.py --check
python3 tooling/run_routing_evals.py
python3 tooling/run_behavior_evals.py
python3 tooling/public_safety.py --root .
python3 -m pytest -q tooling/tests skills/*/tests
```

Before a release, also inspect reachable history:

```bash
python3 tooling/public_safety.py --history
```

## Diagnostics outside CI

`registry/knowledge-rules.json` records bounded claims, sources, verification
findings and TTLs. A `verification` binds a real source read to `verified_at`:
keep its URL, section locator, assessment and short finding. Change that date
only after reading the source. Documentation evidence establishes the recorded
requirement; it does not establish native host execution or model quality.

```sh
uv run python tooling/check_knowledge.py registry/knowledge-rules.json
uv run python tooling/check_knowledge.py registry/knowledge-rules.json --as-of 2026-12-01 --strict
uv run python tooling/doctor.py ai-council
```

The checker fetches nothing and changes no files. `within_ttl` means a current
record, not a verified live claim. Expiry is reported as `status: stale`
(retained for existing consumers), `freshness: expired` and
`review_status: needs_review`. At exactly TTL days the record is still current;
it expires the following day. Future dates, withdrawn and unverified rules also
need review. A separate `contradiction` needs `observed_at`, an HTTPS `url` and
an explanatory `note`; only that recorded evidence yields
`claim_truth: recorded_contradiction`. Neither TTL expiry nor a missing test is
a contradiction. Supporting source reads and contradictory findings are both
recorded reports, never independently authenticated observations.

Rule dependencies name skill IDs (`["*"]` means the current catalog), generated
adapter path templates (`skills/*/agents/openai.yaml`) and repository tooling.
The CLI resolves skill versions from the sibling `registry/skills.json` without
copying the catalog. Adapter templates expand per selected skill; this is a
dependency map, not an existence or execution check. The report preserves each
rule's links and summarizes only the skills/adapters requiring review. Existing
SEO `live-source-registry.json` group registries remain consumable without
rewriting dates or duplicating their claims. Direct `audit()` consumers without
a catalog get `declared_only` dependencies.

`.github/workflows/knowledge-freshness.yml` runs weekly (Monday 07:17 UTC) or
manually, with read-only repository permissions and no persisted checkout
credentials. It uploads a dated JSON report as an Actions artifact for 30 days.
It does not fetch sources, refresh dates, post issues/comments, or send messages.
Expiry is reportable without failing unrelated PRs: this workflow has no PR
trigger, and its non-strict checker exits 0 on review findings. Invalid input
still exits 2; local `--strict` exits 1 on any review finding. Review the artifact
and read only the sources material to the affected change before updating a rule.

Doctor reports catalog version, registry hash, skill visibility, source version
and entrypoint hash alongside package and optional installation comparisons.
Host targets are declarations; adapter files are `present_unverified`.
Knowledge freshness is a separate advisory field and does not change the
installation issue exit code. Missing CLI or installation says nothing about
model competence (`unknown`). `native_execution: not_run` and
`runtime_acceptance: not_assessed` remain neutral even with a reported session
inventory. Public diagnostics contain no private repository paths or credentials;
keep private source overlays and run artifacts outside public tracked files.

## Runtime and side-effect boundary

A host may load a skill while lacking browser, filesystem, code-execution, or
connector access. Missing capabilities lower the result's coverage; they do
not justify fabricated state.

Skills can draft structured outputs and CW-AIP handoffs. The host owns
authorization and external mutations. Any connector-backed benchmark must say
whether it only read data, prepared a draft, or performed an approved write.

## Evaluation discipline

- Do not present test counts as a quality score.
- Do not call a synthetic fixture a provider run.
- Do not call a text-only model test a browser, connector, installation, or
  production acceptance test.
- Keep baseline, candidate, task, capability budget, model, and reviewer scope
  comparable when measuring a change.
- Report unknown, unavailable, blocked, and not-run states explicitly.

## Public boundary

Do not commit credentials, customer data, private runtime bindings, internal
strategy memos, outreach playbooks, or raw private documents. Use placeholders
and local ignored overlays when a skill needs environment-specific values.
