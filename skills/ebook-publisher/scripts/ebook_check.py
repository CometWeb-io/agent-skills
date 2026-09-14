#!/usr/bin/env python3
"""Read-only record checks, not a fact checker, renderer, or publication certificate."""
from __future__ import annotations

import argparse
from datetime import date, datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
from typing import Any
from urllib.parse import urlsplit

SCHEMA = 'cometweb.ebook/v1'
STAGES = ('research', 'manuscript', 'release')
CHECKS = {
    'research': ('scope_coverage', 'source_entailment', 'counterevidence'),
    'manuscript': ('claim_coverage', 'cross_chapter_consistency', 'semantic_fidelity',
                   'editorial_review', 'examples_and_numbers'),
    'release': ('visual_design', 'pdf_structure', 'links_and_navigation',
                'accessibility_review', 'asset_rights', 'package_hygiene'),
}
BINDINGS = {'research': ('research',), 'manuscript': ('research', 'manuscript'),
            'release': ('research', 'manuscript', 'pdf')}
CORE = ('publication', 'scope', 'chapters', 'sources', 'claims')
MAX_JSON = 4 * 1024 * 1024
MAX_MANUSCRIPT = 16 * 1024 * 1024
MAX_PDF = 128 * 1024 * 1024
ID = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$')
HEX = re.compile(r'^[a-f0-9]{64}$')
PLACEHOLDER = re.compile(r'\[(?:UZUPEŁNIJ|UZUPELNIJ|TODO|TBD)\b', re.I)


class InputError(ValueError):
    """Malformed, unsafe, inaccessible, or unsupported input; never a success state."""


def obj(value: Any, where: str) -> dict:
    if not isinstance(value, dict):
        raise InputError(f'{where}: expected an object')
    return value


def array(value: Any, where: str) -> list:
    if not isinstance(value, list):
        raise InputError(f'{where}: expected an array')
    return value


def string(value: Any, where: str) -> str:
    if not isinstance(value, str):
        raise InputError(f'{where}: expected text')
    return value


def boolean(value: Any, where: str) -> bool:
    if type(value) is not bool:
        raise InputError(f'{where}: expected a JSON boolean')
    return value


def integer(value: Any, where: str) -> int:
    if type(value) is not int:
        raise InputError(f'{where}: expected an integer, not a boolean')
    return value


def strict_pairs(pairs: list[tuple[str, Any]]) -> dict:
    out = {}
    for key, value in pairs:
        if key in out:
            raise InputError(f'Duplicate JSON key: {key}')
        out[key] = value
    return out


def invalid_constant(value: str) -> None:
    raise InputError(f'Non-finite JSON constant is not supported: {value}')


def load_json(path: Path) -> dict:
    try:
        with path.open('rb') as stream:
            raw = stream.read(MAX_JSON + 1)
        if len(raw) > MAX_JSON:
            raise InputError(f'Manifest exceeds {MAX_JSON} bytes')
        result = json.loads(raw.decode('utf-8'), object_pairs_hook=strict_pairs,
                            parse_constant=invalid_constant)
        return obj(result, 'manifest')
    except (OSError, UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise InputError(f'Cannot read manifest: {exc}') from exc


def local_path(root: Path, relative: Any) -> Path:
    value = string(relative, 'local file path')
    if not value.strip() or '\\' in value:
        raise InputError('Local file path must be nonempty and use forward slashes')
    p = PurePosixPath(value)
    if p.is_absolute() or '..' in p.parts or ':' in value:
        raise InputError(f'Unsafe local path: {value}')
    try:
        base = root.resolve(strict=True)
        resolved = (base / Path(*p.parts)).resolve()
        resolved.relative_to(base)
    except (OSError, ValueError, RuntimeError) as exc:
        raise InputError(f'Local path escapes or cannot resolve within workspace: {value}') from exc
    return resolved


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open('rb') as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(chunk)
    except OSError as exc:
        raise InputError(f'Cannot hash {path.name}: {exc}') from exc
    return digest.hexdigest()


def canonical_hash(value: Any) -> str:
    try:
        raw = json.dumps(value, ensure_ascii=False, sort_keys=True,
                         separators=(',', ':'), allow_nan=False).encode('utf-8')
    except (TypeError, ValueError, RecursionError) as exc:
        raise InputError(f'Cannot fingerprint records: {exc}') from exc
    return hashlib.sha256(raw).hexdigest()


def fingerprints(manifest: dict, root: Path) -> dict:
    obj(manifest, 'manifest')
    files = obj(manifest.get('files'), 'files')
    out = {'research': canonical_hash({k: manifest.get(k) for k in CORE})}
    for field, key in (('manuscript', 'manuscript'), ('pdf', 'pdf')):
        path = local_path(root, files.get(field))
        out[key] = sha256_file(path) if path.is_file() else None
    return out


def current_date() -> date:
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo('Europe/Warsaw')).date()
    except (ImportError, KeyError, OSError):
        return date.today()


class Review:
    def __init__(self, root: Path, as_of: date):
        self.root = root
        self.as_of = as_of
        self.blockers: list[dict] = []
        self.warnings: list[dict] = []

    def fail(self, code: str, detail: str) -> None:
        self.blockers.append({'code': code, 'detail': detail})

    def require(self, condition: bool, code: str, detail: str) -> None:
        if not condition:
            self.fail(code, detail)

    def text(self, record: dict, key: str, where: str) -> str:
        value = string(record.get(key, ''), f'{where}.{key}')
        self.require(bool(value.strip()) and not PLACEHOLDER.search(value),
                     'missing_text', f'{where}.{key}: meaningful text is required')
        return value

    def day(self, value: Any, where: str, future: bool = False) -> date | None:
        value = string(value, where)
        try:
            if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
                raise ValueError('Use YYYY-MM-DD')
            result = date.fromisoformat(value)
        except ValueError:
            self.fail('invalid_date', f'{where}: invalid ISO calendar date')
            return None
        if not future:
            self.require(result <= self.as_of, 'future_date',
                         f'{where}: after evaluation date {self.as_of}')
        return result

    def indexed(self, records: Any, where: str) -> dict[str, dict]:
        out = {}
        for i, value in enumerate(array(records, where)):
            value = obj(value, f'{where}[{i}]')
            key = string(value.get('id'), f'{where}[{i}].id')
            self.require(bool(ID.fullmatch(key)), 'invalid_id', f'{where}: invalid ID {key!r}')
            self.require(key not in out, 'duplicate_id', f'{where}: duplicate {key}')
            out[key] = value
        return out

    def ids(self, value: Any, where: str) -> list[str]:
        items = array(value, where)
        for item in items:
            string(item, where)
        self.require(len(items) == len(set(items)), 'duplicate_reference', where)
        return items

    def artifact(self, path_value: Any, expected: Any, where: str) -> bool:
        path = local_path(self.root, path_value)
        self.require(path.is_file(), 'missing_evidence_file', f'{where}: file is absent')
        if not path.is_file():
            return False
        digest = string(expected, f'{where}.sha256')
        good = bool(HEX.fullmatch(digest)) and digest == sha256_file(path)
        self.require(good, 'file_hash_mismatch', f'{where}: hash differs from the recorded evidence')
        return good


def check_scope(v: Review, manifest: dict) -> tuple[dict, dict]:
    pub = obj(manifest.get('publication'), 'publication')
    for key in ('id', 'title', 'language', 'edition', 'revision'):
        v.text(pub, key, 'publication')
    v.day(pub.get('as_of', ''), 'publication.as_of')
    scope = obj(manifest.get('scope'), 'scope')
    for key in ('audience', 'outcome'):
        v.text(scope, key, 'scope')
    questions = v.indexed(scope.get('questions'), 'scope.questions')
    chapters = v.indexed(manifest.get('chapters'), 'chapters')
    v.require(bool(questions), 'empty_questions', 'Reader questions are required')
    v.require(bool(chapters), 'empty_chapters', 'Chapter mapping is required')
    for qid, question in questions.items():
        v.text(question, 'question', qid)
        state = string(question.get('status'), f'{qid}.status')
        v.require(state in ('covered', 'open', 'excluded'), 'invalid_question_status', qid)
        v.require(state != 'open', 'open_question', qid)
        linked = v.ids(question.get('chapter_ids'), f'{qid}.chapter_ids')
        if state == 'excluded':
            v.text(question, 'rationale', qid)
            v.require(not linked, 'coverage_mismatch', f'{qid}: excluded question cannot map to a chapter')
        if state == 'covered':
            v.require(bool(linked), 'coverage_mismatch', f'{qid}: no covering chapter')
        for cid in linked:
            v.require(cid in chapters, 'unknown_chapter', f'{qid}: {cid}')
            if cid in chapters:
                v.require(qid in v.ids(chapters[cid].get('question_ids'), f'{cid}.question_ids'),
                          'coverage_mismatch', f'{qid} -> {cid} has no reciprocal mapping')
    for cid, chapter in chapters.items():
        for key in ('title', 'outcome'):
            v.text(chapter, key, cid)
        linked = v.ids(chapter.get('question_ids'), f'{cid}.question_ids')
        v.require(bool(linked), 'coverage_mismatch', f'{cid}: no reader question')
        for qid in linked:
            v.require(qid in questions, 'unknown_question', f'{cid}: {qid}')
            if qid in questions:
                v.require(questions[qid].get('status') == 'covered' and cid in questions[qid].get('chapter_ids', []),
                          'coverage_mismatch', f'{cid} -> {qid} has no reciprocal covered mapping')
    return questions, chapters


def check_sources(v: Review, manifest: dict) -> dict:
    sources = v.indexed(manifest.get('sources'), 'sources')
    for sid, source in sources.items():
        for key in ('title', 'origin'):
            v.text(source, key, sid)
        stype = string(source.get('source_type'), f'{sid}.source_type')
        v.require(stype in ('primary', 'secondary', 'discovery', 'provided', 'experiment'),
                  'invalid_source_type', sid)
        boolean(source.get('inspected'), f'{sid}.inspected')
        accessed = v.day(source.get('accessed_on', ''), f'{sid}.accessed_on')
        if source.get('published_on') is not None:
            published = v.day(source['published_on'], f'{sid}.published_on')
            if accessed and published:
                v.require(published <= accessed, 'source_chronology', f'{sid}: publication after access')
        url = string(source.get('url', ''), f'{sid}.url')
        if url:
            try:
                parsed = urlsplit(url)
                ok = parsed.scheme in ('https', 'http') and bool(parsed.hostname) and not parsed.username and not parsed.password
            except ValueError:
                ok = False
            v.require(bool(ok), 'unsafe_source_url', f'{sid}: use a public HTTP(S) URL without embedded credentials')
        else:
            artifact = source.get('artifact')
            if artifact is None:
                v.fail('missing_source_location', f'{sid}: URL or local source artifact required')
            else:
                artifact = obj(artifact, f'{sid}.artifact')
                v.artifact(artifact.get('path'), artifact.get('sha256'), f'{sid}.artifact')
    return sources


def check_claims(v: Review, manifest: dict, chapters: dict, sources: dict) -> dict:
    claims = v.indexed(manifest.get('claims'), 'claims')
    v.require(bool(claims), 'empty_claims', 'A research record requires a nonempty claim ledger')
    expected = {'fact': ('supported', 'qualified'), 'recommendation': ('recommended',),
                'inference': ('inferred',), 'synthetic': ('illustrative',)}
    for cid, claim in claims.items():
        v.text(claim, 'text', cid)
        chapter = string(claim.get('chapter_id'), f'{cid}.chapter_id')
        v.require(chapter in chapters, 'unknown_chapter', f'{cid}: {chapter}')
        kind = string(claim.get('kind'), f'{cid}.kind')
        importance = string(claim.get('materiality'), f'{cid}.materiality')
        conclusion = string(claim.get('conclusion'), f'{cid}.conclusion')
        v.require(kind in expected, 'invalid_claim_kind', cid)
        v.require(importance in ('critical', 'material', 'background'), 'invalid_materiality', cid)
        v.require(conclusion in expected.get(kind, ()), 'claim_conclusion', f'{cid}: {kind}/{conclusion}')
        if conclusion == 'qualified':
            v.text(claim, 'qualification', cid)
        if kind in ('inference', 'recommendation'):
            v.text(claim, 'rationale', cid)
        if kind == 'synthetic':
            v.text(claim, 'display_label', cid)
        sensitive = boolean(claim.get('time_sensitive'), f'{cid}.time_sensitive')
        if sensitive:
            start = v.day(claim.get('as_of', ''), f'{cid}.as_of')
            end = v.day(claim.get('review_by', ''), f'{cid}.review_by', future=True)
            v.text(claim, 'freshness_rationale', cid)
            if start and end:
                v.require(start <= end, 'freshness_window', cid)
            if end:
                v.require(v.as_of <= end, 'stale_claim', f'{cid}: review due after {end}')
        material = importance in ('critical', 'material') and kind != 'synthetic'
        support = []
        contradictions = []
        for n, edge in enumerate(array(claim.get('evidence'), f'{cid}.evidence')):
            edge = obj(edge, f'{cid}.evidence[{n}]')
            sid = string(edge.get('source_id'), f'{cid}.source_id')
            relation = string(edge.get('relation'), f'{cid}.relation')
            v.require(sid in sources, 'unknown_source', f'{cid}: {sid}')
            v.require(relation in ('supports', 'contradicts', 'context'), 'invalid_relation', cid)
            v.text(edge, 'locator', f'{cid}/{sid}')
            v.text(edge, 'explanation', f'{cid}/{sid}')
            if relation == 'supports':
                support.append(sid)
            if relation == 'contradicts':
                contradictions.append(sid)
            if material and relation in ('supports', 'contradicts') and sid in sources:
                source = sources[sid]
                v.require(source.get('inspected') is True and source.get('source_type') != 'discovery',
                          'inadmissible_source', f'{cid}/{sid}: underlying source must be inspected')
        if material:
            v.require(bool(support), 'missing_support', cid)
            origins = {sources[sid].get('origin') for sid in set(support) if sid in sources}
            if len(set(support)) > 1 and len(origins) == 1:
                v.warnings.append({'code': 'shared_origin', 'detail': f'{cid}: multiple support sources share one origin; not independent confirmations'})
            check = claim.get('countercheck')
            if check is None:
                v.fail('countercheck_missing', cid)
            else:
                check = obj(check, f'{cid}.countercheck')
                v.require(boolean(check.get('performed'), f'{cid}.countercheck.performed'), 'countercheck_missing', cid)
                queries = array(check.get('queries'), f'{cid}.countercheck.queries')
                for query in queries:
                    string(query, f'{cid}.countercheck.query')
                v.require(bool(queries) and all(q.strip() for q in queries), 'countercheck_empty', cid)
                v.text(check, 'outcome', f'{cid}.countercheck')
                v.day(check.get('checked_on', ''), f'{cid}.countercheck.checked_on')
                for sid in v.ids(check.get('source_ids'), f'{cid}.countercheck.source_ids'):
                    v.require(sid in sources, 'unknown_source', f'{cid}.countercheck: {sid}')
        if contradictions:
            resolution = string(claim.get('resolution', ''), f'{cid}.resolution')
            v.require(bool(resolution.strip()), 'unresolved_contradiction', f'{cid}: source-specific resolution is required')
    return claims


def manuscript_prose(text: str, v: Review) -> str:
    """Mask fenced/inline code so examples cannot impersonate citations or ledger anchors.

    This is a bounded Markdown convention, not a complete CommonMark parser.
    """
    lines = []
    fence = None
    for line in text.splitlines(keepends=True):
        if fence is not None:
            char, length = fence
            if re.fullmatch(r"[ ]{0,3}" + re.escape(char) + "{" + str(length) + r",}[ \t]*(?:\r?\n)?", line):
                fence = None
            lines.append("\n" if line.endswith("\n") else "")
            continue
        match = re.match(r"^[ ]{0,3}(`{3,}|~{3,})(.*)$", line.rstrip("\r\n"))
        if match and not (match.group(1)[0] == "`" and "`" in match.group(2)):
            fence = (match.group(1)[0], len(match.group(1)))
            lines.append("\n" if line.endswith("\n") else "")
        else:
            lines.append(line)
    v.require(fence is None, 'unclosed_code_fence', 'Manuscript has an unclosed code fence')
    prose = ''.join(lines)
    return re.sub(r"(?<!`)(`+)(?!`)(.*?)\1(?!`)",
                  lambda match: "\n" * match.group(0).count("\n"), prose, flags=re.S)


def check_manuscript(v: Review, manifest: dict, chapters: dict, sources: dict, claims: dict) -> None:
    path = local_path(v.root, manifest['files'].get('manuscript'))
    if not path.is_file():
        v.fail('missing_manuscript', 'Editable manuscript is absent')
        return
    try:
        with path.open('rb') as stream:
            raw = stream.read(MAX_MANUSCRIPT + 1)
        if len(raw) > MAX_MANUSCRIPT:
            raise InputError('Manuscript exceeds 16 MiB')
        text = raw.decode('utf-8')
    except (OSError, UnicodeError) as exc:
        raise InputError(f'Cannot read UTF-8 manuscript: {exc}') from exc
    v.require(bool(text.strip()), 'empty_manuscript', 'Manuscript has no content')
    v.require(not PLACEHOLDER.search(text), 'placeholder', 'Unfilled editorial placeholder remains')
    text = manuscript_prose(text, v)
    for label, records in (('chapter', chapters), ('claim', claims)):
        markers = re.findall(r'<!--\s*' + label + r':([A-Za-z0-9_-]+)\s*-->', text)
        for key in records:
            v.require(key in markers, f'missing_{label}_anchor', key)
        for key in set(markers):
            v.require(key in records, f'unknown_{label}_anchor', key)
        if label == 'chapter':
            v.require(len(markers) == len(set(markers)), 'duplicate_chapter_anchor', 'Each chapter has one anchor')
    definitions = re.findall(r'^\[\^([A-Za-z0-9_-]+)\]:[ \t]*(.*)$', text, re.M)
    ids = [d[0] for d in definitions]
    v.require(len(ids) == len(set(ids)), 'duplicate_footnote', 'Duplicate footnote definition')
    for key, body in definitions:
        v.require(bool(body.strip()), 'empty_footnote', key)
    prose = re.sub(r'^\[\^[A-Za-z0-9_-]+\]:.*$', '', text, flags=re.M)
    refs = set(re.findall(r'\[\^([A-Za-z0-9_-]+)\]', prose))
    for sid in refs:
        v.require(sid in ids, 'missing_footnote', sid)
    for sid in refs | set(ids):
        v.require(sid in sources, 'unknown_citation', sid)
    anchors = list(re.finditer(r'<!--\s*(?:claim|chapter):([A-Za-z0-9_-]+)\s*-->', prose))
    for index, anchor in enumerate(anchors):
        if not re.match(r'<!--\s*claim:', anchor.group(0)):
            continue
        cid = anchor.group(1)
        if cid not in claims:
            continue
        claim = claims[cid]
        end = anchors[index + 1].start() if index + 1 < len(anchors) else len(prose)
        block = prose[anchor.end():end]
        if claim.get('kind') == 'synthetic':
            label = claim.get('display_label', '')
            v.require(bool(label) and label in block, 'missing_synthetic_label', cid)
        elif claim.get('materiality') in ('critical', 'material'):
            support = {edge['source_id'] for edge in claim['evidence'] if edge.get('relation') == 'supports'}
            block_refs = set(re.findall(r'\[\^([A-Za-z0-9_-]+)\]', block))
            for sid in support:
                v.require(sid in refs, 'uncited_support', f'{cid}: {sid}')
                v.require(sid in block_refs, 'uncited_claim_support', f'{cid}: cite {sid} within this claim block')


def check_reviews(v: Review, manifest: dict, stage: str, fp: dict) -> None:
    reviews = v.indexed(manifest.get('checks'), 'checks')
    known = {item for items in CHECKS.values() for item in items}
    for key in reviews:
        v.require(key in known, 'unknown_check', key)
    for level in STAGES[:STAGES.index(stage) + 1]:
        for key in CHECKS[level]:
            if key not in reviews:
                v.fail('missing_check', key)
                continue
            review = reviews[key]
            v.require(review.get('status') == 'pass', 'check_not_pass', key)
            for field in ('reviewer', 'notes'):
                v.text(review, field, key)
            v.require(review.get('method') in ('manual', 'self_review', 'automated'), 'invalid_review_method', key)
            v.day(review.get('checked_on', ''), f'{key}.checked_on')
            v.artifact(review.get('evidence_file'), review.get('evidence_sha256'), key)
            recorded = obj(review.get('fingerprints'), f'{key}.fingerprints')
            for binding in BINDINGS[level]:
                v.require(fp.get(binding) is not None and recorded.get(binding) == fp[binding],
                          'stale_check', f'{key}: current {binding} fingerprint required')


def check_pdf(v: Review, manifest: dict, fp: dict) -> None:
    path = local_path(v.root, manifest['files'].get('pdf'))
    if not path.is_file():
        v.fail('missing_pdf', 'Final PDF is absent')
        return
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise InputError('Release-stage page checks require the optional pypdf dependency') from exc
    try:
        if path.stat().st_size > MAX_PDF:
            raise InputError('PDF exceeds 128 MiB; use a bounded approved inspection workflow')
        with path.open('rb') as stream:
            reader = PdfReader(stream, strict=True)
            if reader.is_encrypted:
                raise InputError('Encrypted PDF cannot be accepted by this page-check workflow')
            count = len(reader.pages)
    except InputError:
        raise
    except Exception as exc:
        raise InputError(f'Cannot inspect actual PDF page count: {exc}') from exc
    v.require(count > 0, 'empty_pdf', 'PDF contains no pages')
    visual = obj(manifest.get('visual'), 'visual')
    v.text(visual, 'renderer', 'visual')
    v.require(visual.get('pdf_sha256') == fp['pdf'], 'pdf_hash_mismatch', 'Visual review belongs to different PDF bytes')
    declared = integer(visual.get('page_count'), 'visual.page_count')
    v.require(declared == count, 'page_count_mismatch', f'Actual PDF pages: {count}; recorded: {declared}')
    seen = []
    for index, page in enumerate(array(visual.get('pages'), 'visual.pages')):
        page = obj(page, f'visual.pages[{index}]')
        number = integer(page.get('page'), 'visual page number')
        seen.append(number)
        v.require(page.get('status') == 'pass', 'page_not_pass', f'Page {number}')
        for key in ('reviewer', 'notes'):
            v.text(page, key, f'page {number}')
        v.day(page.get('inspected_on', ''), f'page {number}.inspected_on')
        v.artifact(page.get('render_path'), page.get('render_sha256'), f'page {number} render')
    v.require(len(seen) == count and set(seen) == set(range(1, count + 1)),
              'page_coverage', 'Exactly one inspection record per actual PDF page is required')
    deliverables = v.ids(manifest['files'].get('deliverables'), 'files.deliverables')
    v.require(bool(deliverables), 'empty_deliverables', 'Declare the actual delivery files')
    for relative in deliverables:
        file = local_path(v.root, relative)
        v.require(file.is_file(), 'missing_deliverable', relative)
        v.require(file.suffix.lower() not in ('.ttf', '.otf', '.woff', '.woff2') and file.name.lower() != '.env',
                  'forbidden_deliverable', f'{relative}: font files and credential stores are not deliverables')
    for key in ('manuscript', 'pdf'):
        v.require(manifest['files'][key] in deliverables, 'missing_deliverable_entry', key)


def validate(manifest: dict, root: Path, stage: str, as_of: date) -> dict:
    obj(manifest, 'manifest')
    if stage not in STAGES:
        raise InputError(f'Unsupported stage: {stage}')
    if not isinstance(as_of, date):
        raise InputError('Evaluation as_of must be a date')
    v = Review(root, as_of)
    v.require(manifest.get('schema') == SCHEMA, 'invalid_schema', f'Expected {SCHEMA}')
    _, chapters = check_scope(v, manifest)
    sources = check_sources(v, manifest)
    claims = check_claims(v, manifest, chapters, sources)
    fp = fingerprints(manifest, root)
    if stage in ('manuscript', 'release'):
        check_manuscript(v, manifest, chapters, sources, claims)
    check_reviews(v, manifest, stage, fp)
    if stage == 'release':
        check_pdf(v, manifest, fp)
    # Detect concurrent input-file changes across this validation pass.
    v.require(fingerprints(manifest, root) == fp, 'changed_during_validation', 'Manuscript or PDF changed while checking')
    return {'schema': 'cometweb.ebook-check-result/v1', 'stage': stage, 'as_of': as_of.isoformat(),
            'result': 'BLOCKED' if v.blockers else 'RECORDS_COMPLETE',
            'blockers': v.blockers, 'warnings': v.warnings, 'fingerprints': fp,
            'limits': 'Checks record consistency and file identity only; does not establish factual truth, review authenticity, visual quality, accessibility conformance, installation, or permission to publish.'}


def initialise(path: Path) -> None:
    if path.exists() or path.is_symlink():
        raise InputError('init requires a new nonexistent directory; nothing was overwritten')
    templates = Path(__file__).resolve().parents[1] / 'templates'
    names = ('publication.json', 'brief.md', 'manuscript.md', 'qa-report.md')
    if not all((templates / name).is_file() for name in names):
        raise InputError('Skill templates are missing; package is incomplete')
    try:
        path.mkdir(parents=False, exist_ok=False)
        for name in names:
            shutil.copyfile(templates / name, path / name)
    except OSError as exc:
        raise InputError(f'Cannot initialize workspace: {exc}') from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    init = commands.add_parser('init', help='Create a new incomplete publication workspace')
    init.add_argument('directory', type=Path)
    fingerprint = commands.add_parser('fingerprints', help='Print current fingerprints without changing reviews')
    fingerprint.add_argument('manifest', type=Path)
    check = commands.add_parser('validate', help='Validate records, not truth or visual quality')
    check.add_argument('manifest', type=Path)
    check.add_argument('--stage', choices=STAGES, required=True)
    check.add_argument('--as-of', type=date.fromisoformat, default=None)
    args = parser.parse_args(argv)
    try:
        if args.command == 'init':
            initialise(args.directory)
            out = {'result': 'INITIALIZED_DRAFT', 'path': str(args.directory), 'ready': False}
            code = 0
        else:
            before = sha256_file(args.manifest)
            manifest = load_json(args.manifest)
            root = args.manifest.resolve().parent
            if args.command == 'fingerprints':
                out = {'fingerprints': fingerprints(manifest, root), 'reviews_updated': False}
                code = 0
            else:
                out = validate(manifest, root, args.stage, args.as_of or current_date())
                code = 0 if out['result'] == 'RECORDS_COMPLETE' else 1
            if sha256_file(args.manifest) != before:
                raise InputError('Manifest changed during the check; rerun on a stable revision')
        print(json.dumps(out, ensure_ascii=False, indent=2, allow_nan=False))
        return code
    except (InputError, OSError, RecursionError) as exc:
        print(json.dumps({'result': 'INPUT_ERROR', 'error': str(exc)}, ensure_ascii=False))
        return 2


if __name__ == '__main__':
    sys.exit(main())
