#!/usr/bin/env python3
"""Language-native dead-code scanner for shrinkray.

Runs the best available dead-code tool for the project's language(s), then
runs the type checker with strict unused-symbol flags when available. Emits
a unified JSON the Dead Code Hunter agent verifies and applies.

Why this exists: LLMs are bad at *discovering* dead code by reading. SmellBench
(arXiv:2606.05574) reports the best agent at ~50% smell elimination, with the
failure mode being local focus and missing cross-file references. CodeTaste
(arXiv:2603.04177) shows agents implement specified refactorings well but
discover them poorly. Meanwhile, language-native AST tools (knip, vulture,
golang.org/x/tools/cmd/deadcode, cargo udeps/machete) are 100-1000x more
effective in practice — knip users report 40k-300k LOC removed per project
with no false positives. This script wraps those tools; the agent verifies.

Usage: deadcode_scan.py <project_dir> <output_dir>
Outputs:
  <output_dir>/deadcode_scan.json  — unified findings, one schema across tools
  <output_dir>/tools_used.json     — which tools ran, exit codes, raw output paths
  <output_dir>/raw/<tool>.txt      — raw stdout/stderr per tool, for audit

Unified finding schema:
  {
    "source": "vulture|knip|deadcode|cargo-udeps|cargo-machete|mypy|pyright|"
              "tsc|rustc|go-vet|staticcheck|fallback-ast",
    "file": "relative/path",
    "line": <int>,
    "name": "<symbol or empty>",
    "kind": "function|class|import|variable|export|file|unreachable|arg|...",
    "confidence": "high|medium|low",
    "message": "<raw tool message, truncated>",
    "evidence": "<short reason this is dead>"
  }

Tool-certified findings (anything a type checker or specialized dead-code tool
emitted) are marked `confidence: high`. Heuristic or fallback findings are
`medium` or `low`. The agent still verifies before applying — see the Dead
Code Hunter prompt.

Exit codes: 0 always (findings or none). Non-zero only on usage error.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

_SKIP_DIRS = {
    '.git', 'node_modules', '__pycache__', '.venv', 'venv', 'env',
    'dist', 'build', 'target', '.next', 'out', 'coverage',
    '.pytest_cache', '.mypy_cache', '.ruff_cache', 'vendor', '.cache',
    'shrinkray-output', 'stinky-output',
}

# Per-tool stdout size cap to keep JSON manageable.
_RAW_CAP_BYTES = 200_000


def _have(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def _detect_languages(root: Path) -> set[str]:
    langs: set[str] = set()
    if any((root / m).exists() for m in ('pyproject.toml', 'setup.py', 'setup.cfg')):
        langs.add('python')
    if (root / 'package.json').exists() or any(root.rglob('tsconfig*.json')):
        langs.add('ts')
    if (root / 'go.mod').exists():
        langs.add('go')
    if (root / 'Cargo.toml').exists():
        langs.add('rust')
    # Extension-based fallback for projects without manifests.
    if not langs:
        for path in root.rglob('*'):
            if not path.is_file():
                continue
            if any(part in _SKIP_DIRS for part in path.parts):
                continue
            suf = path.suffix.lower()
            if suf in ('.py',):
                langs.add('python')
            elif suf in ('.ts', '.tsx', '.js', '.jsx', '.mjs'):
                langs.add('ts')
            elif suf == '.go':
                langs.add('go')
            elif suf == '.rs':
                langs.add('rust')
            if len(langs) >= 4:
                break
    return langs


def _run(cmd: list[str], cwd: Path, timeout: int = 120) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True,
            timeout=timeout, check=False,
        )
        return proc.returncode, proc.stdout or '', proc.stderr or ''
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as exc:
        return 127, '', str(exc)


def _save_raw(out_dir: Path, tool: str, stdout: str, stderr: str) -> str:
    raw_dir = out_dir / 'raw'
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_dir / f'{tool}.txt'
    blob = f'=== STDOUT ===\n{stdout[:_RAW_CAP_BYTES]}\n=== STDERR ===\n{stderr[:_RAW_CAP_BYTES]}\n'
    path.write_text(blob, encoding='utf-8', errors='replace')
    return str(path.relative_to(out_dir))


# ── Python: vulture ──────────────────────────────────────────────────────

_VULTURE_RE = re.compile(
    r'^(?P<file>[^:]+):(?P<line>\d+):\s+(?P<message>.*?)\s*\((?P<conf>\d+)% confidence\)\s*$'
)


def _exclude_patterns() -> str:
    """Comma-separated glob patterns for `--exclude` flags of vulture etc."""
    return ','.join(f'*/{d}/*' for d in sorted(_SKIP_DIRS))


def _run_vulture(root: Path, out_dir: Path) -> tuple[list[dict], dict]:
    if not _have('python3'):
        return [], {'tool': 'vulture', 'ran': False, 'reason': 'python3 not available'}
    if _have('vulture'):
        cmd = ['vulture', '.', '--min-confidence', '60', '--exclude', _exclude_patterns()]
    else:
        # Probe whether the module is importable before claiming we can run.
        probe_rc, _, _ = _run(['python3', '-c', 'import vulture'], root, timeout=15)
        if probe_rc != 0:
            return [], {'tool': 'vulture', 'ran': False,
                        'reason': 'not installed (pip install vulture)'}
        cmd = ['python3', '-m', 'vulture', '.', '--min-confidence', '60',
               '--exclude', _exclude_patterns()]
    rc, stdout, stderr = _run(cmd, root)
    raw_path = _save_raw(out_dir, 'vulture', stdout, stderr)
    findings: list[dict] = []
    for line in stdout.splitlines():
        m = _VULTURE_RE.match(line.strip())
        if not m:
            continue
        conf = int(m.group('conf'))
        msg = m.group('message').strip()
        kind = _vulture_kind(msg)
        name = _vulture_name(msg)
        findings.append({
            'source': 'vulture',
            'file': m.group('file'),
            'line': int(m.group('line')),
            'name': name,
            'kind': kind,
            'confidence': 'high' if conf >= 90 else ('medium' if conf >= 80 else 'low'),
            'message': msg,
            'evidence': f'vulture reports {kind} as unused ({conf}% confidence)',
        })
    return findings, {
        'tool': 'vulture', 'ran': True, 'exit_code': rc,
        'findings_emitted': len(findings), 'raw_output': raw_path,
    }


def _vulture_kind(msg: str) -> str:
    m = re.search(r'\bunused\s+(\w+)', msg)
    if m:
        return m.group(1)
    if 'unreachable' in msg:
        return 'unreachable'
    return 'symbol'


def _vulture_name(msg: str) -> str:
    m = re.search(r"'([^']+)'", msg)
    return m.group(1) if m else ''


# ── Python: mypy (unused-related diagnostics) ────────────────────────────

_MYPY_UNUSED_RE = re.compile(
    r'^(?P<file>[^:]+):(?P<line>\d+)(?::\d+)?:\s+(?P<level>error|warning|note):\s+(?P<msg>.*?)(?:\s+\[.+?\])?\s*$'
)
_MYPY_UNUSED_PATTERNS = (
    'unused import',
    'is not used',
    'is never used',
    'unreachable',
    'redundant cast',
    'name defined but not used',
)


def _run_mypy(root: Path, out_dir: Path) -> tuple[list[dict], dict]:
    if not _have('mypy') and not _have('python3'):
        return [], {'tool': 'mypy', 'ran': False, 'reason': 'not installed'}
    has_mypy = _have('mypy')
    if not has_mypy:
        # Quick check: is mypy importable?
        rc, _, _ = _run(['python3', '-c', 'import mypy'], root, timeout=15)
        if rc != 0:
            return [], {'tool': 'mypy', 'ran': False, 'reason': 'not installed'}
    cmd = ['mypy'] if has_mypy else ['python3', '-m', 'mypy']
    cmd += ['.', '--warn-unused-ignores', '--warn-redundant-casts',
            '--warn-unreachable', '--no-error-summary', '--show-error-codes']
    rc, stdout, stderr = _run(cmd, root, timeout=300)
    raw_path = _save_raw(out_dir, 'mypy', stdout, stderr)
    findings: list[dict] = []
    for line in stdout.splitlines():
        m = _MYPY_UNUSED_RE.match(line.strip())
        if not m:
            continue
        msg = m.group('msg').strip()
        if not any(p in msg.lower() for p in _MYPY_UNUSED_PATTERNS):
            continue
        name = ''
        nm = re.search(r"'([^']+)'", msg)
        if nm:
            name = nm.group(1)
        findings.append({
            'source': 'mypy',
            'file': m.group('file'),
            'line': int(m.group('line')),
            'name': name,
            'kind': _mypy_kind(msg),
            'confidence': 'high',
            'message': msg,
            'evidence': 'mypy type checker diagnostic',
        })
    return findings, {
        'tool': 'mypy', 'ran': True, 'exit_code': rc,
        'findings_emitted': len(findings), 'raw_output': raw_path,
    }


def _mypy_kind(msg: str) -> str:
    low = msg.lower()
    if 'import' in low:
        return 'import'
    if 'unreachable' in low:
        return 'unreachable'
    if 'cast' in low:
        return 'redundant_cast'
    return 'symbol'


# ── JS/TS: knip ──────────────────────────────────────────────────────────

def _run_knip(root: Path, out_dir: Path) -> tuple[list[dict], dict]:
    if not (_have('knip') or _have('npx')):
        return [], {'tool': 'knip', 'ran': False, 'reason': 'not installed'}
    cmd = ['knip', '--reporter', 'json'] if _have('knip') else ['npx', '--no-install', 'knip', '--reporter', 'json']
    rc, stdout, stderr = _run(cmd, root, timeout=300)
    raw_path = _save_raw(out_dir, 'knip', stdout, stderr)
    findings: list[dict] = []
    try:
        data = json.loads(stdout) if stdout.strip() else {}
    except json.JSONDecodeError:
        data = {}
    # knip JSON schema: {files, issues, unlisted, duplicates, ...}
    for entry in data.get('files', []) or []:
        name = entry.get('name') or entry.get('path') or ''
        findings.append({
            'source': 'knip',
            'file': name,
            'line': int(entry.get('line', 0) or 0),
            'name': os.path.basename(name),
            'kind': 'file',
            'confidence': 'high',
            'message': 'knip: unused file',
            'evidence': 'knip entry-point analysis: file has no inbound references',
        })
    for issue in data.get('issues', []) or []:
        f = issue.get('file') or ''
        line = int(issue.get('line', 0) or 0)
        sym = issue.get('symbol') or issue.get('name') or ''
        kind = issue.get('symbolType') or issue.get('kind') or 'symbol'
        msg = issue.get('message') or f'knip: {kind} {sym} unused'
        findings.append({
            'source': 'knip',
            'file': f,
            'line': line,
            'name': sym,
            'kind': kind,
            'confidence': 'high',
            'message': msg,
            'evidence': 'knip export-graph analysis: symbol unreferenced from entry points',
        })
    return findings, {
        'tool': 'knip', 'ran': True, 'exit_code': rc,
        'findings_emitted': len(findings), 'raw_output': raw_path,
    }


# ── JS/TS: tsc with strict unused flags ──────────────────────────────────

_TSC_RE = re.compile(
    r'^(?P<file>[^(]+)\((?P<line>\d+),(?P<col>\d+)\):\s+(?P<level>error|warning|info):\s+(?P<msg>.*?)\s*$'
)
_TSC_UNUSED_CODES = ('TS6133', 'TS6196', 'TS6192', 'TS6133')


def _run_tsc(root: Path, out_dir: Path) -> tuple[list[dict], dict]:
    if not (_have('tsc') or _have('npx')):
        return [], {'tool': 'tsc', 'ran': False, 'reason': 'not installed'}
    if not (root / 'tsconfig.json').exists():
        return [], {'tool': 'tsc', 'ran': False, 'reason': 'no tsconfig.json'}
    cmd = ['tsc', '--noUnusedLocals', '--noUnusedParameters',
           '--noEmit', '--pretty', 'false'] if _have('tsc') else [
        'npx', '--no-install', 'tsc', '--noUnusedLocals', '--noUnusedParameters',
        '--noEmit', '--pretty', 'false']
    rc, stdout, stderr = _run(cmd, root, timeout=600)
    raw_path = _save_raw(out_dir, 'tsc', stdout, stderr)
    findings: list[dict] = []
    for line in stdout.splitlines():
        m = _TSC_RE.match(line.strip())
        if not m:
            continue
        msg = m.group('msg').strip()
        # TS6133: declared but never read; TS6196: unused import;
        # TS6192: all imports unused. Match by code or message text.
        if not (any(f'[{c}]' in line for c in _TSC_UNUSED_CODES)
                or 'is declared but' in msg.lower()
                or 'never read' in msg.lower()
                or 'is declared but its value' in msg.lower()):
            continue
        name = ''
        nm = re.search(r"'([^']+)'", msg)
        if nm:
            name = nm.group(1)
        kind = 'import' if 'import' in msg.lower() else 'variable'
        findings.append({
            'source': 'tsc',
            'file': m.group('file').strip(),
            'line': int(m.group('line')),
            'name': name,
            'kind': kind,
            'confidence': 'high',
            'message': msg,
            'evidence': 'TypeScript compiler diagnostic',
        })
    return findings, {
        'tool': 'tsc', 'ran': True, 'exit_code': rc,
        'findings_emitted': len(findings), 'raw_output': raw_path,
    }


# ── Go: deadcode + go vet ────────────────────────────────────────────────

_GO_VET_RE = re.compile(
    r'^(?P<file>[^:]+):(?P<line>\d+):(?P<col>\d+):\s+(?P<msg>.*?)(?:\s+\((?P<code>\w+)\))?\s*$'
)


def _run_go_deadcode(root: Path, out_dir: Path) -> tuple[list[dict], dict]:
    if not _have('deadcode'):
        return [], {'tool': 'deadcode', 'ran': False, 'reason': 'not installed (install: go install golang.org/x/tools/cmd/deadcode@latest)'}
    rc, stdout, stderr = _run(['deadcode', './...'], root, timeout=300)
    raw_path = _save_raw(out_dir, 'deadcode', stdout, stderr)
    findings: list[dict] = []
    for line in stdout.splitlines():
        parts = line.split()
        if len(parts) < 2:
            continue
        # deadcode output: <file>:<line>:<col>: <funcname>
        loc, _, rest = line.partition(':')
        if not loc or not rest:
            continue
        # Try to parse "<file>:<line>:<col>: <symbol>"
        m = re.match(r'(?P<file>[^:]+):(?P<line>\d+)(?::(?P<col>\d+))?\s*(?P<sym>.*)', line)
        if not m:
            continue
        findings.append({
            'source': 'deadcode',
            'file': m.group('file'),
            'line': int(m.group('line')),
            'name': m.group('sym').strip(),
            'kind': 'function',
            'confidence': 'high',
            'message': f'deadcode: unreachable function {m.group("sym").strip()}',
            'evidence': 'Go compiler reachability analysis',
        })
    return findings, {
        'tool': 'deadcode', 'ran': True, 'exit_code': rc,
        'findings_emitted': len(findings), 'raw_output': raw_path,
    }


def _run_go_vet(root: Path, out_dir: Path) -> tuple[list[dict], dict]:
    if not _have('go'):
        return [], {'tool': 'go-vet', 'ran': False, 'reason': 'go not installed'}
    rc, stdout, stderr = _run(['go', 'vet', './...'], root, timeout=300)
    raw_path = _save_raw(out_dir, 'go-vet', stdout, stderr)
    findings: list[dict] = []
    for line in stdout.splitlines():
        m = _GO_VET_RE.match(line.strip())
        if not m:
            continue
        msg = m.group('msg').strip()
        if not any(p in msg.lower() for p in ('unreachable', 'declared but', 'unused', 'not used')):
            continue
        name = ''
        nm = re.search(r"'([^']+)'", msg) or re.search(r'(\w+) declared', msg)
        if nm:
            name = nm.group(1)
        findings.append({
            'source': 'go-vet',
            'file': m.group('file'),
            'line': int(m.group('line')),
            'name': name,
            'kind': 'symbol',
            'confidence': 'high',
            'message': msg,
            'evidence': 'go vet diagnostic',
        })
    return findings, {
        'tool': 'go-vet', 'ran': True, 'exit_code': rc,
        'findings_emitted': len(findings), 'raw_output': raw_path,
    }


# ── Rust: cargo udeps / cargo machete ────────────────────────────────────

def _run_cargo_udeps(root: Path, out_dir: Path) -> tuple[list[dict], dict]:
    if not _have('cargo'):
        return [], {'tool': 'cargo-udeps', 'ran': False, 'reason': 'cargo not installed'}
    rc, stdout, stderr = _run(['cargo', '+nightly', 'udeps', '--output', 'json'],
                              root, timeout=600)
    raw_path = _save_raw(out_dir, 'cargo-udeps', stdout, stderr)
    findings: list[dict] = []
    if stdout.strip():
        try:
            data = json.loads(stdout)
        except json.JSONDecodeError:
            data = {}
        for cargo_file, deps in (data.get('unused_deps') or {}).items():
            for dep_name in deps:
                findings.append({
                    'source': 'cargo-udeps',
                    'file': 'Cargo.toml',
                    'line': 0,
                    'name': dep_name,
                    'kind': 'dependency',
                    'confidence': 'high',
                    'message': f'cargo-udeps: dependency {dep_name!r} unused in {cargo_file}',
                    'evidence': 'cargo-udeps build-graph analysis',
                })
    return findings, {
        'tool': 'cargo-udeps', 'ran': True, 'exit_code': rc,
        'findings_emitted': len(findings), 'raw_output': raw_path,
    }


def _run_rustc_deadcode(root: Path, out_dir: Path) -> tuple[list[dict], dict]:
    if not _have('cargo'):
        return [], {'tool': 'rustc', 'ran': False, 'reason': 'cargo not installed'}
    rc, stdout, stderr = _run(['cargo', 'check', '--message-format=short'],
                              root, timeout=600)
    raw_path = _save_raw(out_dir, 'rustc', stdout, stderr)
    findings: list[dict] = []
    # short format: <file>:<line>:<col>: <warning/error>: <message>
    for line in (stdout + '\n' + stderr).splitlines():
        m = re.match(
            r'(?P<file>[^:]+):(?P<line>\d+):(?P<col>\d+):\s+\w+:\s+(?P<msg>.*)', line)
        if not m:
            continue
        msg = m.group('msg').strip()
        if 'is never used' not in msg.lower() and 'dead_code' not in msg.lower() \
                and 'never read' not in msg.lower():
            continue
        name = ''
        nm = re.search(r"`([^`]+)`", msg)
        if nm:
            name = nm.group(1)
        findings.append({
            'source': 'rustc',
            'file': m.group('file'),
            'line': int(m.group('line')),
            'name': name,
            'kind': 'symbol',
            'confidence': 'high',
            'message': msg,
            'evidence': 'rustc dead_code lint',
        })
    return findings, {
        'tool': 'rustc', 'ran': True, 'exit_code': rc,
        'findings_emitted': len(findings), 'raw_output': raw_path,
    }


# ── Fallback: AST-based unused-symbol scan (when no native tool runs) ─────
#
# Lighter than vulture: per-file, finds top-level functions/classes whose name
# never appears as a Name/Attribute Load outside their own definition. Used
# only when vulture is unavailable. Lower confidence than the native tools.

import ast  # noqa: E402


def _fallback_ast_python(root: Path) -> list[dict]:
    findings: list[dict] = []
    defs: dict[str, list[tuple[str, int, str]]] = {}
    refs: set[str] = set()

    files = [p for p in root.rglob('*.py')
             if not any(part in _SKIP_DIRS for part in p.parts)]
    for fpath in files:
        try:
            tree = ast.parse(fpath.read_text(encoding='utf-8', errors='replace'))
        except (OSError, SyntaxError):
            continue
        rel = str(fpath.relative_to(root))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                # Top-level or class-level only
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    kind = 'async_function' if isinstance(node, ast.AsyncFunctionDef) else 'function'
                else:
                    kind = 'class'
                defs.setdefault(node.name, []).append((rel, node.lineno, kind))
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                refs.add(node.id)
            elif isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load):
                refs.add(node.attr)

    for name, occurrences in defs.items():
        if name.startswith('_'):
            continue
        if name in refs:
            continue
        # Heuristic: special methods are called implicitly; skip them.
        if name in ('__init__', '__main__', '__str__', '__repr__'):
            continue
        for rel, lineno, kind in occurrences:
            findings.append({
                'source': 'fallback-ast',
                'file': rel,
                'line': lineno,
                'name': name,
                'kind': kind,
                'confidence': 'low',
                'message': f'{kind} {name!r} has no Name/Attribute references outside its own def',
                'evidence': 'per-file AST scan (fallback); no cross-module dynamic-caller analysis',
            })
    return findings


# ── Main ─────────────────────────────────────────────────────────────────

def scan(project_dir: str, out_dir: str) -> dict:
    root = Path(project_dir).resolve()
    out = Path(out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    (out / 'raw').mkdir(parents=True, exist_ok=True)

    langs = _detect_languages(root)
    findings: list[dict] = []
    tools_used: list[dict] = []

    def _record(result: tuple[list[dict], dict]) -> None:
        f, meta = result
        findings.extend(f)
        tools_used.append(meta)

    any_native_ran = False

    if 'python' in langs:
        vulture_f, vulture_meta = _run_vulture(root, out)
        _record((vulture_f, vulture_meta))
        if vulture_meta.get('ran'):
            any_native_ran = True
        _record(_run_mypy(root, out))

    if 'ts' in langs:
        knip_f, knip_meta = _run_knip(root, out)
        _record((knip_f, knip_meta))
        if knip_meta.get('ran'):
            any_native_ran = True
        _record(_run_tsc(root, out))

    if 'go' in langs:
        dc_f, dc_meta = _run_go_deadcode(root, out)
        _record((dc_f, dc_meta))
        if dc_meta.get('ran'):
            any_native_ran = True
        _record(_run_go_vet(root, out))

    if 'rust' in langs:
        _record(_run_cargo_udeps(root, out))
        _record(_run_rustc_deadcode(root, out))

    # Fallback for Python when vulture was unavailable.
    if 'python' in langs and not any_native_ran:
        fallback = _fallback_ast_python(root)
        for f in fallback:
            findings.append(f)
        tools_used.append({
            'tool': 'fallback-ast', 'ran': True,
            'findings_emitted': len(fallback),
            'note': 'vulture not installed; using per-file AST fallback. '
                    'Install vulture (`pip install vulture`) for high-confidence results.',
        })

    # De-duplicate identical (source, file, line, name) tuples.
    seen: set[tuple] = set()
    deduped: list[dict] = []
    for f in findings:
        key = (f['source'], f['file'], f['line'], f['name'])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(f)

    # Sort: high → medium → low, then by file:line.
    rank = {'high': 0, 'medium': 1, 'low': 2}
    deduped.sort(key=lambda f: (rank.get(f['confidence'], 3), f['file'], f['line']))

    summary = {
        'total': len(deduped),
        'by_confidence': {
            'high': sum(1 for f in deduped if f['confidence'] == 'high'),
            'medium': sum(1 for f in deduped if f['confidence'] == 'medium'),
            'low': sum(1 for f in deduped if f['confidence'] == 'low'),
        },
        'by_source': {},
        'by_kind': {},
        'languages_detected': sorted(langs),
    }
    for f in deduped:
        summary['by_source'][f['source']] = summary['by_source'].get(f['source'], 0) + 1
        summary['by_kind'][f['kind']] = summary['by_kind'].get(f['kind'], 0) + 1

    payload = {
        'project': str(root),
        'summary': summary,
        'tools': tools_used,
        'findings': deduped,
        'notes': [
            'Findings with confidence=high are tool-certified (specialized dead-code '
            'tool or type checker emitted them). The agent verifies before applying.',
            'If no native tool ran for a language, install one: '
            'Python `pip install vulture`; JS/TS `npm i -D knip`; '
            'Go `go install golang.org/x/tools/cmd/deadcode@latest`.',
        ],
    }
    (out / 'deadcode_scan.json').write_text(
        json.dumps(payload, indent=2), encoding='utf-8')
    (out / 'tools_used.json').write_text(
        json.dumps(tools_used, indent=2), encoding='utf-8')

    return payload


def main() -> int:
    if len(sys.argv) < 3:
        sys.stderr.write(__doc__)
        return 2
    payload = scan(sys.argv[1], sys.argv[2])
    s = payload['summary']
    print(json.dumps({
        'project': payload['project'],
        'total_findings': s['total'],
        'high_confidence': s['by_confidence']['high'],
        'medium_confidence': s['by_confidence']['medium'],
        'low_confidence': s['by_confidence']['low'],
        'tools_ran': [t.get('tool') for t in payload['tools'] if t.get('ran')],
        'tools_skipped': [
            {'tool': t.get('tool'), 'reason': t.get('reason')}
            for t in payload['tools'] if not t.get('ran')
        ],
        'output': str(Path(sys.argv[2]) / 'deadcode_scan.json'),
    }, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
