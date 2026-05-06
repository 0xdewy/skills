#!/usr/bin/env python3
"""
Codebase Explorer

Analyzes a codebase and suggests exploration paths.
Provides structured output for interactive exploration.

Usage:
    python explorer.py <codebase-path> [options]

Options:
    --json              Output JSON format
    --language LANG     Force language detection
    --entry-points      Show only entry points
    --structure         Show directory structure
    --summary           Show brief summary
    --suggest            Suggest exploration paths
"""

import os
import re
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Set, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict

@dataclass
class FileInfo:
    path: str
    size: int
    lines: int
    extension: str
    is_entry_point: bool
    imports: List[str]
    exports: List[str]

@dataclass
class DirectoryInfo:
    path: str
    file_count: int
    total_lines: int
    subdirs: List[str]
    languages: Dict[str, int]

@dataclass
class CodebaseSummary:
    root: str
    language: str
    total_files: int
    total_lines: int
    entry_points: List[str]
    main_modules: List[str]
    test_files: List[str]
    config_files: List[str]
    directory_tree: str
    language_breakdown: Dict[str, int]
    suggested_explorations: List[Dict[str, str]]

class CodebaseExplorer:
    LANGUAGES = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.ts': 'TypeScript',
        '.jsx': 'JavaScript (React)',
        '.tsx': 'TypeScript (React)',
        '.go': 'Go',
        '.java': 'Java',
        '.rb': 'Ruby',
        '.rs': 'Rust',
        '.c': 'C',
        '.cpp': 'C++',
        '.h': 'C/C++ Header',
        '.hpp': 'C++ Header',
        '.cs': 'C#',
        '.php': 'PHP',
        '.swift': 'Swift',
        '.kt': 'Kotlin',
        '.scala': 'Scala',
        '.clj': 'Clojure',
        '.ex': 'Elixir',
        '.exs': 'Elixir',
        '.erl': 'Erlang',
        '.hs': 'Haskell',
        '.ml': 'OCaml',
        '.vue': 'Vue',
        '.svelte': 'Svelte',
    }

    ENTRY_PATTERNS = {
        'python': ['__main__.py', 'main.py', 'app.py', 'run.py', 'server.py', 'cli.py', 'wsgi.py', 'asgi.py'],
        'javascript': ['index.js', 'main.js', 'app.js', 'server.js', 'cli.js', 'bin/'],
        'typescript': ['index.ts', 'main.ts', 'app.ts', 'server.ts', 'bin/'],
        'go': ['main.go'],
        'java': ['Main.java', '*Application.java', '*Runner.java'],
        'ruby': ['main.rb', 'app.rb', 'Rakefile'],
        'rust': ['main.rs', 'lib.rs'],
        'c': ['main.c'],
        'cpp': ['main.cpp', '*.cpp'],
    }

    def __init__(self, root_path: str, language: Optional[str] = None):
        self.root = Path(root_path)
        self.language = language
        self.files: List[FileInfo] = []
        self.directories: Dict[str, DirectoryInfo] = {}
        self.entry_points: Set[str] = set()
        self.modules: Set[str] = set()
        self.test_files: Set[str] = set()
        self.config_files: Set[str] = set()
        self._analyze()

    def _analyze(self):
        if not self.language:
            self.language = self._detect_language()

        for root, dirs, files in os.walk(self.root):
            dirs[:] = [d for d in dirs if d not in self._ignore_dirs()]

            rel_root = str(Path(root).relative_to(self.root))
            if rel_root == '.':
                rel_root = ''

            subdirs = [d for d in dirs if not d.startswith('.')]

            dir_info = DirectoryInfo(
                path=rel_root or '.',
                file_count=len(files),
                total_lines=0,
                subdirs=sorted(subdirs),
                languages=defaultdict(int)
            )

            for f in files:
                if f.startswith('.'):
                    continue

                path = Path(root) / f
                ext = path.suffix

                try:
                    size = path.stat().st_size
                    with open(path, 'r', encoding='utf-8', errors='ignore') as file:
                        content = file.read()
                        lines = len(content.splitlines())
                except:
                    size = 0
                    lines = 0

                file_info = FileInfo(
                    path=str(path.relative_to(self.root)),
                    size=size,
                    lines=lines,
                    extension=ext,
                    is_entry_point=False,
                    imports=[],
                    exports=[]
                )

                if self._is_entry_point(f, ext):
                    self.entry_points.add(str(path.relative_to(self.root)))
                    file_info.is_entry_point = True

                if self._is_test_file(f, path):
                    self.test_files.add(str(path.relative_to(self.root)))

                if self._is_config_file(f):
                    self.config_files.add(str(path.relative_to(self.root)))

                if ext in self.LANGUAGES and self._get_language(ext) == self.language:
                    dir_info.total_lines += lines
                    dir_info.languages[self.language] += lines

                    if self.language == 'Python':
                        if ext == '.py' and not f.startswith('_'):
                            self.modules.add(f[:-3])
                        imports, exports = self._extract_python_imports_exports(content)
                        file_info.imports = imports
                        file_info.exports = exports

                self.files.append(file_info)

            if rel_root == '':
                rel_root = '.'
            self.directories[rel_root] = dir_info

    def _ignore_dirs(self) -> List[str]:
        return [
            '__pycache__', '.git', '.svn', '.hg',
            'node_modules', 'venv', '.venv', 'env',
            '.env', 'virtualenvs', 'build', 'dist',
            '.tox', '.pytest_cache', '.mypy_cache',
            'vendor', 'deps', '.deps',
            'target', 'bin', 'obj',
            '.idea', '.vscode', '.vs',
            'coverage', '.nyc_output',
            '.next', '.nuxt', '.gatsby',
            'tmp', 'temp', 'test_output'
        ]

    def _detect_language(self) -> str:
        ext_counts = defaultdict(int)
        for root, dirs, files in os.walk(self.root):
            dirs[:] = [d for d in dirs if d not in self._ignore_dirs()]
            for f in files:
                ext = Path(f).suffix
                if ext in self.LANGUAGES:
                    ext_counts[ext] += 1

        if not ext_counts:
            return 'unknown'

        dominant_ext = max(ext_counts, key=ext_counts.get)
        return self.LANGUAGES.get(dominant_ext, 'unknown')

    def _get_language(self, ext: str) -> Optional[str]:
        return self.LANGUAGES.get(ext)

    def _is_entry_point(self, filename: str, ext: str) -> bool:
        if ext not in self.LANGUAGES:
            return False

        lang = self._get_language(ext)
        if not lang:
            return False

        lang_key = lang.lower()

        for pattern in self.ENTRY_PATTERNS.get(lang_key, []):
            if pattern.startswith('*'):
                if filename.endswith(pattern[1:]):
                    return True
            elif pattern in filename or pattern.rstrip('/') == filename:
                return True

        return False

    def _is_test_file(self, filename: str, path: Path) -> bool:
        test_indicators = ['test_', '_test.', 'tests/', '.test.', '.spec.', '/test/', '/tests/']
        name_lower = filename.lower()
        path_str = str(path).lower()

        for indicator in test_indicators:
            if indicator.lower() in name_lower or indicator.lower() in path_str:
                return True

        parent_dirs = set(path.parts)
        if 'test' in parent_dirs or 'tests' in parent_dirs or 'spec' in parent_dirs:
            return True

        return False

    def _is_config_file(self, filename: str) -> bool:
        config_patterns = [
            'package.json', 'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml',
            'requirements.txt', 'Pipfile', 'Pipfile.lock', 'pyproject.toml', 'setup.py', 'setup.cfg',
            'go.mod', 'go.sum',
            'Cargo.toml', 'Cargo.lock',
            'Gemfile', 'Gemfile.lock',
            'pom.xml', 'build.gradle', 'build.gradle.kts',
            'Makefile', 'CMakeLists.txt', 'Dockerfile', 'docker-compose.yml',
            '.env', '.env.example', '.env.local',
            'tsconfig.json', 'jsconfig.json', 'webpack.config.js', 'vite.config.js',
            'jest.config.js', 'vitest.config.js', 'pytest.ini', 'tox.ini',
            '.eslintrc', '.eslintrc', 'prettier.config.js', '.prettierrc',
            'settings.py', 'config.py', 'conf.py', 'configuration.py',
            'routes.rb', 'routes.js', 'routes.ts',
        ]
        return filename in config_patterns

    def _extract_python_imports_exports(self, content: str) -> tuple:
        imports = []
        exports = []

        for line in content.split('\n'):
            line = line.strip()

            import_match = re.match(r'(?:from\s+([\w.]+)\s+)?import\s+(.+)', line)
            if import_match:
                module = import_match.group(1) or ''
                names = import_match.group(2)
                for name in names.split(','):
                    name = name.strip().split(' as ')[0].strip()
                    if name and not name.startswith('_'):
                        imports.append(name)

            export_match = re.match(r'(?:def|class|async\s+def)\s+(\w+)', line)
            if export_match:
                exports.append(export_match.group(1))

        return imports, exports

    def get_summary(self) -> CodebaseSummary:
        total_files = len(self.files)
        total_lines = sum(f.lines for f in self.files)

        main_modules = sorted(self.modules - self.test_files - self.config_files)

        directory_tree = self._build_tree()

        lang_breakdown = defaultdict(int)
        for f in self.files:
            if f.extension in self.LANGUAGES:
                lang_breakdown[self.LANGUAGES[f.extension]] += f.lines

        suggestions = self._suggest_explorations()

        return CodebaseSummary(
            root=str(self.root),
            language=self.language,
            total_files=total_files,
            total_lines=total_lines,
            entry_points=sorted(self.entry_points),
            main_modules=main_modules[:20],
            test_files=sorted(self.test_files),
            config_files=sorted(self.config_files),
            directory_tree=directory_tree,
            language_breakdown=dict(lang_breakdown),
            suggested_explorations=suggestions
        )

    def _build_tree(self, max_depth: int = 3) -> str:
        lines = []

        root_path = self.root
        for item in sorted(self.root.iterdir()):
            if item.name.startswith('.'):
                continue
            if item.is_dir():
                lines.append(f"{item.name}/")
            else:
                lines.append(f"{item.name}")

        return '\n'.join(lines)

    def _suggest_explorations(self) -> List[Dict[str, str]]:
        suggestions = []

        if self.entry_points:
            suggestions.append({
                'type': 'entry_point',
                'title': 'Start at the entry point',
                'description': f'Every app has a starting point. {list(self.entry_points)[0]} is where everything begins.',
                'path': list(self.entry_points)[0]
            })

        if len(self.modules) > 3:
            suggestions.append({
                'type': 'modules',
                'title': 'Explore the main modules',
                'description': f'Found {len(self.modules)} modules. Let me show you how they connect.',
                'count': len(self.modules)
            })

        if self.test_files:
            suggestions.append({
                'type': 'tests',
                'title': 'Look at the tests',
                'description': 'Tests reveal how the code is meant to be used.',
                'count': len(self.test_files)
            })

        if self.config_files:
            suggestions.append({
                'type': 'configuration',
                'title': 'Check the configuration',
                'description': 'Configuration tells us about the environment and dependencies.',
                'count': len(self.config_files)
            })

        suggestions.append({
            'type': 'call_graph',
            'title': 'Generate a call graph',
            'description': 'See which functions call which — the control flow of the system.',
            'hint': 'run: python scripts/code-graph.py'
        })

        suggestions.append({
            'type': 'dependencies',
            'title': 'Map the dependencies',
            'description': 'Understand what modules depend on what external packages.',
            'hint': 'This reveals the architecture and external dependencies'
        })

        return suggestions

    def to_json(self) -> str:
        summary = self.get_summary()
        return json.dumps(asdict(summary), indent=2)

    def to_markdown(self) -> str:
        summary = self.get_summary()
        lines = [
            f"# Codebase: {summary.root}",
            "",
            f"**Language:** {summary.language}",
            f"**Files:** {summary.total_files}",
            f"**Lines of Code:** {summary.total_lines:,}",
            "",
            "## Entry Points",
        ]

        if summary.entry_points:
            for ep in summary.entry_points:
                lines.append(f"- `{ep}`")
        else:
            lines.append("_None detected_")

        lines.extend([
            "",
            "## Main Modules",
        ])

        if summary.main_modules:
            for mod in summary.main_modules[:10]:
                lines.append(f"- `{mod}`")
            if len(summary.main_modules) > 10:
                lines.append(f"- _... and {len(summary.main_modules) - 10} more_")
        else:
            lines.append("_None detected_")

        lines.extend([
            "",
            "## Configuration Files",
        ])

        if summary.config_files:
            for cf in summary.config_files:
                lines.append(f"- `{cf}`")
        else:
            lines.append("_None detected_")

        lines.extend([
            "",
            "## Directory Structure",
            "```",
            summary.directory_tree,
            "```",
            "",
            "## Language Breakdown",
        ])

        for lang, lines_count in sorted(summary.language_breakdown.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"- {lang}: {lines_count:,} lines")

        lines.extend([
            "",
            "## Suggested Explorations",
        ])

        for suggestion in summary.suggested_explorations:
            lines.append(f"\n### {suggestion['title']}")
            lines.append(f"{suggestion['description']}")

        return '\n'.join(lines)

def main():
    parser = argparse.ArgumentParser(description='Explore and summarize a codebase')
    parser.add_argument('codebase', help='Path to codebase to explore')
    parser.add_argument('--json', action='store_true', help='Output JSON format')
    parser.add_argument('--language', help='Force language detection')
    parser.add_argument('--summary', action='store_true', help='Show brief summary only')
    parser.add_argument('--structure', action='store_true', help='Show directory structure')
    parser.add_argument('--suggest', action='store_true', help='Suggest exploration paths')

    args = parser.parse_args()

    if not os.path.isdir(args.codebase):
        print(f"Error: {args.codebase} is not a directory", file=sys.stderr)
        sys.exit(1)

    explorer = CodebaseExplorer(args.codebase, args.language)

    if args.json:
        print(explorer.to_json())
    else:
        print(explorer.to_markdown())

if __name__ == '__main__':
    main()