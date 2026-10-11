#!/usr/bin/env python3
"""Detect the test runner for a project.

Shared by skills that need to run a project's test suite (code-smellz, shrinkray,
and any future heavyweight skill). Lives in skills/common/scripts/.

Usage: detect_runner.py <project_dir>
Output: JSON {runner, command, confidence}
"""

import os
import sys
import json
from fnmatch import fnmatch
from pathlib import Path

_SKIP_DIRS = {'.git', 'node_modules', '.venv', 'venv', 'env', 'vendor', 'dist', 'build', 'target'}

# (marker_filename, runner_name, command, confidence)
_FILE_MARKERS = [
    ('pytest.ini',       'pytest',  'python3 -m pytest -v', 'high'),
    ('conftest.py',      'pytest',  'python3 -m pytest -v', 'high'),
    ('Cargo.toml',       'cargo',   'cargo test',           'high'),
    ('go.mod',           'go',      'go test ./...',        'high'),
    ('pom.xml',          'maven',   'mvn test -q',          'high'),
    ('build.gradle',     'gradle',  './gradlew test',       'high'),
    ('build.gradle.kts', 'gradle',  './gradlew test',       'high'),
    ('mix.exs',          'mix',     'mix test',             'high'),
    ('Gemfile',          'rspec',   'bundle exec rspec',    'medium'),
    ('phpunit.xml',      'phpunit', 'vendor/bin/phpunit',   'high'),
    ('phpunit.xml.dist', 'phpunit', 'vendor/bin/phpunit',   'high'),
]

# (pyproject.toml content keyword, runner, command, confidence)
_PYPROJECT_HINTS = [
    ('pytest',   'pytest',   'python3 -m pytest -v',         'high'),
    ('unittest', 'unittest', 'python3 -m unittest discover', 'medium'),
]

# (package.json dependency -> command), used when no test script is defined
_NPM_HINTS = [
    ('vitest', 'npx vitest run'),
    ('jest',   'npx jest'),
    ('mocha',  'npx mocha'),
]


def _has_file(root: Path, patterns: tuple) -> bool:
    """True if a file outside dependency and build dirs matches a pattern."""
    for _, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in _SKIP_DIRS]
        if any(fnmatch(f, pat) for f in files for pat in patterns):
            return True
    return False


def detect(project_dir: str) -> dict:
    root = Path(project_dir)

    # package.json — JS/TS projects
    pkg = root / 'package.json'
    if pkg.exists():
        try:
            data = json.loads(pkg.read_text(encoding='utf-8', errors='replace'))
        except ValueError:
            data = {}
        if not isinstance(data, dict):
            data = {}
        # The project's own script wins: it carries the flags, config, and
        # build steps a bare `npx <runner>` would drop.
        script = (data.get('scripts') or {}).get('test', '')
        if script and 'no test specified' not in script:
            return {'runner': 'npm', 'command': 'npm test', 'confidence': 'high'}
        deps = {**(data.get('dependencies') or {}), **(data.get('devDependencies') or {})}
        for name, cmd in _NPM_HINTS:
            if name in deps:
                return {'runner': name, 'command': cmd, 'confidence': 'high'}

    # pyproject.toml
    pp = root / 'pyproject.toml'
    if pp.exists():
        content = pp.read_text(encoding='utf-8', errors='replace')
        for marker, name, cmd, conf in _PYPROJECT_HINTS:
            if marker in content:
                return {'runner': name, 'command': cmd, 'confidence': conf}

    # setup.cfg with [tool:pytest]
    sc = root / 'setup.cfg'
    if sc.exists() and '[tool:pytest]' in sc.read_text(encoding='utf-8', errors='replace'):
        return {'runner': 'pytest', 'command': 'python3 -m pytest -v', 'confidence': 'high'}

    # Explicit marker files
    for marker, name, cmd, conf in _FILE_MARKERS:
        if (root / marker).exists():
            return {'runner': name, 'command': cmd, 'confidence': conf}

    # Makefile with a test target. Precedence-correct: only .PHONY lines count
    # when they actually mention test; bare 'test' targets count directly.
    makefile = root / 'Makefile'
    if makefile.exists():
        content = makefile.read_text(encoding='utf-8', errors='replace')
        if any('test' in line for line in content.splitlines()
               if line.startswith(('test', '.PHONY'))):
            return {'runner': 'make', 'command': 'make test', 'confidence': 'medium'}

    # Fallback: sniff for test files
    if _has_file(root, ('test_*.py', '*_test.py')):
        return {'runner': 'pytest', 'command': 'python3 -m pytest -v', 'confidence': 'low'}

    if _has_file(root, ('*.test.js', '*.spec.js', '*.test.ts', '*.spec.ts')):
        return {'runner': 'jest', 'command': 'npx jest', 'confidence': 'low'}

    return {'runner': 'unknown', 'command': None, 'confidence': 'none'}


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.stderr.write('Usage: detect_runner.py <project_dir>\n')
        sys.exit(1)
    print(json.dumps(detect(sys.argv[1]), indent=2))
