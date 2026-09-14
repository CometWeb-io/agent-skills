#!/usr/bin/env python3
"""Create a local, conflict-aware candidate without modifying a source checkout.

Reads two pinned Git trees; merges overlay changes into HEAD in a NEW directory.
No fetch, checkout, commit, push, hooks, install, test or repository script execution.
Hashes bind bytes, not authorship. A conflict-free merge is NOT semantic validation.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import tempfile
import unicodedata

MAX_FILE = 16 * 1024 * 1024
MAX_TOTAL = 128 * 1024 * 1024
MAX_ENTRIES = 20000
HEX40 = re.compile(r'[0-9a-f]{40}\Z')
HEX64 = re.compile(r'[0-9a-f]{64}\Z')
RETIRED = {'ai-antipattern-writing', 'ai-anti-pattern', 'ai-anti-pattern-writing'}


def require(ok: bool, why: str) -> None:
    if not ok:
        raise ValueError(why)


def digest(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()


def unique(items):
    result = {}
    for key, value in items:
        require(key not in result, 'duplicate JSON key')
        result[key] = value
    return result


def path_name(name: str) -> str:
    require(isinstance(name, str) and 0 < len(name) <= 1024, 'invalid relative filename')
    require(not PurePosixPath(name).is_absolute() and '\\' not in name and ':' not in name
            and not any(ord(c) < 32 for c in name), 'nonportable filename')
    parts = name.split('/')
    require(all(p not in {'', '.', '..'} and p.casefold() != '.git' for p in parts), 'unsafe path')
    require(not any(p.endswith((' ', '.')) for p in parts), 'nonportable trailing dot or space')
    return name


def real_path(path: Path) -> Path:
    path = path.absolute()
    require(not any(p.is_symlink() for p in (path, *path.parents)), 'symlink in filesystem path')
    return path.resolve()


def read_regular(path: Path) -> bytes:
    path = real_path(path)
    require(path.is_file() and stat.S_ISREG(path.stat().st_mode), 'missing or special file')
    require(path.stat().st_size <= MAX_FILE, 'file exceeds size budget')
    with path.open('rb') as stream:
        blob = stream.read(MAX_FILE + 1)
    require(len(blob) <= MAX_FILE, 'file grew beyond size budget')
    return blob


def git_env() -> dict:
    env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
               GIT_NO_REPLACE_OBJECTS='1', GIT_OPTIONAL_LOCKS='0', GIT_TERMINAL_PROMPT='0')
    return env


def git(root: Path, *args: str) -> bytes:
    return subprocess.run(['git', '-c', 'core.fsmonitor=false', '-c', 'core.hooksPath=' + os.devnull,
                           '-c', 'core.pager=cat', '-C', str(root), *args],
                          env=git_env(), capture_output=True, check=True, timeout=60).stdout


def tree(root: Path, revision: str) -> dict:
    require(bool(HEX40.fullmatch(revision)), 'a full immutable Git SHA is required')
    rows = git(root, 'ls-tree', '-r', '-z', '-l', '--full-tree', revision).split(b'\0')
    require(len(rows) - 1 <= MAX_ENTRIES, 'tree has too many files')
    output, names, total = {}, set(), 0
    for row in rows:
        if not row:
            continue
        header, raw_name = row.split(b'\t', 1)
        mode, kind, oid, size = header.decode('ascii').split()
        name = path_name(raw_name.decode('utf-8'))
        folded = unicodedata.normalize('NFC', name).casefold()
        require(folded not in names, 'case/Unicode-normalized tree path collision')
        names.add(folded)
        require(kind == 'blob' and mode in {'100644', '100755'}, 'symlinks/submodules/special Git entries require manual integration')
        length = int(size)
        require(0 <= length <= MAX_FILE, 'Git blob exceeds file budget')
        total += length
        require(total <= MAX_TOTAL, 'Git tree exceeds byte budget')
        output[name] = {'oid': oid, 'size': length, 'mode': mode}
    return output


def blobs(root: Path, entries: dict) -> dict[str, bytes]:
    # --batch does not execute content filters. Advertised sizes bound aggregate output.
    wanted = {meta['oid']: meta['size'] for meta in entries.values()}
    if not wanted:
        return {}
    proc = subprocess.run(['git', '-C', str(root), 'cat-file', '--batch'],
                          input=('\n'.join(wanted) + '\n').encode(), env=git_env(),
                          capture_output=True, check=True, timeout=60)
    raw, offset, by_oid = proc.stdout, 0, {}
    require(len(raw) <= MAX_TOTAL + MAX_ENTRIES * 100, 'batch output exceeds budget')
    for oid, size in wanted.items():
        end = raw.find(b'\n', offset)
        require(end >= offset, 'truncated Git batch header')
        require(raw[offset:end].decode() == f'{oid} blob {size}', 'Git batch header mismatch')
        value = raw[end+1:end+1+size]
        require(raw[end+1+size:end+2+size] == b'\n', 'truncated Git blob')
        require(hashlib.sha1(f'blob {len(value)}\0'.encode() + value).hexdigest() == oid, 'Git object bytes do not match their ID')
        by_oid[oid] = value
        offset = end + 2 + size
    require(offset == len(raw), 'unexpected extra Git batch output')
    return {name: by_oid[meta['oid']] for name, meta in entries.items()}


def overlay_files(overlay: Path, manifest_path: Path, expected_hash: str | None = None) -> tuple[dict, dict]:
    raw = read_regular(manifest_path)
    if expected_hash is not None:
        require(bool(HEX64.fullmatch(expected_hash)) and digest(raw) == expected_hash, 'overlay manifest pin mismatch')
    manifest = json.loads(raw, object_pairs_hook=unique)
    require(isinstance(manifest, dict) and manifest.get('schema') == 'cometweb.overlay/v1', 'unknown overlay manifest')
    require(bool(HEX40.fullmatch(str(manifest.get('canonical_base', '')))), 'invalid canonical base')
    expected = manifest.get('files')
    require(isinstance(expected, dict) and 0 < len(expected) <= 4096, 'empty/oversized overlay manifest')
    real_path(overlay)
    output, total, normalized = {}, 0, set()
    for name, sha in expected.items():
        path_name(name)
        folded = unicodedata.normalize('NFC', name).casefold()
        require(folded not in normalized, 'overlay path collision')
        normalized.add(folded)
        require(isinstance(sha, str) and bool(HEX64.fullmatch(sha)), 'invalid file hash')
        value = read_regular(overlay / name)
        require(digest(value) == sha, 'overlay file does not match manifest')
        total += len(value)
        require(total <= MAX_TOTAL, 'overlay exceeds byte budget')
        output[name] = value
    return manifest, output


def merge_file(current: bytes, base: bytes, incoming: bytes) -> tuple[str, bytes | None]:
    if current == incoming:
        return 'already_present', current
    if current == base:
        return 'replace_unchanged_base', incoming
    if incoming == base:
        return 'preserve_newer_head', current
    try:
        for value in (current, base, incoming):
            require(b'\0' not in value, 'binary')
            value.decode('utf-8')
    except (ValueError, UnicodeError):
        return 'conflict_binary', None
    with tempfile.TemporaryDirectory(prefix='cw-three-way-') as tmp:
        paths = [Path(tmp) / name for name in ('current', 'base', 'incoming')]
        for path, value in zip(paths, (current, base, incoming)):
            path.write_bytes(value)
        proc = subprocess.run(['git', 'merge-file', '-p', '--diff3', '-L', 'current', '-L', 'base', '-L', 'overlay',
                               *map(str, paths)], cwd=tmp, env=git_env(), capture_output=True, timeout=30)
        if proc.returncode == 0:
            require(len(proc.stdout) <= MAX_FILE, 'merged file exceeds budget')
            return 'merged_text_review_required', proc.stdout
        if 1 <= proc.returncode <= 127:
            return 'conflict_text', None
        raise ValueError('three-way merge could not complete')


def preview(checkout: Path, overlay: Path, manifest_path: Path, output: Path, *,
            include_workflows: bool = False, expected_manifest_sha256: str | None = None) -> dict:
    checkout, overlay, output = map(real_path, (checkout, overlay, output))
    require(checkout.is_dir() and overlay.is_dir(), 'checkout and overlay must be directories')
    require(not output.exists() and output.parent.is_dir(), 'output must be a new directory with an existing parent')
    for source in (checkout, overlay):
        require(not output.is_relative_to(source) and not source.is_relative_to(output), 'output must not overlap source directories')
    root = Path(git(checkout, 'rev-parse', '--show-toplevel').decode().strip()).absolute()
    require(root == checkout, 'checkout must be the Git root')
    manifest, incoming = overlay_files(overlay, manifest_path, expected_manifest_sha256)
    base_sha = manifest['canonical_base']
    head = git(checkout, 'rev-parse', 'HEAD').decode().strip()
    require(bool(HEX40.fullmatch(head)), 'unsupported Git object format')
    # Known base must be an ancestor; unrelated histories are not silently overlaid.
    git(checkout, 'merge-base', '--is-ancestor', base_sha, head)
    base_tree, head_tree = tree(checkout, base_sha), tree(checkout, head)
    base = blobs(checkout, {n: meta for n, meta in base_tree.items() if n in incoming})
    current = blobs(checkout, head_tree)
    dirty = [name for name, value in current.items()
             if not (checkout / name).is_file() or read_regular(checkout / name) != value
             or bool((checkout / name).stat().st_mode & 0o111) != (head_tree[name]['mode'] == '100755')]
    require(not dirty, 'tracked working-tree changes require separate review; no files exported')
    # Untracked files never become source evidence or enter the candidate export.
    untracked = git(checkout, 'ls-files', '--others', '--exclude-standard', '-z')
    untracked_count = sum(bool(p) for p in untracked.split(b'\0'))
    candidate, plan, conflicts, omitted = dict(current), [], [], []
    for name, value in sorted(incoming.items()):
        if name.startswith('.github/workflows/') and not include_workflows:
            omitted.append(name); status = 'excluded_workflow_review'
        elif name not in base:
            if name in current and current[name] != value:
                status = 'conflict_added_on_both_sides'; conflicts.append(name)
            else:
                status = 'already_present' if name in current else 'add'
                candidate[name] = value
        elif name not in current:
            if value == base[name]:
                status = 'preserve_upstream_deletion'
            else:
                status = 'conflict_deleted_upstream'; conflicts.append(name)
        else:
            status, merged = merge_file(current[name], base[name], value)
            if merged is None:
                conflicts.append(name)
            else:
                candidate[name] = merged
        plan.append({'path': name, 'status': status, 'incoming_sha256': digest(value),
                     'current_sha256': digest(current[name]) if name in current else None})
    # Reject directory/file and case collisions before touching even the new output.
    names = set(candidate)
    folded = [unicodedata.normalize('NFC', n).casefold() for n in names]
    require(len(folded) == len(set(folded)), 'merged tree has a case/Unicode collision')
    folded_names = set(folded)
    for name in names:
        require(not any(unicodedata.normalize('NFC', str(parent)).casefold() in folded_names for parent in PurePosixPath(name).parents if str(parent) != '.'), 'merged tree has file/directory collision')
        parts = PurePosixPath(name).parts
        require(not (len(parts) > 1 and parts[0] == 'skills' and parts[1] in RETIRED), 'retired skill is present; manual reconciliation required')
    require(sum(map(len, candidate.values())) <= MAX_TOTAL, 'candidate exceeds total budget')
    require(git(checkout, 'rev-parse', 'HEAD').decode().strip() == head, 'HEAD changed during preview')
    result = {'schema': 'cometweb.integration-preview/v1', 'base_revision': base_sha, 'head_revision': head,
              'status': 'conflicts' if conflicts else 'prepared_with_workflow_exclusions' if omitted else 'prepared',
              'manifest_pin': 'matched' if expected_manifest_sha256 else 'not_requested',
              'conflicts': conflicts, 'excluded_workflows': omitted, 'untracked_files_not_exported': untracked_count,
              'plan': plan, 'source_checkout_modified': False, 'remote_write_attempted': False,
              'source_authentication': 'not_performed', 'semantic_validation': 'not_run',
              'visibility': 'local_private_export', 'snapshot_basis': 'pinned_HEAD_not_untracked_work',
              'source_revision_in_export': 'recorded_in_preview_not_a_git_checkout',
              'full_repository_tests': 'not_run', 'model_calls': 0}
    output.mkdir(mode=0o700)  # Exclusive. Never replace an existing directory.
    try:
        if not conflicts:
            target = output / 'candidate'; target.mkdir()
            for name, value in candidate.items():
                path = target / name; path.parent.mkdir(parents=True, exist_ok=True)
                with path.open('xb') as stream:
                    stream.write(value)
                path.chmod(0o755 if head_tree.get(name, {}).get('mode') == '100755' else 0o644)
            (output / 'candidate-files.json').write_bytes(canonical({name: digest(value) for name, value in sorted(candidate.items())}))
            result['candidate_file_count'] = len(candidate)
        (output / 'preview.json').write_bytes(canonical(result))
    except BaseException:
        shutil.rmtree(output)  # Only our exclusively created scratch output, never the checkout.
        raise
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkout', type=Path, required=True)
    parser.add_argument('--overlay', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--expected-manifest-sha256')
    parser.add_argument('--include-workflows', action='store_true')
    args = parser.parse_args(argv)
    try:
        result = preview(args.checkout, args.overlay, args.manifest, args.output,
                         include_workflows=args.include_workflows,
                         expected_manifest_sha256=args.expected_manifest_sha256)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if result['status'] == 'conflicts' else 0
    except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError):
        print(json.dumps({'status': 'blocked', 'source_checkout_modified': False,
                          'remote_write_attempted': False, 'reason': 'preflight_or_preview_failed; inspect inputs and local logs without exposing secrets'}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
