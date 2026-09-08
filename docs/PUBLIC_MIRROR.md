# Public / private pipeline

## Intent

| Repo | Role |
| --- | --- |
| `MaciejZet/agent-skills` (private) | Canonical source: registry, bindings, private context, full evals |
| `MaciejZet/agent-skills` (public) | Public-safe distribution mirror |

Do **not** hand-maintain divergent skill logic in both places once the publish pipeline is live.

## Publish steps (P2 automation target)

1. `python3 tooling/validate_repo.py && python3 tooling/compatibility.py`
2. `python3 tooling/run_routing_evals.py && python3 tooling/run_behavior_evals.py`
3. `python3 -m pytest -q`
4. Run `scripts/public-safety-check.sh` equivalent (strip private vault paths, customer data, Notion bindings, internal URLs that must stay private)
5. Sync allowlisted paths into a checkout of `agent-skills`:
   - `skills/<public-safe>/`
   - `protocol/` (v1 + v2 public schemas)
   - `evals/routing/` (without private-only cases if any)
   - install scripts / site docs
6. Open PR on public repo; never force-push `main`

## Allowlist notes

- `cometweb-context` source-registry **templates** may publish; live customer bindings must not.
- Council Notion binding examples stay `.example.json` only.
- GTM/promotion docs stay in `<COMETWEB_GTM_ROOT>`, never in either skills repo.

## Interim (now)

Until the pipeline exists: critical compatibility fixes (e.g. description ≤ 1024) may be
cherry-picked into public `platforms/agent-skills` so live Cursor/Claude installs stay
host-safe. Canonical development continues here.
