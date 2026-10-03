#!/usr/bin/env python3
"""Run the repository's semgrep rules over tracked Python and shell files, offline.

    uv run python tooling/sast.py              # rule self-test, then the scan
    uv run python tooling/sast.py --list       # the files that would be scanned

The engine is the exact `semgrep` pinned in the `sast` dependency group of
uv.lock, run through `uv run --isolated --frozen`, so it is installed from the
lock's hashes into a throwaway environment and never changes the dev venv. The
rules are the local files in tooling/sast/; no registry rules are fetched.
Metrics and the version check are off and semgrep's settings and logs go to a
temporary directory, so nothing leaves the machine and nothing is written to
HOME. Results depend only on the tracked files, the rules and the pinned engine.

Two steps, both must pass:
1. `semgrep --test` over tooling/sast/tests: every rule fires on its `ruleid:`
   cases and stays quiet on its `ok:` cases, so a rule that silently stopped
   matching fails the gate instead of passing it.
2. The scan of every tracked *.py and *.sh outside test directories and the
   rule fixtures (the same scope bandit uses), failing on any finding.

Suppress a reviewed finding with a `# nosemgrep: <rule-id>` comment that says why.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess  # nosec B404 - fixed argv, no shell
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "tooling" / "sast"
RULE_FILES = ("python.yml", "shell.yml")
FIXTURES = RULES / "tests"
EXCLUDED_PARTS = {"tests", "fixtures"}


def tracked_targets(root: Path = ROOT) -> list[str]:
    listed = subprocess.run(["git", "ls-files", "-z", "--", "*.py", "*.sh"], cwd=root,  # nosec B603 B607
                            capture_output=True, check=True).stdout.decode()
    targets = []
    for name in sorted(filter(None, listed.split("\0"))):
        parts = Path(name).parts
        if EXCLUDED_PARTS & set(parts[:-1]) or name.startswith("tooling/sast/"):
            continue
        if not (root / name).is_file():
            continue  # deleted in the working tree, not yet committed; semgrep would exit 2
        targets.append(name)
    return targets


def semgrep_argv(*args: str) -> list[str]:
    return ["uv", "run", "--isolated", "--frozen", "--only-group", "sast", "--quiet",
            "--", "semgrep", *args]


def environment(scratch: Path) -> dict[str, str]:
    env = dict(os.environ)
    env.update({
        "SEMGREP_SEND_METRICS": "off",
        "SEMGREP_ENABLE_VERSION_CHECK": "0",
        "SEMGREP_SETTINGS_FILE": str(scratch / "settings.yml"),
        "SEMGREP_LOG_FILE": str(scratch / "semgrep.log"),
        "SEMGREP_VERSION_CACHE_PATH": str(scratch / "version-cache"),
    })
    # XDG_CACHE_HOME is left alone: uv keeps its wheel cache there, and an empty
    # cache would download the engine on every run and fail offline.
    return env


def run(argv: list[str], env: dict[str, str]) -> int:
    return subprocess.run(argv, cwd=ROOT, env=env, check=False).returncode  # nosec B603


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--list", action="store_true", help="print the scan targets and exit")
    args = parser.parse_args(argv)
    targets = tracked_targets()
    if args.list:
        print("\n".join(targets))
        return 0
    if not targets:
        print("FAIL: no tracked Python or shell files found (is this a git checkout?)", file=sys.stderr)
        return 1
    common = ["--metrics=off", "--disable-version-check", "--oss-only", "--quiet"]
    configs = [arg for name in RULE_FILES for arg in ("--config", str(RULES / name))]
    with tempfile.TemporaryDirectory(prefix="cw-sast-") as tmp:
        env = environment(Path(tmp))
        code = run(semgrep_argv("--test", *common, "--config", str(RULES), str(FIXTURES)), env)
        if code != 0:
            print("FAIL: semgrep rule self-test (tooling/sast/tests)", file=sys.stderr)
            return 1
        code = run(semgrep_argv("scan", *common, *configs, "--error", "--timeout", "60", *targets), env)
    if code == 1:
        print(f"FAIL: semgrep findings in {len(targets)} scanned files; fix them, or suppress a reviewed one "
              "with `# nosemgrep: <rule-id>` and a reason", file=sys.stderr)
        return 1
    if code != 0:
        print(f"FAIL: semgrep stopped with an engine error (exit {code}), not a finding; the scan runs "
              "with --quiet, so rerun its command from tooling/sast.py without it to see the cause",
              file=sys.stderr)
        return 1
    print(f"OK: {len(targets)} Python and shell files clean under {len(RULE_FILES)} rule files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
