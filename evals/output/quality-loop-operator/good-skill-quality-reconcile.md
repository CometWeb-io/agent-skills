# Quality Run Brief — invoice-summarizer@1.4.0

## STATE

NEEDS_RECONCILIATION

- Run: `qr-2026-10-03-02`, profile SKILL_QUALITY, mode DEEP
- Candidate: `invoice-summarizer@1.4.0`
- Contract: `skill-contract-invoice-summarizer`
- as_of: 2026-10-03T09:15:00+02:00
- `scripts/kernel.py` on the sidecar below: NEEDS_RECONCILIATION, next stage finding-reconciliation, 1 unresolved conflict.

| Stage | State | Evidence |
| --- | --- | --- |
| skill-auditor | PASS | static audit of 1.4.0, no blocking finding |
| rubric-designer | PASS | rubric_hash `e3b0c442…b856` |
| benchmark-curator | PASS | benchmark_hash `91726bcd…c4b4`, READY_TO_FREEZE |
| skill-evaluator | PENDING | not started |

## POLICY LOCK

- Pack `skill-quality` revision 2.0.1, sha256 `0a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f9`, locked before evaluation.

## CONFLICTS

- RC-01 — CONFLICT, unresolved. The skill auditor rates the missing currency guard MINOR (documentation only); the benchmark curator's adversarial case BC-03 treats it as a behavioral failure. Neither severity is adopted by default.

## MEASUREMENT

- Rubric `e3b0c442…b856` and benchmark `91726bcd…c4b4` are bound and consistent. No paired or stability result exists yet, because evaluation has not run.

## RUNTIME LIFECYCLE

- NOT_REQUESTED. No rollout is being asked for in this run.

## NEXT STAGE

finding-reconciliation, then `skill-evaluator`.

## REVALIDATE

- `skill-evaluator` only, after RC-01 is settled. The rubric and benchmark stay as frozen unless the resolution changes a criterion, which would be a new policy revision.

## BLOCKER

- RC-01 is unresolved. Resolve it with a targeted reproduction of BC-03 on 1.4.0, not by picking the harsher severity.

## DONE WHEN

Done when RC-01 has a recorded basis, `skill-evaluator` is PASS with an IMPROVED or NO_MATERIAL_CHANGE result bound to the same rubric and benchmark hashes, and the lock still matches.

```json
{
  "schema": "cometweb.quality-loop/v1",
  "run_id": "qr-2026-10-03-02",
  "profile": "SKILL_QUALITY",
  "mode": "DEEP",
  "as_of": "2026-10-03T09:15:00+02:00",
  "candidate_id": "invoice-summarizer@1.4.0",
  "contract_id": "skill-contract-invoice-summarizer",
  "policy_lock": {"pack_id": "skill-quality", "revision": "2.0.1", "sha256": "0a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f9", "locked_before_evaluation": true},
  "stages": [
    {"skill": "skill-auditor", "state": "PASS"},
    {"skill": "rubric-designer", "state": "PASS", "rubric_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b856"},
    {"skill": "benchmark-curator", "state": "PASS", "rubric_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b856", "benchmark_hash": "91726bcd345c02d670ae2d263c57ebb005bb85ad41933f6df627ea1ba3c6c4b4"},
    {"skill": "skill-evaluator", "state": "PENDING"}
  ],
  "reconciliation": [
    {"status": "CONFLICT", "resolved": false}
  ],
  "runtime_lifecycle": {"state": "NOT_REQUESTED"},
  "coverage": "static audit, rubric and benchmark done; evaluation not started",
  "revalidate": ["skill-evaluator"],
  "completion_evidence": []
}
```
