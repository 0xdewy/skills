#!/usr/bin/env python3
"""Detect the test runner for a project.

Usage: detect_runner.py <project_dir>
Output: JSON {runner, command, confidence}
"""

import sys
import json
from pathlib import Path

_FILE_MARKERS = [
    ('pytest.ini',       'pytest',   'python3 -m pytest -v',    'high'),
    ('conftest.py',      'pytest',   'python3 -m pytest -v',    'high'),
    ('Cargo.toml',       'cargo',    'cargo test',              'high'),
    ('go.mod',           'go',       'go test ./...',           'high'),
    ('pom.xml',          'maven',    'mvn test -q',             'high'),
    ('build.gradle',     'gradle',   './gradlew test',          'high'),
    ('build.gradle.kts', 'gradle',   './gradlew test',          'high'),
    ('mix.exs',          'mix',      'mix test',                'high'),
    ('Gemfile',          'rspec',    'bundle exec rspec',       'medium'),
    ('phpunit.xml',      'phpunit',  'vendor/bin/phpunit',      'high'),
    ('phpunit.xml.dist', 'phpunit',  'vendor/bin/phpunit',      'high'),
]

_PYPROJECT_HINTS = [
    ('pytest',   'pytest',   'python3 -m pytest -v',           'high'),
    ('unittest', 'unittest', 'python3 -m unittest discover',   'medium'),
]

_NPM_HINTS = [
    ('vitest', 'vitest', 'npx vitest run'),
    ('jest',   'jest',   'npx jest'),
    ('mocha',  'mocha',  'npx mocha'),
    ('"test"', 'npm',    'npm test'),
]


def detect(project_dir: str) -> dict:
    root = Path(project_dir)

    pkg = root / 'package.json'
    if pkg.exists():
        content = pkg.read_text(encoding='utf-8', errors='replace')
        for marker, name, cmd in _NPM_HINTS:
            if marker in content:
                return {'runner': name, 'command': cmd, 'confidence': 'high'}

    pp = root / 'pyproject.toml'
    if pp.exists():
        content = pp.read_text(encoding='utf-8', errors='replace')
        for marker, name, cmd, conf in _PYPROJECT_HINTS:
            if marker in content:
                return {'runner': name, 'command': cmd, 'confidence': conf}

    sc = root / 'setup.cfg'
    if sc.exists() and '[tool:pytest]' in sc.read_text(encoding='utf-8', errors='replace'):
        return {'runner': 'pytest', 'command': 'python3 -m pytest -v', 'confidence': 'high'}

    for marker, name, cmd, conf in _FILE_MARKERS:
        if (root / marker).exists():
            return {'runner': name, 'command': cmd, 'confidence': conf}

    makefile = root / 'Makefile'
    if makefile.exists():
        content = makefile.read_text(encoding='utf-8', errors='replace')
        if any('test' in line for line in content.splitlines() if line.startswith(('test', '.PHONY'))):
            return {'runner': 'make', 'command': 'make test', 'confidence': 'medium'}

    if list(root.rglob('test_*.py'))[:1] or list(root.rglob('*_test.py'))[:1]:
        return {'runner': 'pytest', 'command': 'python3 -m pytest -v', 'confidence': 'low'}

    js_tests = (list(root.rglob('*.test.js'))[:1] + list(root.rglob('*.spec.js'))[:1] +
                list(root.rglob('*.test.ts'))[:1] + list(root.rglob('*.spec.ts'))[:1])
    if js_tests:
        return {'runner': 'jest', 'command': 'npx jest', 'confidence': 'low'}

    return {'runner': 'unknown', 'command': None, 'confidence': 'none'}


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.stderr.write('Usage: detect_runner.py <project_dir>\n')
        sys.exit(1)
    print(json.dumps(detect(sys.argv[1]), indent=2))
