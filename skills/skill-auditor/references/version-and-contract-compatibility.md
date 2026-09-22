# Version and contract compatibility

Audit public skill contracts as versioned interfaces.

- PATCH: bugfix/instruction clarification with no observable contract expansion or break.
- MINOR: backward-compatible capability, optional field, new routing signal, additive reference/tooling.
- MAJOR: removed/renamed required field, changed enum semantics, incompatible handoff payload, removed supported host, or routing ownership change that can redirect existing prompts.

A breaking change without a major bump is a release blocker. Breaking public behavior also requires a migration guide. UNKNOWN compatibility cannot be called compatible.

Runtime host support must be distinguished from static packaging compatibility. `STATIC_SHAPE_ONLY` is not `REAL_HOST_VERIFIED`.
