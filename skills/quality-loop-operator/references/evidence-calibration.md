# Evidence calibration

Evidence grades describe fitness for a particular claim/gate. They do not certify truth.

- `A`: direct, candidate/scope-matched evidence from a primary/system-of-record/runtime/release-capable lane, current when freshness matters, with a usable locator.
- `B`: direct and current evidence with good but not highest authority, or authoritative evidence with a bounded independence/scope limitation.
- `C`: indirect/supporting evidence, near-expiry evidence, bounded test evidence for a broader runtime claim, or inference with explicit basis.
- `D`: stale/unknown/context-only/contradicted or materially scope-mismatched evidence. Never sole support for a required material gate.
- `INVALID`: missing source/locator, candidate mismatch where binding is required, malformed timestamp where freshness is required, or other inadmissible shape.

Policy packs may define minimum grades for critical/material/supporting uses. Grade inflation is a defect.
