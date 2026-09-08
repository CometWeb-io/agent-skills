# Optional browser-agent readiness overlay

Use only when the user asks about agentic browsing, task completion, shopping/booking/form agents,
or machine interaction. This overlay is excluded from MAXX unless the registry is explicitly
extended in a future version.

Search/citation readiness and agent interaction are different problems. Do not claim that ARIA
improves search rankings or AI citations merely because it helps an agent interpret controls.

## Inspect

- semantic native controls where possible;
- accurate accessible names, roles, states, and relationships;
- ARIA only where needed and kept synchronized with real state;
- predictable form labels, validation, errors, and success states;
- stable URLs and clear navigation destinations;
- controls that are keyboard/assistive-technology usable;
- visible product/service constraints and transaction prerequisites;
- explicit loading/disabled/selected/expanded states;
- confirmation before irreversible or high-impact actions;
- no critical facts hidden only in inaccessible canvas/image/hover interactions.

## Evidence

Use rendered DOM/accessibility tree, browser interaction, and target-agent tests when available. Do
not infer agent success from visual appearance alone.

## Output

Report:

1. task tested;
2. step where the agent succeeds/fails;
3. exact DOM/accessibility/state evidence;
4. user impact and safe remediation;
5. whether the issue is agent-specific or also an accessibility/usability defect.

Re-check current platform guidance before naming a specific agent/browser implementation as a stable
requirement.
