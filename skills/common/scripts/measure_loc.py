#!/usr/bin/env python3
"""Count non-blank, non-comment source lines in a project.

Shared by skills that measure codebase size (shrinkray and any
future heavyweight skill). Lives in skills/common/scripts/.

Usage: measure_loc.py <project_dir> [extra_skip,extra_skip,...]
Output: JSON {total, by_language, top_files}

In a git repo only tracked and untracked-but-not-ignored files count, so
ignored build output and generated code stay out of the total. The optional
second argument is a comma-separated list of extra directory names to skip.
"""

import sys
import json
import subprocess
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

# Skipped always, along with any `.<skill>-workspace` dir (the execution
# contract's project-local fallback) so a skill never counts its own scratch.
_SKIP_DIRS = {
    '.git', 'node_modules', '__pycache__', '.venv', 'venv', 'env',
    'dist', 'build', 'target', '.next', 'out', 'coverage',
    '.pytest_cache', '.mypy_cache', 'vendor', '.cache',
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


def _list_files(root: Path) -> list[Path]:
    """Files git would show as tracked or untracked; a plain walk outside git."""
    cmd = ['git', '-C', str(root), 'ls-files', '-z', '--cached', '--others', '--exclude-standard']
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
        return [root / p for p in out.split('\0') if p]
    except (OSError, subprocess.CalledProcessError):
        return list(root.rglob('*'))


def measure(project_dir: str, extra_skip: str = '') -> dict:
    root = Path(project_dir)
    skip = set(_SKIP_DIRS)
    if extra_skip:
        skip.update(s.strip() for s in extra_skip.split(',') if s.strip())
    by_file: dict[str, int] = {}
    by_lang: dict[str, int] = {}

    for path in _list_files(root):
        parts = path.relative_to(root).parts
        if any(p in skip or p.endswith('-workspace') for p in parts) or path.is_symlink() or not path.is_file():
            continue
        lang = _EXTENSIONS.get(path.suffix.lower())
        if not lang:
            continue
        rel = str(path.relative_to(root))
        loc = _count_file(path, lang)
        if loc:
            by_file[rel] = loc
            by_lang[lang] = by_lang.get(lang, 0) + loc

    return {
        'total': sum(by_file.values()),
        'by_language': dict(sorted(by_lang.items(), key=lambda x: -x[1])),
        'top_files': dict(sorted(by_file.items(), key=lambda x: -x[1])[:30]),
    }


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.stderr.write('Usage: measure_loc.py <project_dir> [extra_skip,extra_skip,...]\n')
        sys.exit(1)
    extra = sys.argv[2] if len(sys.argv) > 2 else ''
    print(json.dumps(measure(sys.argv[1], extra), indent=2))
