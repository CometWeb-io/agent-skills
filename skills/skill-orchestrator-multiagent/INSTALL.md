# Installation — skill-orchestrator-multiagent v1.1.2

Requires a host with **subagent / Task** support (e.g. Cursor Agent) and the
`skill-orchestrator` package installed in the same host. This is an alias, not
a standalone replacement for the canonical orchestrator. For single-thread
workflows use `skill-orchestrator` instead.

Install alongside other CometWeb skills (recommended):

```bash
./scripts/install-cursor.sh
```

To install only the orchestration pair from a repository checkout, link both:

```bash
mkdir -p ~/.cursor/skills
ln -s "$(pwd)/skills/skill-orchestrator" ~/.cursor/skills/skill-orchestrator
ln -s "$(pwd)/skills/skill-orchestrator-multiagent" ~/.cursor/skills/skill-orchestrator-multiagent
```

For extracted ZIP packages, place both extracted skill directories in the
host's skills directory. The envelope validator also needs the Python package
listed in `requirements.txt`; the ZIP includes its schema but cannot install
Python dependencies into the host. For a one-off validation from this skill's
directory, use:

```bash
uv run --no-project --with 'jsonschema>=4.18,<5' python scripts/validate_envelope.py /path/to/envelope.json
```

Without `jsonschema`, validation fails closed. A host still needs an actual
Task/subagent API; structural package checks do not verify that capability.

## Invoke

```text
@skill-orchestrator-multiagent — Multiagent: verify pricing claims, then Council GO/NO-GO.
```

Run payload builder:

```bash
python3 scripts/orchestrate_multiagent_kernel.py "<goal>" --json --workspace-root "$(pwd)"
```
