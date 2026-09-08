# Public / private pipeline

## Intent

| Repo | Role |
| --- | --- |
| `MaciejZet/agent-skills` (private) | Canonical source |
| `MaciejZet/agent-skills` (public) | Public-safe distribution mirror |

## Status

- **Tooling: done** — `publish_public_dry_run.py`, `sync_public_repo.py`, `public-safety-check.sh`
- **Automation: not done** — no GitHub Action that opens the PR yet; operator runs sync and opens PR

## Operator publish steps

```bash
python3 tooling/validate_repo.py
python3 tooling/compatibility.py
python3 tooling/run_routing_evals.py
python3 tooling/run_behavior_evals.py
python3 -m pytest -q
python3 tooling/publish_public_dry_run.py
python3 tooling/sync_public_repo.py --public-root /path/to/agent-skills --apply
cd /path/to/agent-skills
./scripts/public-safety-check.sh
# review diff → commit → open PR
```

Until Actions automation exists, cherry-pick critical host fixes (e.g. description ≤1024) if public installs must stay green.
