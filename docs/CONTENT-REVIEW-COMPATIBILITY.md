# Content review compatibility

`content-reviewer` 1.8.0 owns the shared editorial and adversarial review
instructions. `content-roaster` 7.0.0 is its ADVERSARIAL profile entry and
retained v6 adapter. A profile changes review emphasis, not evidence thresholds,
authority, independence or the report format. Ordinary prose needs one review.

## Contracts retained

| Receiving contract | Existing validation | Compatibility rule |
| --- | --- | --- |
| `cometweb.content-review/v1` | `content-reviewer/scripts/kernel.py`, `review(payload)` | Preserve candidate/finding ids, evidence, coverage, evidence floors and carried-finding revalidation. |
| `cometweb.content-roaster/v6` | `content-roaster/scripts/validate_roast.py` | Preserve source ids, finding keys, diagnosis/evidence links, confidence, verification and resolution semantics. |

Both validators and v6 schema remain unchanged. They have different admission
rules and neither authenticates source evidence. Do not feed v6 through the v1
gate, infer one verdict from the other or invent fields to manufacture a pass.
The caller's receiving contract selects the format. Merely asking for a sharper
critique does not require v6, JSON or another review pass.

## Existing workflows

Existing `content-reviewer` and `content-roaster` stage ids remain valid in
quality-loop plans. Stored plans and locks are not rewritten by this change.
An explicitly frozen two-stage plan must still supply its required rows; two
passes in one context are not independent. New ordinary plans select one review
entry. A new or changed plan needs its own version/lock and fresh verification.

All helper paths remain in their original packages. Canonical-only installations
can use review/v1; a v6 request requires the compatibility package. A missing
adapter is a missing capability, not permission to fall back to a weaker gate.

## Installation and rollback

This is a major package/distribution change: content-roaster is no longer a
standalone instruction owner. A manually copied 7.0.0 package needs the
content-reviewer 1.8.0 package beside it. The bundle candidate is 3.0.0; this
does not rename or change the retained v6 wire format. Upgrades through a
complete bundle or the updated selective installers include the dependency.
A missing/excluded canonical package stops the alias instead of weakening it.


Selective host installs of an alias include its canonical dependency:

```bash
./scripts/install-codex.sh --skill content-roaster --dry-run
./scripts/install-claude.sh --skill content-roaster --dry-run
./scripts/install-cursor.sh --skill content-roaster --dry-run
```

The same closure applies to other shell host installers and pinned snapshot
installation. `ALIAS_OF` files are generated from registry `alias_of`; they are
installation data, not a second policy source. Missing/cyclic/invalid targets
fail before writes. Snapshot receipts and rollback cover every selected alias
dependency. Uninstalling just an alias leaves the canonical package intact.

Upgrade the adapter and canonical package together. Keep the prior reviewed
SHA/receipt for rollback; restore that whole set, not a single alias against an
incompatible canonical version. This source change performs no host installation.

Routing retains legacy entry ids while grouping them under one owner. An alias
does not bypass canonical exclusion or unavailability. Generated alias text uses
its own declared intent; content aliases do not request multiagent execution.

These are compatibility guarantees checked by local deterministic tests, not
evidence that the merged instructions outperform the native model or that a
particular host/model has accepted the package.
