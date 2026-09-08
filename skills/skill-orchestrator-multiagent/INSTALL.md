# Installation — skill-orchestrator-multiagent v1.0.0

Requires a host with **subagent / Task** support (e.g. Cursor Agent). For
single-thread workflows use `skill-orchestrator` instead.

Install alongside other CometWeb skills (recommended):

```bash
./scripts/install-cursor.sh
```

Or symlink only this skill:

```bash
ln -s "$(pwd)/skills/skill-orchestrator-multiagent" ~/.cursor/skills/skill-orchestrator-multiagent
```

## Invoke

```text
@skill-orchestrator-multiagent — Multiagent: verify pricing claims, then Council GO/NO-GO.
```

Run payload builder:

```bash
python3 scripts/orchestrate_multiagent_kernel.py "<goal>" --json --workspace-root "$(pwd)"
```
