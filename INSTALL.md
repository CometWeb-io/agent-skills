# Install

Canonical private repo: `MaciejZet/agent-skills`.

```bash
./scripts/install-all.sh
# or individually:
./scripts/install-cursor.sh
./scripts/install-claude.sh
./scripts/install-codex.sh
```

Skills are discovered from `skills/*/SKILL.md` (includes `cometweb-context`).
Cursor also links `docs/generated-cursor-routing.mdc` as the routing rule.

Public distribution mirror remains `MaciejZet/agent-skills` — sync with:

```bash
python3 tooling/publish_public_dry_run.py
python3 tooling/sync_public_repo.py --public-root ../agent-skills   # dry-run
python3 tooling/sync_public_repo.py --public-root ../agent-skills --apply
```
