# Formal counterevidence check

Use this reference for v6 structured reports. Ordinary prose uses the checklist in `SKILL.md`; no role simulation or multiple personas are required.

Before admitting a material finding, bind it to source evidence and search the reviewed scope for qualifications, proof, sequencing or alternative explanations that could defeat it. Record the search and what was actually found, including a bounded explanation if no counterevidence was found.

For BLOCKER and MAJOR, populate `falsifier_check`:

- `challenge`: the bounded failure claim being tested;
- `searched_for`, `counterevidence`, `alternative_explanations`: actual inspection and results;
- `result`: `SURVIVES`, `DOWNGRADED`, `WITHDRAWN`, or `UNRESOLVED`;
- `notes`: why the result follows from the evidence.

Remove withdrawn findings. A downgrade uses the final lower severity and records `downgraded_from`. Unresolved candidates cannot have high confidence; move unsupported defects to verification questions. Weak evidence or high sensitivity to unseen context excludes BLOCKER and high confidence.

Link `source_manifest -> evidence_register -> evidence_refs -> finding`; evidence must include the anchor's source. Record unresolved contradictions in `evidence_conflicts` and lower confidence or the evidence gate accordingly. An omission needs sufficient inspected scope, not a failed search alone.

Apply `references/evidence-discipline.md` and `references/severity-calibration.md` for formal field semantics. A repair needs a check that can distinguish fixed from unfixed. Multiple symptoms with the same cause and repair belong together.
