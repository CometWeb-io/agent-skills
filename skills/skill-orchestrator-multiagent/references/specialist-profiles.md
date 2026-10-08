# Local specialist profiles

These four opt-in profiles supplement existing owners; they are not globally installed skills.

| Profile | Owner | Added job |
| --- | --- | --- |
| conversion-audit | web-app-auditor | Evidence-bound conversion friction and test hypotheses |
| experiment-design | brief-architect | Preregisterable product experiment design |
| activation-onboarding | product-operator | First-value journey, activation and cohort gaps |
| sop-documentation | content-writer | Confirmed procedure, exceptions and verification |

From the local pilot root, preview routing without dispatch:

```sh
python3 skills/skill-orchestrator/scripts/specialist_profiles.py select 'Audyt CRO formularza'
```

Build one isolated existing-owner task, as a PLAN_ONLY preview, without executing a model or external action:

```sh
python3 skills/skill-orchestrator-multiagent/scripts/orchestrate_multiagent_kernel.py \
  'Udokumentuj potwierdzony proces eksportu danych jako SOP' \
  --specialist-profile sop-documentation --json
```

The canonical owner is pinned to this pilot tree. The generator verifies registry/inventory/license hashes, binds exactly one owner and adds instructions plus the sidecar schema path. The host loads that schema through its structured-output mechanism and then runs:

```sh
python3 skills/skill-orchestrator/scripts/specialist_profiles.py validate /path/to/sidecar.json
```

Validation requires the declared jsonschema runtime (use the existing project environment). Return the owner envelope and profile sidecar separately. Their contracts are not interchangeable. The profile gate validates shape, routing, source roles and local completeness. Full-response and wrapper validation additionally control local ledger completion. It does not verify evidence truth, calculate statistical power, authorize experiments or prove native/domain consumer compatibility.

Profiles cannot be combined through this flag with PRD ledger dispatch or Council packs until a domain handoff has been designed and qualified. They do not change existing default task generation, native skill discovery or installed metadata. Local deterministic checks are not model/host acceptance; the previous full-pipeline NO-GO remains.

## Ledger-backed owner/profile response

PROFILE.md is a specialization of the named owner, not another agent. selected_skills contains only the owner; selected_profile_id names the extension. Write the complete substantive owner artifact in artifact and the additional typed sidecar separately. Numeric input provenance and framework references use distinct fields in the v2 response schema. A method reference does not verify a product observation.

Create/save the plan from the preview above, then use the canonical workflow ledger's create command. Resume through this generator with --run-dir, --plan-json and --prior-envelopes-json exactly as described in prd-handoff.md. Profiles have the separate specialist-profile-owner/v2 gate and retry_limit, not the PRD READY requirement. The prefix contains full accepted carriers; altered/missing inputs dispatch nothing. The first prefix is an empty array. Complete-step needs the full CW-AIP carrier, with payload containing selected_skills, selected_profile_id, artifact and sidecar. Use the owner's envelope type and producer from the plan. Rejection appends no completion; an explicit fail closes the attempt before bounded retry. Profile completion includes profile_accepted, payload_hash and gate_lock_hash. Completed runs resume without model calls.

From the local pilot root:

```sh
python3 skills/skill-orchestrator/scripts/specialist_profiles.py validate-response /path/to/response.json --profile conversion-audit
```

Native discovery/Task remains unqualified. The opt-in trusted compiled pipeline is described in compiled-worker.md. Generic carrier admission does not independently validate the substantive owner artifact.
