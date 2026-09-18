# Security Policy

## Reporting a vulnerability

Report privately — do not open a public issue.

- Preferred: [GitHub private vulnerability reporting](https://github.com/CometWeb-io/agent-skills/security/advisories/new)
- Email: hello@cometweb.io

Please include the affected version or commit, what an attacker gains, and the
smallest reproduction you have. We aim to acknowledge within 5 working days.

## Supported versions

The `main` branch is supported. Fixes land on `main` first; older tags are not
patched.

## What this repository does and does not protect

These are agent **skill packages**: instructions, schemas, validators and
deterministic scripts. They do not run as a privileged service, and they hold
no credentials.

Security-relevant properties this repo does enforce:

- **Leak gate.** `tooling/public_safety.py` scans tracked files, and with
  `--history` every reachable commit, for secrets, private filesystem paths and
  forbidden filenames. It is fail-closed: a scan that cannot complete blocks the
  release rather than reporting success.
- **No bypass.** Publication is gated per skill by explicit approval. There is
  no flag that skips the safety scan; attempting one exits non-zero.
- **Packages are scanned and deterministic.** `tooling/package_skill.py` refuses
  unsafe filenames, path-escaping entries, case-insensitive collisions and
  oversized inputs before anything is packaged.
- **Local bindings.** Real paths into private locations are never committed;
  tracked files carry placeholders and untracked `*.local.json` / `*.local.txt`
  overlays supply the values.

What is explicitly **not** in scope:

- Whether a model, host or connector behaves correctly at runtime. The checks
  prove deterministic contracts and repository consistency, not model output.
- Side effects at the host boundary. A skill may prepare a draft, decision or
  handoff; authorization and execution belong to the host.
- Third-party hosts, marketplaces and connectors that distribute or load these
  skills.

## Reporting something that is not a vulnerability

Broken links, stale docs, failing checks and routing mistakes belong in normal
issues. If you are unsure whether a finding is sensitive, report it privately
and we will move it if it is not.
