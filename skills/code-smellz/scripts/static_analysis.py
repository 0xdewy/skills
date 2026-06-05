#!/usr/bin/env python3
"""Pre-pass static analysis: dead code detection and cross-file duplication.

Usage: static_analysis.py <project_dir> <output_dir>
Outputs:
  <output_dir>/dead_code.json  — unused functions, classes, imports, exports
  <output_dir>/dupes.json      — cross-file duplicate code blocks (5+ lines)
"""

import ast
import fnmatch
import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

_SKIP_DIRS = {
    '.git', 'node_modules', '__pycache__', '.venv', 'venv', 'env',
    'dist', 'build', 'target', '.next', 'out', 'coverage',
    '.pytest_cache', '.mypy_cache', 'vendor', '.cache',
    'stinky-output', 'resume-output',
}

_PY_EXT = {'.py'}
_JS_EXT = {'.js', '.mjs', '.cjs', '.jsx'}
_TS_EXT = {'.ts', '.mts', '.cts', '.tsx'}
_ALL_JS_TS = _JS_EXT | _TS_EXT


# ── helpers ──────────────────────────────────────────────────────────────

def _collect_files(root: Path, extensions: set[str]) -> list[Path]:
    files = []
    for path in root.rglob('*'):
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        if not path.is_file():
            continue
        if path.suffix.lower() in extensions:
            files.append(path)
    return files


def _hash_line(line: str) -> str:
    """Normalize and hash a source line for duplication detection."""
    stripped = ''.join(c for c in line if not c.isspace())
    if not stripped:
        return ''
    return hashlib.md5(stripped.encode()).hexdigest()[:8]


# ── Python dead-code detection (AST) ────────────────────────────────────

class _PyCollector(ast.NodeVisitor):
    """Collect all definitions and usages in a Python file."""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.defs: dict[str, tuple[str, int]] = {}   # name → (kind, lineno)
        self.refs: set[str] = set()                   # names referenced
        self.imports: dict[str, list[str]] = defaultdict(list)  # module → imported names
        self.import_used: dict[str, int] = defaultdict(int)     # module → use count

    def visit_FunctionDef(self, node: ast.FunctionDef):
        if not node.name.startswith('_') or node.name == '__init__':
            self.defs[node.name] = ('function', node.lineno)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        if not node.name.startswith('_') or node.name == '__init__':
            self.defs[node.name] = ('async_function', node.lineno)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        if not node.name.startswith('_'):
            self.defs[node.name] = ('class', node.lineno)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name):
        if isinstance(node.ctx, ast.Load):
            self.refs.add(node.id)

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            name = alias.asname or alias.name.split('.')[0]
            self.imports[self.filepath] = [name]
            self.refs.add(name)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        module = node.module or ''
        for alias in node.names:
            name = alias.asname or alias.name
            if name == '*':
                continue
            self.imports[module] = list(set(self.imports.get(module, []) + [name]))
            self.refs.add(name)


def _py_dead_code(root: Path) -> list[dict]:
    """Find dead Python functions, classes, and imports."""
    all_defs: dict[str, list[dict]] = defaultdict(list)  # name → [{file, kind, line}]
    all_refs: set[str] = set()
    unused_imports: list[dict] = []

    for fpath in _collect_files(root, _PY_EXT):
        try:
            source = fpath.read_text(encoding='utf-8', errors='replace')
        except OSError:
            continue
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue

        collector = _PyCollector(str(fpath.relative_to(root)))
        collector.visit(tree)

        # Track defs
        for name, (kind, lineno) in collector.defs.items():
            all_defs[name].append({
                'file': str(fpath.relative_to(root)),
                'line': lineno,
                'kind': kind,
            })

        all_refs.update(collector.refs)

        # Check for unused imports (within-file)
        import_lines: list[tuple[int, str, str]] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name.split('.')[0]
                    import_lines.append((node.lineno, name, alias.name))
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name != '*':
                        name = alias.asname or alias.name
                        import_lines.append((node.lineno, name, alias.name))

        # Simple unused import check (name not appearing as a bare word in file)
        lines = source.splitlines()
        for lineno, name, full_name in import_lines:
            if name not in collector.refs and name != '__future__':
                line_text = lines[lineno - 1].strip() if lineno <= len(lines) else ''
                unused_imports.append({
                    'file': str(fpath.relative_to(root)),
                    'line': lineno,
                    'kind': 'unused_import',
                    'name': name,
                    'full_name': full_name,
                    'evidence': line_text,
                })

    # Find defs never referenced anywhere
    dead_defs = []
    for name, def_list in all_defs.items():
        if name not in all_refs and name != '__init__':
            dead_defs.extend(def_list)

    result = dead_defs + unused_imports
    return result


# ── JS/TS export analysis ────────────────────────────────────────────────

_JS_EXPORT_RE = re.compile(
    r'export\s+(?:default\s+)?(?:const|let|var|function|class|async\s+function)\s+(\w+)'
)
_JS_NAMED_EXPORT_RE = re.compile(r'export\s*\{\s*([^}]+)\s*\}')
_JS_IMPORT_RE = re.compile(
    r'import\s*(?:\{[^}]*\}|\w+)\s*(?:\{[^}]*\})?\s*(?:,\s*(?:\{[^}]*\}|\w+))?\s*from\s*[\'\"]([^\'\"]+)[\'\"]'
)
_JS_IMPORT_NAME_RE = re.compile(r'import\s+\{([^}]+)\}')


def _js_ts_exports(root: Path) -> list[dict]:
    """Find JS/TS exports that may be unused (exported but never imported)."""
    exports: dict[str, list[dict]] = defaultdict(list)  # name → [{file, line, kind}]
    import_refs: set[str] = set()

    for fpath in _collect_files(root, _ALL_JS_TS):
        try:
            source = fpath.read_text(encoding='utf-8', errors='replace')
        except OSError:
            continue
        rel = str(fpath.relative_to(root))
        lines = source.splitlines()

        # Collect exports
        for i, line in enumerate(lines, 1):
            m = _JS_EXPORT_RE.search(line)
            if m:
                exports[m.group(1)].append({
                    'file': rel, 'line': i, 'kind': 'js_export',
                })
            m2 = _JS_NAMED_EXPORT_RE.search(line)
            if m2:
                for name in m2.group(1).split(','):
                    name = name.strip().split(' as ')[-1].strip()
                    exports[name].append({
                        'file': rel, 'line': i, 'kind': 'js_export',
                    })

    # Collect imports (names brought in from other files)
    for fpath in _collect_files(root, _ALL_JS_TS):
        try:
            source = fpath.read_text(encoding='utf-8', errors='replace')
        except OSError:
            continue
        for m in _JS_IMPORT_NAME_RE.finditer(source):
            for name in m.group(1).split(','):
                name = name.strip().split(' as ')[-1].strip()
                import_refs.add(name)

    # Exported but never imported anywhere = potentially dead
    dead_exports = []
    for name, elist in exports.items():
        if name not in import_refs:
            dead_exports.extend(elist)

    return dead_exports


# ── Cross-file duplication detection ─────────────────────────────────────

def _find_dupes(root: Path) -> list[dict]:
    """Find duplicate code blocks (5+ consecutive lines) across files."""
    all_exts = _PY_EXT | _ALL_JS_TS
    block_hashes: dict[str, list[tuple[str, int, int]]] = defaultdict(list)
    # key = concatenated line hashes → [(file, start_line, end_line)]

    for fpath in _collect_files(root, all_exts):
        try:
            source = fpath.read_text(encoding='utf-8', errors='replace')
        except OSError:
            continue
        rel = str(fpath.relative_to(root))
        lines = source.splitlines()
        line_hashes = []
        for line in lines:
            h = _hash_line(line)
            line_hashes.append(h)

        # Sliding window: find blocks of 5+ consecutive non-empty lines
        i = 0
        while i < len(line_hashes) - 4:
            chunk_hashes = []
            chunk_start = i
            j = i
            while j < len(line_hashes) and line_hashes[j]:
                chunk_hashes.append(line_hashes[j])
                j += 1
            if len(chunk_hashes) >= 5:
                key = '|'.join(chunk_hashes)
                block_hashes[key].append((rel, i + 1, j))
                i = j
            else:
                i += 1

    dupes = []
    for key, occurrences in block_hashes.items():
        if len(occurrences) < 2:
            continue
        # Only report if at least 2 different files
        files_involved = {o[0] for o in occurrences}
        if len(files_involved) < 2:
            continue
        dupes.append({
            'files': [{'file': f, 'line_start': s, 'line_end': e} for f, s, e in occurrences],
            'block_size_lines': len(key.split('|')),
            'occurrences': len(occurrences),
        })

    return dupes


# ── Type checker and linter detection ────────────────────────────────────

def _detect_typechecker(root: Path) -> dict:
    """Detect available type checker for the project."""
    # Python
    pp = root / 'pyproject.toml'
    if pp.exists():
        content = pp.read_text(encoding='utf-8', errors='replace')
        if 'mypy' in content or '[tool.mypy]' in content:
            return {'typechecker': 'mypy', 'command': 'python3 -m mypy . 2>&1'}
        if 'pyright' in content:
            return {'typechecker': 'pyright', 'command': 'npx pyright 2>&1'}

    sc = root / 'setup.cfg'
    if sc.exists() and 'mypy' in sc.read_text(encoding='utf-8', errors='replace'):
        return {'typechecker': 'mypy', 'command': 'python3 -m mypy . 2>&1'}

    # JS/TS
    tsconfig = root / 'tsconfig.json'
    if tsconfig.exists():
        return {'typechecker': 'tsc', 'command': 'npx tsc --noEmit 2>&1'}

    # JS-only
    pkg = root / 'package.json'
    if pkg.exists():
        return {'typechecker': 'tsc', 'command': 'npx tsc --noEmit 2>&1'}

    # Go
    if (root / 'go.mod').exists():
        return {'typechecker': 'go', 'command': 'go vet ./... 2>&1'}

    # Rust
    if (root / 'Cargo.toml').exists():
        return {'typechecker': 'cargo', 'command': 'cargo check 2>&1'}

    return {'typechecker': None, 'command': None}


def _detect_linter(root: Path) -> dict:
    """Detect available linter for the project."""
    # Python
    pp = root / 'pyproject.toml'
    if pp.exists():
        content = pp.read_text(encoding='utf-8', errors='replace')
        if 'ruff' in content or '[tool.ruff]' in content:
            return {'linter': 'ruff', 'command': 'python3 -m ruff check . 2>&1'}
        if 'flake8' in content:
            return {'linter': 'flake8', 'command': 'python3 -m flake8 . 2>&1'}

    sc = root / 'setup.cfg'
    if sc.exists():
        content = sc.read_text(encoding='utf-8', errors='replace')
        if 'flake8' in content:
            return {'linter': 'flake8', 'command': 'python3 -m flake8 . 2>&1'}

    # JS/TS
    pkg = root / 'package.json'
    if pkg.exists():
        content = pkg.read_text(encoding='utf-8', errors='replace')
        if 'eslint' in content:
            return {'linter': 'eslint', 'command': 'npx eslint . 2>&1'}
        if 'prettier' in content or '"lint"' in content:
            return {'linter': 'npm lint', 'command': 'npm run lint 2>&1 || true'}

    # Go
    if (root / 'go.mod').exists():
        return {'linter': 'golangci-lint', 'command': 'golangci-lint run ./... 2>&1'}

    # Rust
    if (root / 'Cargo.toml').exists():
        return {'linter': 'clippy', 'command': 'cargo clippy 2>&1'}

    return {'linter': None, 'command': None}


# ── Formatter detection ──────────────────────────────────────────────────

def _detect_formatter(root: Path) -> dict:
    """Detect available formatter for the project."""
    # Python
    pp = root / 'pyproject.toml'
    if pp.exists():
        content = pp.read_text(encoding='utf-8', errors='replace')
        if 'ruff' in content or '[tool.ruff]' in content:
            return {'formatter': 'ruff', 'command': 'python3 -m ruff format . 2>&1'}
        if 'black' in content or '[tool.black]' in content:
            return {'formatter': 'black', 'command': 'python3 -m black . 2>&1'}

    sc = root / 'setup.cfg'
    if sc.exists() and 'black' in sc.read_text(encoding='utf-8', errors='replace'):
        return {'formatter': 'black', 'command': 'python3 -m black . 2>&1'}

    # JS/TS
    pkg = root / 'package.json'
    if pkg.exists():
        content = pkg.read_text(encoding='utf-8', errors='replace')
        if 'prettier' in content:
            return {'formatter': 'prettier', 'command': 'npx prettier --write . 2>&1'}
        if '"format"' in content:
            return {'formatter': 'npm format', 'command': 'npm run format 2>&1 || true'}

    # Go
    if (root / 'go.mod').exists():
        return {'formatter': 'gofmt', 'command': 'gofmt -w . 2>&1'}

    # Rust
    if (root / 'Cargo.toml').exists():
        return {'formatter': 'rustfmt', 'command': 'cargo fmt 2>&1'}

    return {'formatter': None, 'command': None}


# ── Dependency CVE scanner detection ─────────────────────────────────────

def _detect_cve_scanner(root: Path) -> dict:
    """Detect available dependency vulnerability scanner."""
    # npm/yarn
    pkg_lock = root / 'package-lock.json'
    yarn_lock = root / 'yarn.lock'
    if pkg_lock.exists():
        return {'scanner': 'npm audit', 'command': 'npm audit --json 2>&1 || true'}
    if yarn_lock.exists():
        return {'scanner': 'yarn audit', 'command': 'yarn audit --json 2>&1 || true'}

    # Python
    for lock in ('poetry.lock', 'Pipfile.lock', 'requirements.txt'):
        if (root / lock).exists():
            return {'scanner': 'pip-audit', 'command': 'pip-audit 2>&1 || safety check 2>&1 || true'}

    # Rust
    if (root / 'Cargo.lock').exists():
        return {'scanner': 'cargo audit', 'command': 'cargo audit 2>&1 || true'}

    # Go
    if (root / 'go.sum').exists():
        return {'scanner': 'govulncheck', 'command': 'govulncheck ./... 2>&1 || true'}

    return {'scanner': None, 'command': None}


# ── .stinkyignore reader ─────────────────────────────────────────────────

def _load_stinkyignore(root: Path, output_dir: Path):
    """Load .stinkyignore patterns and write exclusions.txt."""
    ignore_file = root / '.stinkyignore'
    exclusions_path = output_dir / 'exclusions.txt'

    if not ignore_file.exists():
        exclusions_path.write_text('')
        return []

    patterns = []
    for line in ignore_file.read_text(encoding='utf-8', errors='replace').splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith('#'):
            patterns.append(stripped)

    exclusions_path.write_text('\n'.join(patterns))
    return patterns


def _should_exclude(rel_path: str, patterns: list[str]) -> bool:
    """Check if a relative path matches any .stinkyignore pattern."""
    for pattern in patterns:
        negate = pattern.startswith('!')
        p = pattern[1:] if negate else pattern
        if fnmatch.fnmatch(rel_path, p) or fnmatch.fnmatch(f'/{rel_path}', p):
            return not negate
    return False


# ── main ─────────────────────────────────────────────────────────────────

def main() -> None:
    if len(sys.argv) < 3:
        sys.stderr.write('Usage: static_analysis.py <project_dir> <output_dir>\n')
        sys.exit(1)

    project_dir = sys.argv[1]
    output_dir = sys.argv[2]
    root = Path(project_dir)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # .stinkyignore
    stinky_patterns = _load_stinkyignore(root, out)

    # Dead code (skip excluded files)
    dead_py = [d for d in _py_dead_code(root)
               if not _should_exclude(d['file'], stinky_patterns)]
    dead_js = [d for d in _js_ts_exports(root)
               if not _should_exclude(d['file'], stinky_patterns)]
    dead_all = dead_py + dead_js
    (out / 'dead_code.json').write_text(
        json.dumps({'total': len(dead_all), 'findings': dead_all}, indent=2)
    )

    # Duplicates (skip excluded files in occurrences)
    dupes = _find_dupes(root)
    filtered_dupes = []
    for d in dupes:
        d['files'] = [f for f in d['files']
                      if not _should_exclude(f['file'], stinky_patterns)]
        if len(d['files']) >= 2:
            filtered_dupes.append(d)
    (out / 'dupes.json').write_text(
        json.dumps({'total': len(filtered_dupes), 'findings': filtered_dupes}, indent=2)
    )

    # Type checker / linter / formatter / CVE
    tc = _detect_typechecker(root)
    linter = _detect_linter(root)
    fmt = _detect_formatter(root)
    cve = _detect_cve_scanner(root)
    tools_json = {
        'typechecker': tc['typechecker'],
        'typecheck_cmd': tc['command'],
        'linter': linter['linter'],
        'lint_cmd': linter['command'],
        'formatter': fmt['formatter'],
        'format_cmd': fmt['command'],
        'cve_scanner': cve['scanner'],
        'dep_audit_cmd': cve['command'],
    }
    (out / 'tools.json').write_text(json.dumps(tools_json, indent=2))

    print(json.dumps({
        'dead_code_count': len(dead_all),
        'dupe_blocks': len(filtered_dupes),
        'stinkyignore_patterns': len(stinky_patterns),
        'dead_code_file': str(out / 'dead_code.json'),
        'dupes_file': str(out / 'dupes.json'),
        'tools_file': str(out / 'tools.json'),
    }))


if __name__ == '__main__':
    main()
