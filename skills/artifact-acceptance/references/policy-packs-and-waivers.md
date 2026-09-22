# Acceptance profiles, policy packs, and waivers

Use a profile to predeclare required gates before seeing the outcome.

Built-in profile families: `GENERAL`, `EDITORIAL`, `RESEARCH`, `SALES`, `TECHNICAL_DOCS`; `CUSTOM` is allowed when the user supplies an explicit contract.

A required gate may be `N/A` only when the contract allows N/A for that gate and the report records why. `N/A` is not a pass shortcut.

## Controls and waivers

Controls can bound residual non-critical risk. They cannot convert a failed or unknown required gate into READY.

A waiver is admissible only for non-blocking `MINOR`/`NOTE` residuals and, when required by the mode, records approver, approval time, expiry/revisit condition, candidate identity, and rationale. An expired waiver is not current control evidence.

Never use `READY_WITH_CONTROLS` as a euphemism for an unresolved required gate.
