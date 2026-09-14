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
