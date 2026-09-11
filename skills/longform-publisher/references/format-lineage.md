# Derived-format lineage

`manuscript.md` is canonical. Every derived artifact records:

```text
id
format
path
master_sha256
generation_status
qa_required
qa_status
parity_status
direct_material_edit
```

`master_sha256` must equal the current canonical master hash.

DOCX and PDF require visual render/inspection QA before FORMAT_READY because layout defects cannot be inferred from source text alone. Use the `docx` and `pdfs` specialist workflows for generation/verification.

For HTML/EPUB/other formats, record the QA appropriate to the target. If `qa_required=true`, `qa_status` must be PASS.

`parity_status=PASS` means material text/content is consistent with the canonical master for the intended transformation. It does not require byte equality.

A direct material edit to a derived DOCX/PDF/HTML is not a canonical change. Set `direct_material_edit=true`, reject release readiness, move the content change back to `manuscript.md`, then regenerate.
