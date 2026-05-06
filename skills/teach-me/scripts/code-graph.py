#!/usr/bin/env python3
"""
Code Graph Generator

Generates call graphs and dependency graphs for codebases.
Supports multiple languages: Python, JavaScript, TypeScript, Go, Java, Ruby.

Usage:
    python code-graph.py <codebase-path> [options]

Options:
    --type call|dep        Type of graph (default: call)
    --format mermaid|dot  Output format (default: mermaid)
    --depth N              Max depth for call graph (default: 3)
    --output FILE          Write to file instead of stdout
    --language LANG        Force language (auto-detected if not specified)
"""

import os
import re
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import ast

@dataclass
class FunctionCall:
    caller: str
    callee: str
    file: str
    line: int

@dataclass
class Import:
    module: str
    name: str
    alias: Optional[str]
    file: str

class CodeAnalyzer:
    LANGUAGES = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.jsx': 'javascript',
        '.tsx': 'typescript',
        '.go': 'go',
        '.java': 'java',
        '.rb': 'ruby',
        '.c': 'c',
        '.cpp': 'cpp',
        '.cc': 'cpp',
        '.h': 'c',
        '.hpp': 'cpp',
    }

    def __init__(self, root_path: str, language: Optional[str] = None):
        self.root_path = Path(root_path)
        self.language = language or self._detect_language()
        self.functions: Dict[str, List[str]] = defaultdict(list)  # file -> function names
        self.calls: List[FunctionCall] = []
        self.imports: List[Import] = []
        self.modules: Dict[str, Set[str]] = defaultdict(set)  # module -> dependencies

    def _detect_language(self) -> str:
        ext_counts = defaultdict(int)
        for root, dirs, files in os.walk(self.root_path):
            if '__pycache__' in root or 'node_modules' in root or '.git' in root:
                continue
            for f in files:
                ext = Path(f).suffix
                if ext in self.LANGUAGES:
                    ext_counts[ext] += 1
        if not ext_counts:
            return 'python'
        dominant_ext = max(ext_counts, key=ext_counts.get)
        return self.LANGUAGES.get(dominant_ext, 'python')

    def analyze(self):
        for root, dirs, files in os.walk(self.root_path):
            dirs[:] = [d for d in dirs if d not in ('__pycache__', 'node_modules', '.git', 'venv', '.venv', 'env')]
            for f in files:
                path = Path(root) / f
                ext = path.suffix
                if ext not in self.LANGUAGES:
                    continue
                lang = self.LANGUAGES[ext]
                if lang == self.language:
                    getattr(self, f'_analyze_{lang}')(path)

    def _analyze_python(self, path: Path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            return

        try:
            tree = ast.parse(content, filename=str(path))
        except:
            return

        module_name = self._get_module_name(path)
        current_file_calls = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                self.functions[str(path)].append(node.name)
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        callee = self._get_call_name(child)
                        if callee:
                            self.calls.append(FunctionCall(
                                caller=node.name,
                                callee=callee,
                                file=str(path),
                                line=child.lineno
                            ))

            elif isinstance(node, ast.Import):
                for alias in node.names:
                    self.imports.append(Import(
                        module=alias.name,
                        name=alias.asname or alias.name,
                        alias=None,
                        file=str(path)
                    ))

            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    self.imports.append(Import(
                        module=node.module or '',
                        name=alias.name,
                        alias=alias.asname,
                        file=str(path)
                    ))

        for imp in self.imports:
            if imp.module:
                self.modules[module_name].add(imp.module)

    def _get_call_name(self, node: ast.Call) -> Optional[str]:
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr
        return None

    def _get_module_name(self, path: Path) -> str:
        try:
            rel = path.relative_to(self.root_path)
            parts = list(rel.parts[:-1]) + [path.stem]
            return '.'.join(parts)
        except:
            return str(path)

    def _analyze_javascript(self, path: Path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            return

        func_pattern = r'(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=.*?(?:function|\(.*?\)\s*=>)|(\w+)\s*:\s*function\s*\(.*?\)\s*\{|(\w+)\s*\(.*?\)\s*\{)'
        import_pattern = r'(?:import\s+.*?from\s+[\'"](.+?)[\'"]|require\([\'"](.+?)[\'"]\))'

        for match in re.finditer(func_pattern, content):
            func_name = match.group(1) or match.group(2) or match.group(3) or match.group(4)
            if func_name:
                self.functions[str(path)].append(func_name)

        for match in re.finditer(import_pattern, content):
            module = match.group(1) or match.group(2)
            if module:
                self.imports.append(Import(
                    module=module,
                    name=module.split('/')[-1],
                    alias=None,
                    file=str(path)
                ))
                self.modules[self._get_module_name(path)].add(module)

    def _analyze_typescript(self, path: Path):
        self._analyze_javascript(path)

    def _analyze_go(self, path: Path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            return

        func_pattern = r'func\s+(?:\([^)]+\)\s+)?(\w+)\s*\('
        import_pattern = r'import\s+(?:"(.+?)"|\(\s*"(.+?)")'

        for match in re.finditer(func_pattern, content):
            self.functions[str(path)].append(match.group(1))

        for match in re.finditer(import_pattern, content):
            module = match.group(1) or match.group(2)
            if module:
                self.imports.append(Import(
                    module=module,
                    name=module.split('/')[-1],
                    alias=None,
                    file=str(path)
                ))

    def _analyze_java(self, path: Path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            return

        class_pattern = r'class\s+(\w+)'
        func_pattern = r'(?:public|private|protected)\s+(?:static\s+)?(?:\w+\s+)*(\w+)\s*\('
        import_pattern = r'import\s+([\w.]+);'

        for match in re.finditer(class_pattern, content):
            self.functions[str(path)].append(match.group(1))

        for match in re.finditer(func_pattern, content):
            self.functions[str(path)].append(match.group(1))

        for match in re.finditer(import_pattern, content):
            module = match.group(1)
            self.imports.append(Import(
                module=module,
                name=module.split('.')[-1],
                alias=None,
                file=str(path)
            ))

    def _analyze_ruby(self, path: Path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            return

        func_pattern = r'def\s+(\w+)'
        require_pattern = r'require\s+[\'"](.+?)[\'"]'

        for match in re.finditer(func_pattern, content):
            self.functions[str(path)].append(match.group(1))

        for match in re.finditer(require_pattern, content):
            self.imports.append(Import(
                module=match.group(1),
                name=match.group(1).split('/')[-1],
                alias=None,
                file=str(path)
            ))

    def generate_call_graph(self, depth: int = 3) -> List[FunctionCall]:
        return self.calls

    def generate_dependency_graph(self) -> Dict[str, Set[str]]:
        return self.modules

class GraphGenerator:
    @staticmethod
    def to_mermaid_callgraph(calls: List[FunctionCall], depth: int = 3) -> str:
        lines = ["```mermaid", "graph TD"]

        unique_calls = {}
        for call in calls:
            key = (call.caller, call.callee)
            if key not in unique_calls:
                unique_calls[key] = call
                safe_caller = re.sub(r'[^a-zA-Z0-9_]', '_', call.caller)
                safe_callee = re.sub(r'[^a-zA-Z0-9_]', '_', call.callee)
                lines.append(f"    {safe_caller}({call.caller}) --> {safe_callee}({call.callee})")

        lines.append("```")
        return '\n'.join(lines)

    @staticmethod
    def to_mermaid_dependency(deps: Dict[str, Set[str]]) -> str:
        lines = ["```mermaid", "graph LR"]

        seen = set()
        for module, dependencies in deps.items():
            safe_module = re.sub(r'[^a-zA-Z0-9_]', '_', module)
            for dep in dependencies:
                key = (module, dep)
                if key not in seen:
                    seen.add(key)
                    safe_dep = re.sub(r'[^a-zA-Z0-9_]', '_', dep)
                    lines.append(f"    {safe_module}[{module}] --> {safe_dep}[{dep}]")

        lines.append("```")
        return '\n'.join(lines)

    @staticmethod
    def to_dot_callgraph(calls: List[FunctionCall]) -> str:
        lines = ["digraph callgraph {", "  rankdir=LR;", "  node [shape=box];"]

        seen = set()
        for call in calls:
            key = (call.caller, call.callee)
            if key not in seen:
                seen.add(key)
                safe_caller = re.sub(r'[^a-zA-Z0-9_]', '_', call.caller).replace('"', '\\"')
                safe_callee = re.sub(r'[^a-zA-Z0-9_]', '_', call.callee).replace('"', '\\"')
                lines.append(f'  "{safe_caller}" -> "{safe_callee}";')

        lines.append("}")
        return '\n'.join(lines)

    @staticmethod
    def to_dot_dependency(deps: Dict[str, Set[str]]) -> str:
        lines = ["digraph dependency {", "  rankdir=LR;", "  node [shape=box];"]

        seen = set()
        for module, dependencies in deps.items():
            safe_module = re.sub(r'[^a-zA-Z0-9_]', '_', module).replace('"', '\\"')
            for dep in dependencies:
                key = (module, dep)
                if key not in seen:
                    seen.add(key)
                    safe_dep = re.sub(r'[^a-zA-Z0-9_]', '_', dep).replace('"', '\\"')
                    lines.append(f'  "{safe_module}" -> "{safe_dep}";')

        lines.append("}")
        return '\n'.join(lines)

def main():
    parser = argparse.ArgumentParser(description='Generate call and dependency graphs from code')
    parser.add_argument('codebase', help='Path to codebase to analyze')
    parser.add_argument('--type', choices=['call', 'dep'], default='call', help='Type of graph')
    parser.add_argument('--format', choices=['mermaid', 'dot'], default='mermaid', help='Output format')
    parser.add_argument('--depth', type=int, default=3, help='Max depth for call graph')
    parser.add_argument('--output', help='Output file (default: stdout)')
    parser.add_argument('--language', help='Force language (auto-detected if not specified)')
    parser.add_argument('--json', action='store_true', help='Output raw JSON data')

    args = parser.parse_args()

    if not os.path.isdir(args.codebase):
        print(f"Error: {args.codebase} is not a directory", file=sys.stderr)
        sys.exit(1)

    analyzer = CodeAnalyzer(args.codebase, args.language)
    analyzer.analyze()

    if args.json:
        output = json.dumps({
            'language': analyzer.language,
            'functions': {k: v for k, v in analyzer.functions.items()},
            'calls': [(c.caller, c.callee, c.file, c.line) for c in analyzer.calls],
            'dependencies': {k: list(v) for k, v in analyzer.modules.items()}
        }, indent=2)
    elif args.type == 'call':
        graph_data = analyzer.generate_call_graph(args.depth)
        if args.format == 'mermaid':
            output = GraphGenerator.to_mermaid_callgraph(graph_data, args.depth)
        else:
            output = GraphGenerator.to_dot_callgraph(graph_data)
    else:
        deps = analyzer.generate_dependency_graph()
        if args.format == 'mermaid':
            output = GraphGenerator.to_mermaid_dependency(deps)
        else:
            output = GraphGenerator.to_dot_dependency(deps)

    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
        print(f"Written to {args.output}")
    else:
        print(output)

if __name__ == '__main__':
    main()