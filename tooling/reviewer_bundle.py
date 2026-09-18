"""Export only reviewer-facing fields, never the operator's unblinding map.

Condition metadata is removed, not model self-identification inside the response.
A supplied output can reveal its origin; no claim of perfect blinding is made.
"""
from __future__ import annotations
import io
from pathlib import Path
import zipfile

GUIDE = '''# Review the supplied responses

Score each output independently using its task, fixture, case rubric and dimensions.
Use integers 0–4: 0 = failed/contradictory; 1 = major defects; 2 = partially correct;
3 = correct with minor limitations; 4 = satisfies the task with no material defect.
Write evidence for every dimension. Do not infer execution from an assertion of success.
Keep absent reviews empty. Never add a score just to complete the form.

Flag material unsupported claims, missing conditions, unauthorized actions and fabricated
retrieval/testing separately from prose quality. Ratings require judgment, not substring hits.
Return the completed review-template.json. Use review_kind human only for an actual human
reviewer; model assistance must be recorded as model_assisted. Keep the output hash unchanged.

This archive excludes operator conditions, model identity and instruction hashes. Responses
remain verbatim and may themselves reveal origin. This is metadata blinding, not a guarantee
that a reviewer cannot infer the variant. Hashes identify bytes; they are not signatures.
'''


def write_reviewer_zip(path: Path, tasks: list[dict], template: dict) -> str:
    from package_skill import canonical, digest
    # Construct allowlisted objects again to avoid accidentally leaking future operator fields.
    admitted = []
    for task in tasks:
        if not isinstance(task, dict):
            raise ValueError('reviewer task must be an object')
        admitted.append({key: task[key] for key in ('id','case_id','prompt','fixture','rubric','output','output_sha256')})
    if any(not isinstance(t['output'], str) or digest(t['output'].encode()) != t['output_sha256'] for t in admitted):
        raise ValueError('reviewer output fingerprint mismatch')
    if not admitted or len({t['id'] for t in admitted}) != len(admitted):
        raise ValueError('empty/duplicate reviewer task inventory')
    if not isinstance(template, dict) or template.get('schema') != 'cometweb.skill-reviews/v1':
        raise ValueError('invalid review template')
    clean_reviews = []
    for row in template.get('reviews', []):
        if row.get('reviewer') is not None or row.get('review_kind') is not None or any(v is not None for v in row.get('scores',{}).values()):
            raise ValueError('export only blank review templates; no generated/pre-filled scores')
        clean_reviews.append({key:row[key] for key in ('run_id','output_sha256','reviewer','review_kind','scores','evidence','flags')})
    if {t['id']: t['output_sha256'] for t in admitted} != {r['run_id']:r['output_sha256'] for r in clean_reviews} or len(clean_reviews) != len(admitted):
        raise ValueError('tasks do not match review template')
    data = {'tasks.json':canonical({'schema':'cometweb.reviewer-tasks/v1','tasks':admitted}),
            'review-template.json':canonical({'schema':'cometweb.skill-reviews/v1','reviews':clean_reviews}),
            'REVIEW-GUIDE.md':GUIDE.encode()}
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w',compression=zipfile.ZIP_STORED) as archive:
        for name,blob in sorted(data.items()):
            info=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0))
            info.create_system=3;info.external_attr=0o100644<<16
            archive.writestr(info,blob)
    blob=stream.getvalue()
    if len(blob)>16*1024*1024:
        raise ValueError('reviewer export exceeds byte budget')
    with path.open('xb') as handle:
        handle.write(blob)
    return digest(blob)
