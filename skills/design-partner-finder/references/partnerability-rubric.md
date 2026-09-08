# Partnerability rubric v2

## Contents

- [Stage A — Research Discovery Fit](#stage-a--research-discovery-fit)
- [Stage A gates](#stage-a-gates)
- [Stage B — Live Partner Readiness](#stage-b--live-partner-readiness)
- [Stage B gates](#stage-b-gates)
- [Diagnostic interpretation](#diagnostic-interpretation)


Use two different models. Do not collapse public research and live commitment into one score.

## Stage A — Research Discovery Fit

Rate each 0–5 from evidence available before contact.

| Dimension | Weight | High score means |
|---|---:|---|
| Problem evidence | 25 | The target pain/workflow is directly evidenced, repeated, costly, or visibly worked around. |
| Representativeness | 20 | The candidate resembles the intended market on the dimensions the Learning Contract says should transfer. |
| Urgency | 15 | A current trigger, switching event, workaround, or initiative makes action plausible now. |
| Learning value | 15 | The candidate can materially answer named Learning Contract hypotheses. |
| Implementation plausibility | 10 | Public/known evidence suggests the stack, process, data, and organization could support the intended motion. |
| Stakeholder path | 5 | A plausible professional route exists to the relevant buyer/champion/user. |
| Credibility | 5 | Material company/capability/portfolio claims are sufficiently substantiated for this decision. |
| Commercial optionality | 3 | If value is proven, a normal customer relationship is plausible. |
| Reference/network value | 2 | Success could create credible proof or distribution. Keep this a tie-breaker. |

### Stage A gates

Capture separately:

- `evidence_confidence` 0–5,
- `contradiction_risk` 0–5,
- `customization_risk` 0–5,
- `conflict_risk` 0–5,
- `professional_contact_path` boolean,
- `exploration_mode` boolean.

Apply:

1. `problem_evidence < 2` → `REJECT`, cap 49.
2. `representativeness < 2` and not exploration mode → `REJECT`, cap 49.
3. `evidence_confidence <= 1` → `HOLD_VERIFY`, cap 49 unless already rejected.
4. `credibility <= 1` → `HOLD_VERIFY`, cap 49 unless already rejected.
5. `contradiction_risk >= 4` or `conflict_risk >= 4` → `HOLD_VERIFY` until resolved.
6. `customization_risk >= 4` → cap 64 for a core-design-partner recommendation.
7. `implementation_plausibility <= 1` → cap 64.
8. No professional contact path → never `PRIORITY_DISCOVERY`.

Statuses:

- `PRIORITY_DISCOVERY` — score >=80, core fit dimensions >=3, evidence confidence >=3, no hold/reject gate, contact path exists.
- `DISCOVERY` — score 65–79 or high fit with a non-fatal gap that should be resolved live.
- `WATCHLIST` — score 50–64.
- `HOLD_VERIFY` — evidence/credibility/conflict contradiction blocks action.
- `REJECT` — hard reject or score <50.

Interpret Stage A as **who deserves a discovery conversation**, not who has agreed to participate.

## Stage B — Live Partner Readiness

Use only after direct conversation or direct company evidence. Rate each 0–5.

| Dimension | Weight | High score means |
|---|---:|---|
| Problem confirmed | 15 | Actual user/buyer confirms the problem and consequence of status quo. |
| Urgency confirmed | 10 | There is a concrete reason to act inside the intended learning window. |
| User + champion access | 15 | The actual operator and a capable internal champion will participate. |
| Implementation readiness | 15 | Required data, integrations, owners, permissions, and capacity are realistically available. |
| Feedback commitment | 15 | Specific recurring time/usage/feedback commitment is agreed. |
| Decision/procurement feasibility | 10 | Required approval path fits the selected engagement motion and timeline. |
| Mutual value alignment | 10 | Both sides understand what they give/get and expectations are compatible. |
| Pilot measurability | 5 | Success/failure can be observed with credible criteria. |
| Transferability | 5 | The requested workflow is likely to generalize beyond this one account. |

### Stage B gates

Capture:

- `security_privacy_blocker` boolean,
- `legal_contract_blocker` boolean,
- `customization_risk` 0–5,
- `conflict_risk` 0–5,
- `commercial_commitment` 0–5 when relevant,
- `reference_permission` boolean/unknown when lighthouse value is material.

Apply:

1. `problem_confirmed < 2` → `REJECT`.
2. `user_champion_access < 2` or `feedback_commitment < 2` → never `PARTNER_READY`.
3. `implementation_readiness < 2` → `ALIGNMENT_REQUIRED` or `PAUSE`, depending on whether the blocker is realistically removable.
4. `customization_risk >= 4` or `transferability < 2` → never core `PARTNER_READY` without an explicit strategic exception.
5. Material unresolved security/privacy/legal/conflict blocker → `HOLD_VERIFY`.
6. For `PAID_PILOT`, insufficient commercial/approval commitment blocks `PARTNER_READY` but does not retroactively invalidate learning fit.
7. For `LIGHTHOUSE`, missing reference permission blocks lighthouse designation, not the underlying design-partner relationship.

Statuses:

- `PARTNER_READY` — score >=80, core readiness dimensions >=3, no blocker.
- `ALIGNMENT_REQUIRED` — score >=65 but a resolvable commitment/implementation/authority gap remains.
- `PAUSE` — timing or readiness makes activation inefficient now.
- `HOLD_VERIFY` — material blocker or contradiction requires resolution.
- `REJECT` — confirmed poor problem fit or non-transferable/bespoke direction.

## Diagnostic interpretation

For both stages also report:

- `learning_fit` — problem + representativeness/transferability + learning value,
- `activation_readiness` — urgency + implementation/access/commitment,
- `strategic_confidence` — evidence/credibility + commercial/reference optionality where applicable,
- score-driving dimensions,
- weakest binding dimension,
- highest-value missing fact.

Never let the composite average away a hard blocker.
