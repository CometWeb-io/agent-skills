# Local profile owner admission v2

Profiles are extensions of existing owners, with PROFILE.md entrypoints, not SKILL.md packages. Registry schema cometweb.specialist-profiles/local-v2 locks every entrypoint, output_schema, response_schema and license. Native discovery and global installation are outside this opt-in interface.

Response fields: selected_skills contains exactly the canonical owner, selected_profile_id contains the profile ID, artifact contains the complete standalone owner result, sidecar is additional typed metadata. Essential hypotheses, recommendations, procedure and verification remain in artifact. A provenance note may mention the sidecar; explicit delegation of essential content is rejected conservatively. This detector does not prove complete semantic output; independent content review remains necessary.

Sidecar schema is cometweb.specialist-profile-output/v2. Numeric experiment fields use separate parameter_source_ids for baseline_rate, sample_size_per_variant, mde_absolute, alpha and power. Supplied inputs require USER_INPUT/OBSERVED; framework_source_ids require FRAMEWORK and justify methods only. Hypotheses and planned steps resolve their references but cannot establish observed facts. Confirmed SOP steps have basis CONFIRMED, proposed ones PROPOSED. EXTERNAL_MUTATION always requires approval_requirement, including proposed steps. No status authorizes execution.

select returns suggested_profiles and dispatch=false. validate checks the sidecar. validate-response --profile PROFILE checks the complete response. New response_schema and profile_result_schema pointers supplement profile_output_schema in the task. The plan and step carry profile_lock and gate_lock; source hashes bind the registry, profile files, owner entrypoint, helper, ledger and CW-AIP wrapper/schemas. Source drift requires a new plan/run; v1 is not coerced into v2.

The one-owner plan uses handoff_gate specialist-profile-owner/v2, retry_limit 2 (allowed integer 1..3). The generator emits PLAN_ONLY; save the plan and create a canonical workflow ledger. Ledger-backed dispatch validates completed full CW-AIP carriers and exact recorded hashes. The carrier payload is the full response, preserving the owner's artifact string unchanged and sidecar separately. Full envelope type/producer must match the owner. It is a standalone carrier with empty dependencies; Legacy carriers provide contract-only checks. The opt-in trusted compiled interface is described in compiled-worker.md and adds a four-stage PRD/research/Council pipeline.

Completion revalidates response, provenance and wrapper; wrong owners, profile-as-skill IDs, explicit delegation, malformed JSON, unknown references and changed source locks append no completion. handoff_validation includes profile_accepted, payload_hash, expected_type, producer and gate_lock_hash. Rejected attempts remain RUNNING until explicit fail/block/cancel. Retry is a fresh attempt with incremented attempt_number; exhaustion records BLOCKED. Resume is idempotent and does not dispatch completed steps. Source locks and hash chains are local operational controls for one sequential parent, not a distributed dispatcher or authentication boundary.

Generic wire shape is qualified separately from semantic correctness of the owner's artifact; completion is not acceptance of a product/experiment or a native downstream consumer. Default unprofiled planning is unchanged.

Additional literal interface vocabulary:

```text
artifact
framework_source_ids
parameter_source_ids
profile_accepted
profile_lock
response_schema
selected_profile_id
selected_skills
sidecar
```

Registry profiles carry profile_id/id, owner_skill, source_sha256 and the plan's specialist_profile lock. Sidecar unknowns preserve missing data; the helper returns errors. Conversion fields include baseline_source_ids and observations with source_ids. Experimental method and instrumentation describe the proposed design. Product activation fields include activation_definition, cohort, activation_rate, activation_source_ids, retention_link and retention_source_ids. SOP step risk determines the permission checkpoint. All source_ids resolve in evidence and retain their declared provenance role.
