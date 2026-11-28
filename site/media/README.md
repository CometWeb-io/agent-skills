# Landing page media

Everything here was produced on 7 November 2026 from commit `c40de2e` of this
repository (plugin version 3.0.0 on `main`), on macOS with Node.js 22.23.1 and
the locked `uv` environment. Nothing is a mockup.

- The "Real answers" section quotes three real Claude Code runs with these
  skills installed (content-roaster, release-readiness, evidence-researcher).
  `skill-runs.md` has the full prompts, answers, timings and how each run was
  made. The page shows a few sentences of each answer, verbatim, plus a short
  version of each prompt.
- `transcripts.txt`: the command output quoted on the page (router answers,
  envelope validation, installer runs into a throwaway home directory, the
  example's Node tests and the test count). The throwaway home directory is
  shown as `~`, the clone path as `<clone>` and the scratch copies as
  `<scratch>`; nothing else is edited. No installer touched a real host
  directory.

## Hero and logos (added 7 Nov 2026)

- The hero is a diagram, not a recording. The four requests and what they map
  to (web-app-auditor, release-readiness, evidence-researcher and no skill) are
  the real `tooling/route_skill.py` results in `transcripts.txt`. The one-line
  descriptions on the card paraphrase each skill's `SKILL.md` description. Which
  host tile is highlighted only rotates; the router does not depend on the host.
- Host logos for Claude, Cursor and Qwen are from Simple Icons 16.36.0 and
  belong to their owners. Simple Icons has no OpenAI, Qoder or Lingma mark, so
  Codex uses a generic terminal glyph and the other two are named in text. The
  six hosts are the ones with an installer in `scripts/`.
- Strip under the hero: 9,345 is the count `pytest` collected (see
  `transcripts.txt`); 35 is the number of gates `tooling/check_all.py` ran, all
  passing, on 7 Nov 2026.
