# OpenAI marketplace distribution

This repository is the canonical source for the CometWeb skills tree. The
OpenAI marketplace layer points at that same tree; it does not copy skills into
a second `plugins/` directory.

## Repository shape

```text
.agents/plugins/marketplace.json  # repository marketplace catalog
plugin.json                       # portable plugin manifest
skills/<skill-name>/SKILL.md      # canonical skill packages
registry/skills.json               # routing and compatibility metadata
```

The marketplace entry uses `source.path: "./"`, relative to the repository
root. This is intentional: `skills/` remains the only skill payload and the
registry remains the metadata source of truth.

## ChatGPT workspace import

A workspace admin can import the public marketplace from:

```text
https://github.com/CometWeb-io/agent-skills
```

Use an empty Path so the client reads `.agents/plugins/marketplace.json` from
the repository root. Leave Branch empty to follow the repository default
branch, or enter `main` to make that choice explicit. Do not enter a commit SHA
if the marketplace should receive future commits.

OpenAI performs marketplace sync daily. After a push, an admin can use
**Workspace settings → Plugins → Marketplaces → Sync now** for an immediate
refresh request. The imported plugin keeps workspace installation and app
policies in ChatGPT; repository JSON does not grant members access to apps or
connections.

## Codex Desktop and local development

The same `.agents/plugins/marketplace.json` is a repository-scoped marketplace
for ChatGPT Desktop and Codex. Open the repository in the client, restart the
client after manifest or skill changes, and install the listed plugin from the
local marketplace. The existing `scripts/install-*.sh` installers remain
supported for hosts that use `~/.<host>/skills`; the marketplace does not
replace that local compatibility path.

## Update contract

```text
edit skills/ or registry/
  → local validation
  → commit and push main
  → GitHub-backed marketplace daily sync
  → Sync now when an immediate refresh is needed
```

The repository does not add a GitHub Actions workflow for marketplace syncing.
The marketplace service owns the daily refresh, while the existing validation
workflow remains the quality gate for changes merged to `main`.
