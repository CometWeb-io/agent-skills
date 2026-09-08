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
