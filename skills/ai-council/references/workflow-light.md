# Council workflow — LIGHT

Use for small, reversible decisions. Do **not** load forecasting, portfolio, or living-decision machinery unless a binding risk gate forces it.

1. Set timezone-aware `as_of`. Build Decision Contract (`decision-contract.md`) — known fields only.
2. Optional `context-route` for material internal claims (`internal-context.md`).
3. `plan` with LIGHT/FAST budget (`modes.md`).
4. 2–3 perspectives (advisers/specialists within budget).
5. Evidence sanity + one falsifier pass on critical claims.
6. Key risks / abbreviated Red Team + Evidence Judge.
7. Verdict: `GO` | `TEST` | `DEFER` with explicit blockers/controls.
8. Emit Decision Snapshot + output contract (`output-contract.md`).

Hard stop: if Legal/Security/Privacy risk surface requires a gate that LIGHT cannot clear → escalate profile to STANDARD.
