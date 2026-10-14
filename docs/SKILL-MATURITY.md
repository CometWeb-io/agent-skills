# Skill maturity and experimental distribution

All 34 current packages are **experimental**, with declared stage `DEVELOPMENT`.
Their package and contract checks do not establish task effectiveness across
models or hosts. Previous bounded experiments retain their original scope;
they are not qualification of the current catalog.

## Stages

| Stage | Meaning | Publication in this distribution |
|---|---|---|
| `SCAFFOLD` | Generated author prompts and synthetic structural cases | Development ZIP only; full admission and versioned builds refuse it |
| `DEVELOPMENT` | Authored instructions and executable local contracts; usefulness unqualified | Explicitly `EXPERIMENTAL` |
| `CANDIDATE` | A declared candidate prepared for a frozen, version-bound task experiment | Explicitly `EXPERIMENTAL`; the label does not prove preparation or success |
| `QUALIFIED` | Independent task evidence supports a stated version/host/model scope | Reserved; current experimental distribution refuses this label |

There is no automatic stage promotion. Removing scaffold phrases, changing a
version, passing deterministic tests or supplying `QUALIFIED` in JSON cannot
qualify a skill. Advancement to candidate requires a review of the task contract,
frozen cases and evaluation plan; those materials must retain their provenance.
Qualification needs observed real-task results, independent blind assessment,
source and host/model binding, ground truth, regressions and resource limits.
It requires a separate reviewed admission change, rather than disabling the
experimental gate or accepting a self-certified flag. Qualification would remain
scoped to that experiment; it would not grant publication or external-action
authority.

## Package contract

Each installed source folder carries `MATURITY.json` with these exact fields:

```json
{
  "schema": "cometweb.skill-maturity/v1",
  "skill": "example-skill",
  "version": "1.0.0",
  "stage": "DEVELOPMENT",
  "publication": "EXPERIMENTAL",
  "task_qualification": "not_established"
}
```

Identity must match the folder and `VERSION`. Missing, duplicate, unknown or
mistyped fields, non-experimental publication, claimed qualification and
`QUALIFIED` block current admission. Versioned builds also refuse `SCAFFOLD`,
even if every recognized template phrase has been removed. The generator starts
at `SCAFFOLD`; after writing real instructions and cases, the author explicitly
changes the stage to `DEVELOPMENT`. This declaration still proves no usefulness.

The same parser serves the full plugin gate, registry projection and ZIP
admission. Registry values and catalog notes are generated from package metadata.
The existing closed `cometweb.package/v1` manifest hashes the single canonical
`MATURITY.json` payload file; it does not duplicate that declaration in a new
manifest field. Current readers validate the declaration, while older readers
can still inspect payload integrity without assessing maturity. CLI build results
report the parsed declaration. Changing the file or reusing an old unclassified
archive cannot silently produce a classified release. An immutable conflict requires a newer package
version; existing archives are preserved.

Every versioned build, including cache reuse, also requires a currently clean
Git checkout and an archive with clean, SHA-pinned source provenance. A dev ZIP
copied into the versioned path is refused, including when a concurrent writer
places it there. Neither cache presence nor equal payload hashes grants release
provenance.

Legacy ZIPs without maturity metadata remain inspectable as unclassified
historical artifacts. Inspection does not upgrade them, prove task quality or
make them eligible for a new build. Development ZIPs remain outside the versioned
release path and retain their declared stage and unassessed runtime acceptance.
Installers copy/link whole skill folders, so the declaration accompanies a
selective install without a new pack loader or front-door instruction.
