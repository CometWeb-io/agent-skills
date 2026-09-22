# State machine

States are evidence-backed observations, not motivational labels.

- `CONTRACTED`: executable brief/policy exists.
- `DRAFTED`: candidate exists and is bound to a contract.
- `REVIEWED`: constructive review completed for the current candidate.
- `ROASTED`: required adversarial profile completed for the current candidate.
- `REPAIRING`: accepted findings are being addressed.
- `VERIFIED`: repairs have fresh candidate-bound verification.
- `ACCEPTED`: required knowledge-artifact acceptance gates passed.
- `LEARNING`: observations are eligible for feedback-integration analysis.

Never infer a later state from an earlier one. A new candidate version invalidates candidate-bound review/roast/repair evidence unless a delta rule explicitly preserves it.

Operational statuses:

- `READY_FOR_NEXT`
- `NEEDS_RECONCILIATION`
- `BLOCKED`
- `COMPLETE`
- `INVALID`
