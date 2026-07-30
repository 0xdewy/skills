#!/usr/bin/env python3
"""Count non-blank, non-comment source lines in a project.

Usage: measure_loc.py <project_dir>
Output: JSON {total, by_language, top_files}
"""

import sys
import json
from pathlib import Path

_EXTENSIONS = {
    '.py': 'Python', '.js': 'JavaScript', '.ts': 'TypeScript',
    '.jsx': 'JavaScript', '.tsx': 'TypeScript', '.mjs': 'JavaScript',
    '.go': 'Go', '.rs': 'Rust', '.java': 'Java',
    '.cpp': 'C++', '.cc': 'C++', '.cxx': 'C++', '.c': 'C',
    '.h': 'C/C++ Header', '.hpp': 'C++ Header',
    '.cs': 'C#', '.rb': 'Ruby', '.php': 'PHP',
    '.swift': 'Swift', '.kt': 'Kotlin',
    '.sh': 'Shell', '.bash': 'Shell',
    '.ex': 'Elixir', '.exs': 'Elixir',
}

_SKIP_DIRS = {
    '.git', 'node_modules', '__pycache__', '.venv', 'venv', 'env',
    'dist', 'build', 'target', '.next', 'out', 'coverage',
    '.pytest_cache', '.mypy_cache', 'vendor', '.cache',
    'stinky-output', 'shrinkray-output',
}

_LINE_COMMENT = {
    'Python': '#', 'Shell': '#', 'Ruby': '#', 'Elixir': '#',
    'JavaScript': '//', 'TypeScript': '//', 'Go': '//',
    'Rust': '//', 'Java': '//', 'C++': '//', 'C': '//',
    'C/C++ Header': '//', 'C++ Header': '//', 'C#': '//',
    'PHP': '//', 'Swift': '//', 'Kotlin': '//',
}


def _count_file(path: Path, lang: str) -> int:
    prefix = _LINE_COMMENT.get(lang, '')
    try:
        lines = path.read_text(encoding='utf-8', errors='replace').splitlines()
    except OSError:
        return 0
    return sum(
        1 for line in lines
        if (s := line.strip()) and not (prefix and s.startswith(prefix))
    )


def measure(project_dir: str) -> dict:
    root = Path(project_dir)
    by_file: dict[str, int] = {}
    by_lang: dict[str, int] = {}

    for path in root.rglob('*'):
        if any(part in _SKIP_DIRS for part in path.parts) or not path.is_file():
            continue
        lang = _EXTENSIONS.get(path.suffix.lower())
        if not lang:
            continue
        rel = str(path.relative_to(root))
        loc = _count_file(path, lang)
        if loc:
            by_file[rel] = loc
            by_lang[lang] = by_lang.get(lang, 0) + loc

    total = sum(by_file.values())
    return {
        'total': total,
        'by_language': dict(sorted(by_lang.items(), key=lambda x: -x[1])),
        'top_files': dict(sorted(by_file.items(), key=lambda x: -x[1])[:30]),
    }


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.stderr.write('Usage: measure_loc.py <project_dir>\n')
        sys.exit(1)
    print(json.dumps(measure(sys.argv[1]), indent=2))
