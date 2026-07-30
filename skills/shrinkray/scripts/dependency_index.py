#!/usr/bin/env python3
"""Cross-file dependency index for shrinkray.

Builds the kind of call/import graph LLMs cannot reliably hold in working
memory across an 8000-LOC codebase. SmellBench (arXiv:2606.05574) identifies
the failure mode directly: *"a focus on local code smells and a lack of
cross-file understanding."* CodeTaste (arXiv:2603.04177) confirms agents
implement specified refactorings well but discover poorly. This script hands
agents cross-file relationships as data so they can reason about reachability
without re-reading the codebase into context.

Usage: dependency_index.py <project_dir> <output_dir>
Outputs:
  <output_dir>/dependency_index.json

Schema (top-level keys):
  {
    "symbols": {
      "<name>": {
        "kind": "function|class|method|interface|component|constant",
        "definitions": [{"file": "...", "line": N, "language": "..."}],
        "call_sites": [{"file": "...", "line": N, "context": "..."}],
        "caller_count": N,
        "def_count": N
      }, ...
    },
    "files": {
      "<relative/path>": {
        "language": "...",
        "imports": ["<module>", ...],
        "exported_symbols": ["<name>", ...],
        "imported_by": ["<relative/path>", ...],
        "import_count": N
      }, ...
    },
    "single_caller_symbols": [
      # Symbols with exactly one external call site — inlining candidates.
      {"name": "...", "definition_file": "...", "definition_line": N,
       "sole_caller_file": "...", "sole_caller_line": N, "kind": "..."}
    ],
    "single_importer_files": [
      # Files imported by exactly one other file — module merger candidates.
      {"file": "...", "sole_importer": "..."}
    ],
    "single_implementor_interfaces": [
      # Interfaces/abstract bases with exactly one implementor — inlining
      # candidates. (Python heuristic: class with <=1 subclass.)
      {"name": "...", "file": "...", "implementors": ["..."]}
    ],
    "summary": {
      "total_symbols": N, "single_caller_symbols": N,
      "single_importer_files": N, "single_implementor_interfaces": N,
      "languages_detected": [...], "files_indexed": N
    }
  }

Exit codes: 0 always (index or empty). Non-zero only on usage error.
"""
from __future__ import annotations

import ast
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

_SKIP_DIRS = {
    '.git', 'node_modules', '__pycache__', '.venv', 'venv', 'env',
    'dist', 'build', 'target', '.next', 'out', 'coverage',
    '.pytest_cache', '.mypy_cache', '.ruff_cache', 'vendor', '.cache',
    'shrinkray-output', 'stinky-output',
}

_PY_EXT = {'.py'}
_JS_TS_EXT = {'.js', '.mjs', '.cjs', '.jsx', '.ts', '.tsx', '.mts', '.cts'}
_GO_EXT = {'.go'}
_RS_EXT = {'.rs'}

_LANGUAGE_BY_EXT = {
    '.py': 'python',
    '.js': 'javascript', '.mjs': 'javascript', '.cjs': 'javascript',
    '.jsx': 'javascript',
    '.ts': 'typescript', '.tsx': 'typescript', '.mts': 'typescript',
    '.cts': 'typescript',
    '.go': 'go', '.rs': 'rust',
}


def _collect(root: Path) -> list[Path]:
    out = []
    for path in root.rglob('*'):
        if not path.is_file():
            continue
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in (_PY_EXT | _JS_TS_EXT | _GO_EXT | _RS_EXT):
            out.append(path)
    return out


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding='utf-8', errors='replace')
    except OSError:
        return ''


# ── Python: AST-based definition + reference collection ──────────────────

class _PyIndexer:
    """Collect defined names (with kind) and referenced names per file."""

    def __init__(self, root: Path):
        self.root = root
        # name → list of (file, line, kind)
        self.definitions: dict[str, list[tuple[str, int, str]]] = defaultdict(list)
        # name → list of (file, line, context)
        self.references: dict[str, list[tuple[str, int, str]]] = defaultdict(list)
        # file → imported module names
        self.file_imports: dict[str, list[str]] = defaultdict(list)
        # file → exported (top-level def) names
        self.file_exports: dict[str, list[str]] = defaultdict(list)
        # class → subclass names (heuristic inheritance tracker)
        self.class_children: dict[str, list[str]] = defaultdict(list)

    def index_file(self, path: Path) -> None:
        rel = str(path.relative_to(self.root))
        source = _read(path)
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return

        # Pass 1: definitions + class inheritance
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                kind = 'async_function' if isinstance(node, ast.AsyncFunctionDef) else 'function'
                # Method vs function: depth check
                self.definitions[node.name].append((rel, node.lineno, kind))
                if rel not in self.file_exports or True:
                    if node.name not in self.file_exports[rel]:
                        self.file_exports[rel].append(node.name)
            elif isinstance(node, ast.ClassDef):
                self.definitions[node.name].append((rel, node.lineno, 'class'))
                if node.name not in self.file_exports[rel]:
                    self.file_exports[rel].append(node.name)
                # Track inheritance
                for base in node.bases:
                    base_name = self._dotted_name(base)
                    if base_name:
                        self.class_children[base_name].append(node.name)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                names = []
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        names.append(alias.asname or alias.name.split('.')[0])
                else:
                    mod = node.module or ''
                    if mod:
                        self.file_imports[rel].append(mod)
                    for alias in node.names:
                        if alias.name != '*':
                            names.append(alias.asname or alias.name)
                for n in names:
                    # Treat imported names as references to that name (for caller counting)
                    self.references.setdefault(n, []).append((rel, node.lineno, 'import'))

        # Pass 2: references (Name Loads, Attribute Loads)
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                self.references.setdefault(node.id, []).append(
                    (rel, node.lineno, 'name_load'))
            elif isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load):
                # Track attribute access by attr name; helps with method callers
                self.references.setdefault(node.attr, []).append(
                    (rel, node.lineno, 'attribute_load'))

    @staticmethod
    def _dotted_name(node: ast.expr) -> str | None:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            base = _PyIndexer._dotted_name(node.value)
            return f'{base}.{node.attr}' if base else node.attr
        return None


# ── JS/TS: regex-based definition + import/export collection ─────────────

_JS_EXPORT_RE = re.compile(
    r'\bexport\s+(?:default\s+)?(?:async\s+)?'
    r'(?:function|class|const|let|var)\s+(\w+)')
_JS_EXPORT_LIST_RE = re.compile(r'\bexport\s*\{([^}]+)\}')
_JS_IMPORT_FROM_RE = re.compile(
    r'\bimport\s+(?:[\w\s,{}*]+?\s+from\s+)?[\'"]([^\'"]+)[\'"]')
_JS_IMPORT_NAMES_RE = re.compile(r'\bimport\s+\{([^}]+)\}')
_JS_FUNC_DEF_RE = re.compile(
    r'\b(?:export\s+(?:default\s+)?(?:async\s+)?)?'
    r'(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\()')
_JS_CLASS_DEF_RE = re.compile(
    r'\b(?:export\s+(?:default\s+)?)?class\s+(\w+)')
_JS_INTERFACE_DEF_RE = re.compile(
    r'\b(?:export\s+)?interface\s+(\w+)')
_JS_TYPE_DEF_RE = re.compile(
    r'\b(?:export\s+)?type\s+(\w+)\s*=')


def _index_js_ts(path: Path, root: Path,
                 definitions: dict, references: dict,
                 file_imports: dict, file_exports: dict) -> None:
    rel = str(path.relative_to(root))
    source = _read(path)
    if not source:
        return

    for line_num, line in enumerate(source.splitlines(), 1):
        for m in _JS_FUNC_DEF_RE.finditer(line):
            name = m.group(1) or m.group(2)
            if name:
                definitions[name].append((rel, line_num, 'function'))
                file_exports[rel].append(name)
        for m in _JS_CLASS_DEF_RE.finditer(line):
            definitions[m.group(1)].append((rel, line_num, 'class'))
            file_exports[rel].append(m.group(1))
        for m in _JS_INTERFACE_DEF_RE.finditer(line):
            definitions[m.group(1)].append((rel, line_num, 'interface'))
            file_exports[rel].append(m.group(1))
        for m in _JS_TYPE_DEF_RE.finditer(line):
            definitions[m.group(1)].append((rel, line_num, 'type_alias'))

        # Exports via `export {a, b}`
        for m in _JS_EXPORT_LIST_RE.finditer(line):
            for raw in m.group(1).split(','):
                name = raw.strip().split(' as ')[-1].strip()
                if name and name not in file_exports[rel]:
                    file_exports[rel].append(name)
                # treat as a definition if not yet seen
                if name and name not in definitions:
                    definitions[name].append((rel, line_num, 'export'))

        # Imports: capture names (for caller tracking) and source paths (for importer map)
        for m in _JS_IMPORT_FROM_RE.finditer(line):
            file_imports[rel].append(m.group(1))
        for m in _JS_IMPORT_NAMES_RE.finditer(line):
            for raw in m.group(1).split(','):
                name = raw.strip().split(' as ')[0].strip()
                if name:
                    references.setdefault(name, []).append((rel, line_num, 'import'))

        # Word-boundary usage of identifiers (lightweight caller counting)
        # Skip declaration lines themselves — handled by def patterns above.
        if not _JS_FUNC_DEF_RE.search(line) and not _JS_CLASS_DEF_RE.search(line):
            for word in re.findall(r'\b[a-zA-Z_]\w*\b', line):
                if word in ('return', 'if', 'else', 'for', 'while', 'function',
                            'class', 'const', 'let', 'var', 'import', 'export',
                            'from', 'default', 'new', 'await', 'async', 'typeof',
                            'this', 'super', 'true', 'false', 'null', 'undefined'):
                    continue
                references.setdefault(word, []).append((rel, line_num, 'use'))


# ── Go: regex-based function/type definitions + imports ─────────────────

_GO_FUNC_RE = re.compile(r'^\s*func\s+(?:\([^)]+\)\s+)?(\w+)\s*\(', re.MULTILINE)
_GO_TYPE_RE = re.compile(r'^\s*type\s+(\w+)\s+(?:interface|struct)', re.MULTILINE)
_GO_IMPORT_RE = re.compile(r'^\s*"([^"]+)"', re.MULTILINE)


def _index_go(path: Path, root: Path,
              definitions: dict, references: dict,
              file_imports: dict, file_exports: dict) -> None:
    rel = str(path.relative_to(root))
    source = _read(path)
    if not source:
        return
    for m in _GO_FUNC_RE.finditer(source):
        # Convert byte offset to line number
        line = source.count('\n', 0, m.start()) + 1
        definitions[m.group(1)].append((rel, line, 'function'))
        # Go: capitalised = exported
        if m.group(1)[0].isupper():
            file_exports[rel].append(m.group(1))
    for m in _GO_TYPE_RE.finditer(source):
        line = source.count('\n', 0, m.start()) + 1
        definitions[m.group(1)].append((rel, line, 'type'))
        if m.group(1)[0].isupper():
            file_exports[rel].append(m.group(1))
    # Reference: bare word usage (rough)
    for word in re.findall(r'\b[a-zA-Z_]\w*\b', source):
        references.setdefault(word, []).append(
            (rel, 0, 'use'))  # line 0 = unknown


# ── Rust: regex-based ────────────────────────────────────────────────────

_RS_FUNC_RE = re.compile(
    r'^\s*(?:pub\s+)?(?:async\s+)?fn\s+(\w+)', re.MULTILINE)
_RS_STRUCT_TRAIT_RE = re.compile(
    r'^\s*(?:pub\s+)?(?:struct|trait|enum)\s+(\w+)', re.MULTILINE)
_RS_USE_RE = re.compile(r'^\s*use\s+([\w:]+)', re.MULTILINE)


def _index_rust(path: Path, root: Path,
                definitions: dict, references: dict,
                file_imports: dict, file_exports: dict) -> None:
    rel = str(path.relative_to(root))
    source = _read(path)
    if not source:
        return
    for m in _RS_FUNC_RE.finditer(source):
        line = source.count('\n', 0, m.start()) + 1
        definitions[m.group(1)].append((rel, line, 'function'))
    for m in _RS_STRUCT_TRAIT_RE.finditer(source):
        line = source.count('\n', 0, m.start()) + 1
        kind = 'trait' if 'trait ' in m.group(0) else 'type'
        definitions[m.group(1)].append((rel, line, kind))
    for m in _RS_USE_RE.finditer(source):
        name = m.group(1).split(':').pop().split('::').pop()
        file_imports[rel].append(name)
        references.setdefault(name, []).append(
            (rel, source.count('\n', 0, m.start()) + 1, 'use'))


# ── Build the unified index ──────────────────────────────────────────────

def build_index(project_dir: str, out_dir: str) -> dict:
    root = Path(project_dir).resolve()
    out = Path(out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    py_indexer = _PyIndexer(root)
    definitions: dict[str, list[tuple[str, int, str]]] = defaultdict(list)
    references: dict[str, list[tuple[str, int, str]]] = defaultdict(list)
    file_imports: dict[str, list[str]] = defaultdict(list)
    file_exports: dict[str, list[str]] = defaultdict(list)
    file_language: dict[str, str] = {}

    files = _collect(root)
    for path in files:
        ext = path.suffix.lower()
        lang = _LANGUAGE_BY_EXT.get(ext, 'unknown')
        rel = str(path.relative_to(root))
        file_language[rel] = lang
        if lang == 'python':
            py_indexer.index_file(path)
        elif lang in ('javascript', 'typescript'):
            _index_js_ts(path, root, definitions, references,
                         file_imports, file_exports)
        elif lang == 'go':
            _index_go(path, root, definitions, references,
                      file_imports, file_exports)
        elif lang == 'rust':
            _index_rust(path, root, definitions, references,
                        file_imports, file_exports)

    # Merge Python results into the shared dicts.
    for name, defs in py_indexer.definitions.items():
        definitions[name].extend(defs)
    for name, refs in py_indexer.references.items():
        references[name].extend(refs)
    for f, imps in py_indexer.file_imports.items():
        file_imports[f].extend(imps)
    for f, exps in py_indexer.file_exports.items():
        file_exports[f].extend(exps)
    class_children = dict(py_indexer.class_children)

    # Build symbols map with caller_count (external call sites only).
    symbols: dict[str, dict] = {}
    for name, defs in definitions.items():
        # References that are NOT inside the definition's own file count as external.
        def_files = {d[0] for d in defs}
        external_call_sites = []
        internal_call_sites = []
        for ref_file, ref_line, ctx in references.get(name, []):
            if ref_file in def_files and ctx in ('name_load', 'use', 'import'):
                # Could be self-reference or unrelated same-file use.
                internal_call_sites.append(
                    {'file': ref_file, 'line': ref_line, 'context': ctx})
            else:
                external_call_sites.append(
                    {'file': ref_file, 'line': ref_line, 'context': ctx})
        symbols[name] = {
            'kind': defs[0][2] if defs else 'unknown',
            'definitions': [
                {'file': f, 'line': ln, 'language': file_language.get(f, '?')}
                for f, ln, _ in defs
            ],
            'call_sites': external_call_sites[:50],  # cap for size
            'caller_count': len(external_call_sites),
            'def_count': len(defs),
        }

    # Build files map with importer counts.
    files_map: dict[str, dict] = {}
    # Build reverse map: for each module imported, who imports it?
    # Convert file_imports (file → [modules]) into imported_by (file → [importers]).
    module_to_files: dict[str, list[str]] = defaultdict(list)
    # Each file maps to its module-ish path. We use the relative path without ext
    # as a coarse module handle.
    file_to_module: dict[str, str] = {}
    for rel in file_language:
        file_to_module[rel] = rel.rsplit('.', 1)[0].replace('/', '.')
    for importer, modules in file_imports.items():
        for mod in modules:
            # Try to resolve mod to an actual file in the project.
            target = _resolve_module(mod, importer, file_to_module)
            if target:
                module_to_files[target].append(importer)

    for rel, lang in file_language.items():
        imported_by = module_to_files.get(rel, [])
        files_map[rel] = {
            'language': lang,
            'imports': sorted(set(file_imports.get(rel, [])))[:50],
            'exported_symbols': sorted(set(file_exports.get(rel, [])))[:50],
            'imported_by': sorted(set(imported_by)),
            'import_count': len(set(imported_by)),
        }

    # Single-caller symbols: definitions with exactly one external call site.
    single_caller = []
    for name, info in symbols.items():
        if info['caller_count'] == 1 and info['def_count'] == 1:
            cs = info['call_sites'][0]
            single_caller.append({
                'name': name,
                'definition_file': info['definitions'][0]['file'],
                'definition_line': info['definitions'][0]['line'],
                'sole_caller_file': cs['file'],
                'sole_caller_line': cs['line'],
                'kind': info['kind'],
            })

    # Single-importer files: files imported by exactly one other file.
    single_importer = []
    for rel, info in files_map.items():
        if info['import_count'] == 1:
            single_importer.append({
                'file': rel,
                'sole_importer': info['imported_by'][0],
            })

    # Single-implementor interfaces (Python-only heuristic via class_children).
    single_impl = []
    for cls, children in class_children.items():
        unique_children = sorted(set(children))
        if len(unique_children) == 1:
            defs = symbols.get(cls, {}).get('definitions', [])
            single_impl.append({
                'name': cls,
                'file': defs[0]['file'] if defs else '?',
                'implementors': unique_children,
            })

    # Filter out generic/common names from the candidate lists to reduce noise.
    _NOISE = {'main', 'test', 'run', 'init', 'setup', 'teardown', 'logger',
              'print', 'log', 'self', 'cls', 'this', 'super', 'true', 'false',
              'null', 'none', 'value', 'key', 'item', 'data', 'result',
              'args', 'kwargs', 'error', 'exception', 'str', 'int', 'float',
              'bool', 'list', 'dict', 'set', 'tuple'}
    single_caller = [c for c in single_caller
                     if c['name'].lower() not in _NOISE
                     and not c['name'].startswith('_')][:200]
    single_impl = [c for c in single_impl
                   if c['name'].lower() not in _NOISE
                   and not c['name'].startswith('_')][:200]

    index = {
        'symbols': dict(sorted(symbols.items())),
        'files': files_map,
        'single_caller_symbols': single_caller,
        'single_importer_files': single_importer,
        'single_implementor_interfaces': single_impl,
        'summary': {
            'total_symbols': len(symbols),
            'single_caller_symbols': len(single_caller),
            'single_importer_files': len(single_importer),
            'single_implementor_interfaces': len(single_impl),
            'languages_detected': sorted(set(file_language.values())),
            'files_indexed': len(file_language),
        },
    }
    (out / 'dependency_index.json').write_text(
        json.dumps(index, indent=2), encoding='utf-8')
    return index


def _resolve_module(mod: str, importer: str,
                    file_to_module: dict[str, str]) -> str | None:
    """Best-effort: resolve an imported module name to a project file path."""
    if not mod:
        return None
    # JS/TS relative imports: './foo' or '../bar/baz'
    if mod.startswith('.'):
        importer_dir = '/'.join(importer.split('/')[:-1])
        candidate = (importer_dir + '/' + mod).lstrip('./').lstrip('/')
        # Try with extensions
        for ext in ('.ts', '.tsx', '.js', '.jsx', '.mjs', '/index.ts', '/index.js'):
            cand = candidate + ext if not candidate.endswith(ext) else candidate
            if cand in file_to_module.values() or cand.replace('/', '.') in file_to_module.values():
                return cand
        return None
    # Python absolute imports: a.b.c → a/b/c.py or a/b/c/__init__.py
    candidate = mod.replace('.', '/')
    for ext in ('.py', '/__init__.py'):
        cand = candidate + ext
        if cand in file_to_module or any(
                f.startswith(cand.rsplit('.', 1)[0]) for f in file_to_module):
            return cand
    return None


def main() -> int:
    if len(sys.argv) < 3:
        sys.stderr.write(__doc__)
        return 2
    index = build_index(sys.argv[1], sys.argv[2])
    s = index['summary']
    print(json.dumps({
        'project': sys.argv[1],
        'output': str(Path(sys.argv[2]) / 'dependency_index.json'),
        **s,
    }, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
