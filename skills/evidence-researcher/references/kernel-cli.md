# Evidence kernel CLI

Deterministic helpers for validation — not fact discovery.

```bash
python3 scripts/evidence_kernel.py template --question "..." --as-of "2026-01-01T12:00:00+00:00" --mode STANDARD
python3 scripts/evidence_kernel.py canonical-url --url "https://example.com/a?utm_source=x#section"
python3 scripts/evidence_kernel.py make-id --kind source --value "..."
python3 scripts/evidence_kernel.py source-policy --claim-type vendor_policy
python3 scripts/evidence_kernel.py temporal --source-json '{...}' --claim-type vendor_policy --as-of "..."
python3 scripts/evidence_kernel.py fingerprint-source --source-json '{...}'
python3 scripts/evidence_kernel.py pack-hash --ledger-json evidence.json
python3 scripts/evidence_kernel.py validate --ledger-json evidence.json
python3 scripts/evidence_kernel.py coverage --ledger-json evidence.json
python3 scripts/evidence_kernel.py audit --ledger-json evidence.json
python3 scripts/evidence_kernel.py refresh-plan --ledger-json evidence.json
python3 scripts/evidence_kernel.py delta --old-ledger-json old.json --new-ledger-json new.json
python3 scripts/evidence_kernel.py stop --ledger-json evidence.json --no-novelty-rounds 2 --expected-information-gain 0.1 --research-cost 0.2
python3 scripts/evidence_kernel.py migrate-v1 --ledger-json old.json
```

Review migrated falsifier/search records before high-stakes use. See `migration-v1-v2.md`.

## Explicit automation gate (kernel 2.0.1)

```bash
python3 scripts/evidence_kernel.py audit --ledger-json evidence.json --require-ready
```

With `--require-ready`, exit 0 means the deterministic research gate is READY; exit 1 means a validly processed result is not READY; exit 2 means input/processing failed. Ordinary `audit` keeps its legacy report-only exit policy: inspect the JSON, not only process success. Neither result authorizes a business decision or proves source authenticity.

Zero-cache temporal checks accept `--research-id` and `--research-started-at`; full ledger commands read `research_id` and `research_contract.started_at`. See [freshness.md](freshness.md) for migration and admission rules. Missing verification data must be gathered, not generated to satisfy validation.

`refresh-plan.dependent_claim_ids` lists dependent inferences affected by source refresh. The kernel does not execute refresh work. A migrated v1 falsifier flag is only historical metadata; its reminder is incomplete until a real search is performed and recorded.
