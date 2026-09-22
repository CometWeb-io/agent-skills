#!/usr/bin/env python3
"""Read-only repository topology and change-surface inventory for Repo Roaster."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

DEFAULT_EXCLUDES = {
    '.git','node_modules','vendor','dist','build','.next','.svelte-kit','.venv','venv','__pycache__',
    'coverage','target','.turbo','.cache','.idea','.vscode','.gradle','.pytest_cache'
}
KEY_FILES = {
    'package.json','pnpm-workspace.yaml','pnpm-lock.yaml','yarn.lock','package-lock.json','bun.lockb','bun.lock',
    'pyproject.toml','requirements.txt','poetry.lock','uv.lock','go.mod','go.sum','Cargo.toml','Cargo.lock',
    'composer.json','composer.lock','pom.xml','build.gradle','build.gradle.kts','settings.gradle','settings.gradle.kts',
    'Gemfile','Gemfile.lock','Package.swift','Podfile','Podfile.lock','Dockerfile','docker-compose.yml','docker-compose.yaml',
    'Makefile','justfile','Taskfile.yml','README.md','AGENTS.md','CONTRIBUTING.md','CODEOWNERS','LICENSE','SECURITY.md'
}
LOCK_FILES = {'pnpm-lock.yaml','yarn.lock','package-lock.json','bun.lockb','bun.lock','poetry.lock','uv.lock','go.sum','Cargo.lock','composer.lock','Gemfile.lock','Podfile.lock'}
MANIFEST_FILES = {'package.json','pyproject.toml','requirements.txt','go.mod','Cargo.toml','composer.json','pom.xml','build.gradle','build.gradle.kts','Gemfile','Package.swift','Podfile'}
TEST_DIRS = {'test','tests','spec','specs','__tests__','e2e','integration'}
MIGRATION_DIRS = {'migration','migrations','alembic','prisma','drizzle','schema_migrations'}
ENV_NAMES = {'.env.example','.env.sample','.env.template','env.example','example.env'}
ENTRY_NAMES = {'main.py','app.py','server.py','manage.py','index.ts','index.js','server.ts','server.js','main.ts','main.js','main.go','main.rs','main.kt','Program.cs'}
CONFIG_SUFFIXES = {'.yml','.yaml','.toml','.ini','.cfg','.conf','.properties'}
INFRA_SUFFIXES = {'.tf','.tfvars','.hcl'}
INFRA_TOKENS = {'infra','infrastructure','terraform','k8s','kubernetes','helm','deploy','deployment','docker','compose','ansible','pulumi','cloudformation'}
OBS_TOKENS = {'observability','metrics','telemetry','logging','logger','otel','opentelemetry','sentry','datadog','grafana','prometheus','alert','alerts','tracing','trace'}
RISK_TOKENS = {'auth','authentication','authorization','permission','permissions','tenant','billing','payment','payments','invoice','checkout','entitlement','webhook','admin','session','secret','secrets','queue','worker','job','jobs','cron','migration','migrations','delete','destructive','sudo','root','token','tokens','oauth','sso'}
DATA_TOKENS = {'schema','schemas','database','db','model','models','repository','repositories','storage','sql','prisma','drizzle','alembic','orm'}
JOB_TOKENS = {'queue','queues','worker','workers','job','jobs','cron','scheduler','scheduled','celery','bull','sidekiq','rq'}
AUTH_TOKENS = {'auth','authentication','authorization','permission','permissions','rbac','acl','session','oauth','sso','jwt','tenant'}
GENERATED_TOKENS = {'generated','gen','dist','build','vendor'}
SECRETISH_NAMES = {'.env','.npmrc','.pypirc','credentials','credentials.json','service-account.json','id_rsa','id_ed25519'}
SOURCE_ROOTS = {'src','app','lib','server','backend','frontend','api','services','packages','apps','cmd','internal','pkg','crates','modules'}
CI_PREFIXES = {'.github/workflows/','.gitlab-ci.yml','azure-pipelines.yml','Jenkinsfile','.circleci/','buildkite/'}

LANGUAGE_BY_SUFFIX = {
    '.py':'Python','.js':'JavaScript','.jsx':'JavaScript','.ts':'TypeScript','.tsx':'TypeScript','.go':'Go','.rs':'Rust',
    '.java':'Java','.kt':'Kotlin','.kts':'Kotlin','.cs':'C#','.php':'PHP','.rb':'Ruby','.swift':'Swift','.dart':'Dart',
    '.c':'C','.h':'C/C++ header','.cc':'C++','.cpp':'C++','.cxx':'C++','.vue':'Vue','.svelte':'Svelte','.sql':'SQL',
    '.tf':'Terraform','.sh':'Shell','.bash':'Shell','.zsh':'Shell','.ps1':'PowerShell','.proto':'Protobuf'
}


def _path_tokens(rel: str) -> set[str]:
    parts = rel.lower().replace('-', '/').replace('_', '/').replace('.', '/').split('/')
    return {p for p in parts if p}


def _safe_json(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        return data if isinstance(data, dict) else None
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None


def _workspace_hints(root: Path) -> list[str]:
    out: list[str] = []
    package = _safe_json(root / 'package.json')
    if package:
        workspaces = package.get('workspaces')
        if isinstance(workspaces, list):
            out.extend(str(x) for x in workspaces if isinstance(x, str))
        elif isinstance(workspaces, dict) and isinstance(workspaces.get('packages'), list):
            out.extend(str(x) for x in workspaces['packages'] if isinstance(x, str))
    pnpm = root / 'pnpm-workspace.yaml'
    if pnpm.is_file():
        try:
            for line in pnpm.read_text(encoding='utf-8').splitlines():
                stripped = line.strip().lstrip('-').strip().strip('"\'')
                if stripped and not stripped.startswith(('packages:', '#')) and ('*' in stripped or '/' in stripped):
                    out.append(stripped)
        except (OSError, UnicodeDecodeError):
            pass
    return sorted(set(out))


def _git_run(root: Path, *args: str, timeout: int = 8) -> str | None:
    try:
        proc = subprocess.run(['git', '-C', str(root), *args], capture_output=True, text=True, timeout=timeout)
        return proc.stdout.strip() if proc.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def _git_snapshot(root: Path) -> dict[str, Any]:
    sha = _git_run(root, 'rev-parse', 'HEAD')
    branch = _git_run(root, 'rev-parse', '--abbrev-ref', 'HEAD')
    status = _git_run(root, 'status', '--porcelain')
    toplevel = _git_run(root, 'rev-parse', '--show-toplevel')
    return {
        'available': bool(sha),
        'head_sha': sha,
        'branch': branch,
        'working_tree': 'clean' if status == '' else ('dirty' if status is not None else 'unknown'),
        'toplevel': toplevel,
    }


def _git_change_surface(root: Path, base: str, head: str) -> dict[str, Any]:
    name_status = _git_run(root, 'diff', '--name-status', f'{base}...{head}')
    numstat = _git_run(root, 'diff', '--numstat', f'{base}...{head}')
    changed: list[dict[str, str]] = []
    if name_status:
        for line in name_status.splitlines():
            parts = line.split('\t')
            if len(parts) >= 2:
                changed.append({'status': parts[0], 'path': parts[-1]})
    stats: list[dict[str, Any]] = []
    if numstat:
        for line in numstat.splitlines():
            parts = line.split('\t')
            if len(parts) >= 3:
                add, delete, path = parts[0], parts[1], parts[-1]
                stats.append({
                    'path': path,
                    'added': int(add) if add.isdigit() else None,
                    'deleted': int(delete) if delete.isdigit() else None,
                })
    return {
        'base': base,
        'head': head,
        'changed_files': changed,
        'line_stats': stats,
        'available': name_status is not None,
    }


def _package_managers(names: set[str]) -> list[str]:
    out: list[str] = []
    if {'pnpm-lock.yaml','pnpm-workspace.yaml'} & names: out.append('pnpm')
    if 'yarn.lock' in names: out.append('yarn')
    if 'package-lock.json' in names: out.append('npm')
    if {'bun.lockb','bun.lock'} & names: out.append('bun')
    if 'poetry.lock' in names: out.append('poetry')
    if 'uv.lock' in names: out.append('uv')
    if any(n.startswith('requirements') for n in names): out.append('pip/requirements')
    if 'go.mod' in names: out.append('go modules')
    if 'Cargo.toml' in names: out.append('cargo')
    if 'composer.json' in names: out.append('composer')
    if 'pom.xml' in names: out.append('maven')
    if {'build.gradle','build.gradle.kts'} & names: out.append('gradle')
    if 'Gemfile' in names: out.append('bundler')
    if 'Package.swift' in names: out.append('swiftpm')
    if 'Podfile' in names: out.append('cocoapods')
    return sorted(set(out))


def inventory(root: Path, excludes: set[str], largest_n: int = 20, include_git: bool = False, base: str | None = None, head: str | None = None) -> dict[str, Any]:
    root = root.resolve()
    counts: Counter[str] = Counter()
    bytes_by_ext: Counter[str] = Counter()
    language_files: Counter[str] = Counter()
    language_bytes: Counter[str] = Counter()
    total = 0
    total_bytes = 0
    top: set[str] = set()
    key_files: list[str] = []
    manifests: list[str] = []
    lockfiles: list[str] = []
    tests: list[str] = []
    workflows: list[str] = []
    migrations: list[str] = []
    env_examples: list[str] = []
    entry_candidates: list[str] = []
    configs: list[str] = []
    files_by_size: list[tuple[int, str]] = []
    symlinks: list[str] = []
    infra: list[str] = []
    observability: list[str] = []
    risk_surfaces: list[str] = []
    data_surfaces: list[str] = []
    job_surfaces: list[str] = []
    auth_surfaces: list[str] = []
    generated_candidates: list[str] = []
    secretish_files: list[str] = []
    source_roots: set[str] = set()

    for current, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = [d for d in dirs if d not in excludes]
        current_path = Path(current)
        rel_dir = current_path.relative_to(root)
        if rel_dir.parts:
            top.add(rel_dir.parts[0])
            if rel_dir.parts[0].lower() in SOURCE_ROOTS:
                source_roots.add(rel_dir.parts[0])
        for name in files:
            path = current_path / name
            try:
                if path.is_symlink():
                    symlinks.append(path.relative_to(root).as_posix())
                size = path.stat().st_size
            except OSError:
                continue
            rel = path.relative_to(root).as_posix()
            tokens = _path_tokens(rel)
            total += 1
            total_bytes += size
            files_by_size.append((size, rel))
            ext = path.suffix.lower() or '<no_ext>'
            counts[ext] += 1
            bytes_by_ext[ext] += size
            language = LANGUAGE_BY_SUFFIX.get(path.suffix.lower())
            if language:
                language_files[language] += 1
                language_bytes[language] += size
            lower_parts = {x.lower() for x in path.parts}
            if name in KEY_FILES or (name.startswith('requirements') and name.endswith('.txt')):
                key_files.append(rel)
            if name in MANIFEST_FILES or (name.startswith('requirements') and name.endswith('.txt')):
                manifests.append(rel)
            if name in LOCK_FILES:
                lockfiles.append(rel)
            if lower_parts & TEST_DIRS or name.startswith('test_') or name.endswith(('_test.py','.spec.ts','.test.ts','.spec.js','.test.js','.spec.tsx','.test.tsx','.spec.jsx','.test.jsx')):
                tests.append(rel)
            if rel.startswith('.github/workflows/') and rel.endswith(('.yml','.yaml')):
                workflows.append(rel)
            elif name in CI_PREFIXES or any(rel.startswith(prefix) for prefix in CI_PREFIXES if prefix.endswith('/')):
                workflows.append(rel)
            if lower_parts & MIGRATION_DIRS or 'migration' in name.lower():
                migrations.append(rel)
            if name in ENV_NAMES:
                env_examples.append(rel)
            if name in ENTRY_NAMES or name.startswith('main.') or name.startswith('server.'):
                entry_candidates.append(rel)
            if path.suffix.lower() in CONFIG_SUFFIXES or name in {'package.json','pyproject.toml','tsconfig.json','vite.config.ts','vite.config.js','svelte.config.js','next.config.js','next.config.mjs'}:
                configs.append(rel)
            if path.suffix.lower() in INFRA_SUFFIXES or tokens & INFRA_TOKENS or name in {'Dockerfile','docker-compose.yml','docker-compose.yaml'}:
                infra.append(rel)
            if tokens & OBS_TOKENS:
                observability.append(rel)
            if tokens & RISK_TOKENS:
                risk_surfaces.append(rel)
            if tokens & DATA_TOKENS or path.suffix.lower() == '.sql':
                data_surfaces.append(rel)
            if tokens & JOB_TOKENS:
                job_surfaces.append(rel)
            if tokens & AUTH_TOKENS:
                auth_surfaces.append(rel)
            if tokens & GENERATED_TOKENS:
                generated_candidates.append(rel)
            if name.lower() in SECRETISH_NAMES or name.lower().endswith(('.pem','.key','.p12','.pfx')):
                secretish_files.append(rel)

    largest = [{'path': rel, 'bytes': size} for size, rel in sorted(files_by_size, reverse=True)[:largest_n]]
    names = {Path(x).name for x in key_files}
    report: dict[str, Any] = {
        'root': str(root),
        'file_count': total,
        'total_bytes': total_bytes,
        'top_level': sorted(top),
        'source_roots': sorted(source_roots),
        'workspace_hints': _workspace_hints(root),
        'extensions': [{'ext': k, 'files': counts[k], 'bytes': bytes_by_ext[k]} for k in sorted(counts, key=lambda x: (-counts[x], x))],
        'languages': [{'language': k, 'files': language_files[k], 'bytes': language_bytes[k]} for k in sorted(language_files, key=lambda x: (-language_files[x], x))],
        'key_files': sorted(set(key_files)),
        'manifest_files': sorted(set(manifests)),
        'lock_files': sorted(set(lockfiles)),
        'package_managers': _package_managers(names),
        'entrypoint_candidates': sorted(set(entry_candidates)),
        'test_files': sorted(set(tests)),
        'workflow_files': sorted(set(workflows)),
        'migration_files': sorted(set(migrations)),
        'env_example_files': sorted(set(env_examples)),
        'config_files': sorted(set(configs)),
        'infrastructure_files': sorted(set(infra)),
        'observability_files': sorted(set(observability)),
        'risk_surface_files': sorted(set(risk_surfaces)),
        'auth_surface_files': sorted(set(auth_surfaces)),
        'job_surface_files': sorted(set(job_surfaces)),
        'data_surface_files': sorted(set(data_surfaces)),
        'generated_or_vendor_candidates': sorted(set(generated_candidates)),
        'secretish_file_names': sorted(set(secretish_files)),
        'symlinks': sorted(set(symlinks)),
        'largest_files': largest,
        'excluded_dir_names': sorted(excludes),
    }
    if include_git or base or head:
        report['git'] = _git_snapshot(root)
    if base or head:
        if not base or not head:
            raise ValueError('base and head must be supplied together')
        report['change_surface'] = _git_change_surface(root, base, head)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', nargs='?', default='.')
    parser.add_argument('--exclude', action='append', default=[])
    parser.add_argument('--largest', type=int, default=20)
    parser.add_argument('--git', action='store_true', help='include read-only git HEAD/branch/working-tree snapshot')
    parser.add_argument('--base', help='optional git base ref for change-surface inventory')
    parser.add_argument('--head', help='optional git head ref for change-surface inventory')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    root = Path(args.root)
    if not root.is_dir():
        parser.error('root must be an existing directory')
    if args.largest < 0:
        parser.error('--largest must be >= 0')
    if bool(args.base) != bool(args.head):
        parser.error('--base and --head must be supplied together')
    try:
        report = inventory(root, DEFAULT_EXCLUDES | set(args.exclude), args.largest, include_git=args.git, base=args.base, head=args.head)
    except ValueError as exc:
        parser.error(str(exc))
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"root: {report['root']}")
        print(f"files: {report['file_count']}")
        print(f"bytes: {report['total_bytes']}")
        print('languages:')
        for row in report['languages'][:10]:
            print(f"  - {row['language']}: {row['files']} files")
        print('key files:')
        for item in report['key_files']:
            print(f"  - {item}")
        print(f"tests: {len(report['test_files'])}")
        print(f"workflows: {len(report['workflow_files'])}")
        print(f"migrations: {len(report['migration_files'])}")
        print(f"risk surfaces: {len(report['risk_surface_files'])}")
        print(f"auth surfaces: {len(report['auth_surface_files'])}")
        print(f"job surfaces: {len(report['job_surface_files'])}")
        print(f"infrastructure files: {len(report['infrastructure_files'])}")
        if 'change_surface' in report:
            print(f"changed files: {len(report['change_surface']['changed_files'])}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
