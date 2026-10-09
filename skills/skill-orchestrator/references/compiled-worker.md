# Compiled local workers (opt-in pilot)

The parent authors `cometweb.trusted-profile-context/v1`: exact original_brief, profile_id, sources with id/kind/reference/summary, expected_result (explicit quantitative values or null), and optional declared cohort numerator/denominator/source_ids. Commit the data before model execution; changing it requires a new plan/run. Context integrity is not proof of source truth. Input kinds must come from the parent, never from model output.

`--trusted-context-json` enables inline compiled workers. A source list in a response may use only unchanged original records; new source IDs, changed kinds/text or changed protected values fail. `owner_output_json` must parse to a nonempty native owner report and pass the owner's actual validator. The primary artifact remains complete prose. A passing helper cannot establish agreement between all prose and structured claims; independent content review is mandatory for promotion.

The source lock covers the full file inventory of all eight runtime skills, registry, profiles and protocol, including generators, references, schemas and owner kernels. Added, removed or changed resources invalidate admission. Installed copies and symlinks outside the pinned root are forbidden. Cache files are excluded.

Combined mode (`--specialist-profile ... --with-prd-handoff --with-domain-gates`) requires trusted context and defers every downstream task until its full prefix passes checkpoint admission. PRD dependencies equal the completed profile prefix. Research and Council additionally bind exact upstream IDs/hashes/order; the Council research step is taken from the locked plan rather than a fixed index.

Send the returned prompt unchanged with worker_schema. Record prompt_hash, raw answer, tool events and cost/usage. Retry needs explicit fail_step, a new attempt ID and a new model call compiled with --previous-error. Max two attempts; failure/budget stop must not leave an active attempt. Resume through a fresh generator process, revalidating full prefix contents.

Council roles: compile two blind memos with no peers/Judge; then compile Judge from both raw memos and kernel-ready claims; then Chairman from admitted claims and the native confidence threshold. Parent preserves original proposals and computes only deterministic constraints. No worker or completion authorizes external execution/publication. The baseline arm removes profile instructions only; it uses the same new transport/gates and is an instruction ablation, not the released legacy runtime.

### Typed local native reports

Add `--typed-native-reports` with the trusted profile input to pin
`native_report_contract=cometweb.typed-local-owner/v2`. Resume uses that locked
choice, without an override. It replaces legacy owner_output_json with a typed
owner_output and native_source_bindings. The closed supplied-input schemas are
[brief](native-reports/brief-architect.schema.json),
[operator](native-reports/product-operator.schema.json),
[writer](native-reports/content-writer.schema.json) and
[auditor](native-reports/web-app-auditor.schema.json).

Bindings cover every native source slot exactly once. Writer/operator source
fields hold original IDs, locator fields hold exact original references, and
authority/claim_type preserve original kinds. Writer approved_sources equals
the parent ID inventory. Brief inputs and auditor evidence.location use exact
original references. Unknown sources/pointers, duplicate or missing bindings,
changed kinds/references, malformed native structures and brief/kernel status
disagreement fail before completion. Never invent a hypothesis source ID to
represent an inferred claim. Bound sources remain supplied data, not proof of
world truth or approval of every claim supported by them.

This is a complete typed interface for this bounded read-only pilot. It excludes
live mutation, browser acquisition, contract traces and product state snapshots;
the existing canonical live-host contracts continue to apply outside this mode.
Each native validator still checks cross-field invariants. All Council roles,
including the Chair, receive previous_attempt_error on a fresh retry; blind
memos still receive no peer/Judge reports. Error text is diagnostic data, never
new evidence or execution permission.

output_oracles.exact_number retains the sign, accepts only an entire ASCII
decimal numeric response (including Unicode minus), and rejects explanations,
NaN/Infinity, exponents and Unicode digit lookalikes. exact_text is a trimmed
literal text control; neither is a semantic grader.

Literal compiled interface fields (included in the locked plan, task, inputs or report):

```text
acceptance_criteria
compiled_worker_version
const
denominator
derived
environment
expected_result
findings
instruction_arm
numerator
original_brief
owner_output_json
sources
trusted_context
trusted_context_hash
```

Native binding/report interface keys: `source_id`, `approved_sources`, `authority`, `claim_type`, `inputs`, `kernel_result`, `location`, `locator`, `source`. kernel_result is the independent owner validation result, not model evidence.

Native binding pointer uses the whole response as its JSON root: every pointer starts with `/owner_output/`. Examples: `/owner_output/inputs/0`, `/owner_output/evidence/0/location`, `/owner_output/claims/0/evidence/0/source`, `/owner_output/verify_now/0/evidence/0/source`. Relative pointers without this prefix are not the v2 wire contract.

For typed product-operator dispatch supply --report-as-of with a parent timestamp and timezone. It is frozen report metadata, not observed_at/verified_at or proof of evidence freshness. The native as_of must equal that anchor. Resume reuses the plan value; replacing it requires a new plan. Hosts must strictly parse raw worker JSON before object admission: owner_admission.parse_json rejects duplicate keys and non-finite values. The typed schema cannot detect keys already discarded by a caller decoder. Interface keys: `report_as_of`, `report_timestamp_scope`.
