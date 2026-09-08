# Routing eval suite

Structured cases for cross-skill **implicit routing** before `SKILL.md` loads.

Each case in `suite.json`:

- `prompt` — user message
- `expected_primary_skill` — skill that should win
- `allowed_secondary_skills` — acceptable co-triggers
- `must_not_trigger` — skills that must not be primary
- `reason` — routing rationale for reviewers

CI validates schema and coverage (including the Product Operator / Repo to
Roadmap / Release Readiness collision set). LLM routing accuracy is measured
operator-side by replaying prompts against your host's skill picker.

Target: grow toward 100–200 cases; current suite is the v1 seed set.
