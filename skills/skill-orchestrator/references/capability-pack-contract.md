# Optional capability-pack contract (local pilot)

`schema: cometweb.capability-packs/pilot-v1` identifies the registry. Its `packs`
list contains rows with unique `id`, `role_id`, `match_any` regular expressions,
`entrypoint`, `license_file`, `license`, `source_repository`, `source_commit`,
`claim_class`, and `files` (relative path -> lowercase SHA-256).

The local pilot accepts MIT materials, pins the source_commit to a 40-character
Git SHA and validates both the entrypoint and license_file in the locked files.
All paths resolve within the package root; missing or changed files block loading.
role_id is product_customer, offer_pricing or sales. claim_class is FRAMEWORK:
this field describes doctrine, not factual evidence or an independent vote.

An opted-in plan adds `capability_packs[]` with id, role_id, entrypoint,
source_repository, source_commit, license, license_file and claim_class. It never
executes pack commands or changes the existing step plan. A specialist/host must
explicitly consume selected pointers under the Council evidence and permission
rules. Normal CLI output does not include capability_packs without opt-in.
