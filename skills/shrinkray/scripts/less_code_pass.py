#!/usr/bin/env python3
"""Deterministic, test-gated pre-pass for shrinkray, via `less-code` (`lc`).

Runs BEFORE any agent is dispatched (Phase 0.4) and applies real changes
directly, not findings for an agent to review: every rewrite is gated by
`lc`'s own frozen test suite / public-API / doc-preservation checks, and a
failing layer reverts itself internally, so there is nothing here for the
orchestrator's patch/revert machinery to do. This is the same "spend tokens
verifying and implementing rather than discovering" argument the other two
pre-pass scripts make, taken one step further: for Python, JavaScript,
TypeScript, and Rust, `lc` does not just find candidates for an agent to fix,
it fixes and verifies them itself, for zero agent budget.

What it covers deterministically: dead internal code, accumulator/append-loop
-> comprehension folds, redundant temporaries, guard-clause and conditional
collapses, import packing, and (Python) cross-function duplicate-window
outlining. It does NOT replace Dead Code Hunter, Verbosity Reducer, Code
Consolidator, or the structural roles — those catch what a peephole rule
cannot: candidates needing project-wide semantic judgment, prose/naming
verbosity, and cross-file consolidation. Run deadcode_scan.py and
dependency_index.py on the tree AFTER this pass so they do not re-propose
what `lc` already applied.

Language support and the tool itself are both optional: unsupported
languages, and a project where `lc` cannot be found, are reported and
skipped rather than treated as a blocker (see execution-contract.md ->
"Tool and Subagent Fallbacks").

Usage: less_code_pass.py <project_dir> <output_dir> [--test-command CMD]
                          [--timeout SECONDS]

Finding `lc`:
  1. `shutil.which("lc")` - a global install (`uv tool install --editable
     /path/to/less-code`, or any install that puts `lc` on PATH).
  2. `$LESS_CODE_HOME` - a checkout directory, run via
     `uv run --project "$LESS_CODE_HOME" lc`.
  If neither resolves, the pass is skipped and the output JSON says so with
  the same one-line setup hint printed here.

--test-command overrides the project's OWN detected test command (typically
the same value `detect_runner.py` found in Phase 0) instead of `lc`'s
built-in per-language default, so this pass and the loop's Phase 4 verify
run the identical suite. Needed for a project with its own venv or a
monorepo package whose tests must be scoped (e.g.
`.venv/bin/python -m pytest -x -q`, or `npm --prefix js test --silent`).

Output: <output_dir>/less_code_pass.json
  {
    "ran": true|false,
    "reason": "<why skipped, when ran is false>",
    "languages": ["python", ...],
    "per_language": [
      {"lang": "python", "loc_start": N, "loc_final": N, "pct": 0.0,
       "tests_ok": true, "api_ok": true, "docs_ok": true,
       "layers": [{"layer": "rules", "loc_before": N, "loc_after": N,
                   "committed": true}, ...],
       "report": "<path to lc's own JSON report>"}
    ],
    "total_loc_removed": N
  }

Exit codes: 0 always (ran, partially ran, or skipped). Non-zero only on
usage error. A gate failure inside `lc` is not a script failure - `lc`
already reverted that layer; `tests_ok`/`api_ok`/`docs_ok` say what held.
"""
from __future__ import annotations

import argparse
import json
import os
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

_SETUP_HINT = (
    "less-code (`lc`) not found. Install globally with "
    "`uv tool install --editable /path/to/less-code` (exposes `lc` on PATH), "
    "or set LESS_CODE_HOME to the checkout directory."
)


_EXT_LANG = {
    '.py': 'python',
    '.rs': 'rust',
    '.js': 'javascript', '.mjs': 'javascript', '.cjs': 'javascript',
    '.ts': 'typescript', '.mts': 'typescript',
}


def _detect_languages(root: Path) -> list[str]:
    """`lc`-compatible language names actually present.

    A manifest (`pyproject.toml`, `Cargo.toml`, ...) is a fast, cheap signal
    but not a reliable one on its own: plenty of real Python projects have
    neither `pyproject.toml`, `setup.py`, nor `setup.cfg`, and a nested
    Rust/JS package in a monorepo may sit below a root with no manifest at
    all. Manifest presence and a full-tree extension scan are combined
    (OR), the same union `lc`'s own language detection ultimately falls
    back to, so a real project is never silently skipped for want of one
    particular file `lc` does not actually require.
    """
    found: set[str] = set()
    if any((root / m).exists() for m in ('pyproject.toml', 'setup.py', 'setup.cfg')):
        found.add('python')
    if (root / 'Cargo.toml').exists():
        found.add('rust')
    for path in root.rglob('*'):
        if not path.is_file() or any(part in _SKIP_DIRS for part in path.parts):
            continue
        lang = _EXT_LANG.get(path.suffix.lower())
        if lang:
            found.add(lang)
        if len(found) == len(set(_EXT_LANG.values())):
            break
    # Stable, deterministic order regardless of filesystem walk order.
    return [lang for lang in ('python', 'rust', 'javascript', 'typescript') if lang in found]


def _resolve_lc() -> list[str] | None:
    """The `lc` invocation prefix, or None when the tool cannot be found."""
    on_path = shutil.which('lc')
    if on_path:
        return [on_path]
    home = os.environ.get('LESS_CODE_HOME')
    if home and Path(home).is_dir():
        return ['uv', 'run', '--project', home, 'lc']
    return None


def _default_python_test_command(project_dir: Path) -> str | None:
    """A project-local venv's own interpreter, when the caller gave none.

    `lc`'s built-in Python default is `sys.executable -m pytest`, where
    `sys.executable` is *lc's own* interpreter. That is correct when `lc`
    runs via `uv run` inside the project it is reducing (the documented
    workflow), but when `lc` is installed once, globally, as a `uv tool`
    (the way this pass expects it), that interpreter is an isolated venv
    with only `lc`'s own dependencies - not the target project's pytest,
    or anything else the project's tests import. A project-local `.venv`
    or `venv` almost always already has its own test dependencies
    installed, so it is a safe, common-convention default; anything else
    (a conda env, a non-standard layout, a project needing dependencies
    installed before its tests can even collect) genuinely needs an
    explicit --test-command - there is no ambient interpreter this script
    could guess that would be right more often than it is wrong.
    """
    for candidate in ('.venv', 'venv'):
        python = project_dir / candidate / 'bin' / 'python'
        if python.is_file():
            return f'{python} -m pytest -x -q --no-header'
    return None


def _run_one(
    lc_cmd: list[str],
    lang: str,
    project_dir: Path,
    out_dir: Path,
    test_command: str | None,
    timeout: int,
) -> dict:
    report_path = out_dir / f'lc_report_{lang}.json'
    cmd = [
        *lc_cmd, 'shrink', str(project_dir),
        '--lang', lang,
        '--out', str(report_path),
        '--timeout', str(timeout),
    ]
    if test_command:
        cmd += ['--test-command', test_command]
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout + 60, check=False,
        )
        exit_code = proc.returncode
        stderr, stdout = proc.stderr, proc.stdout
    except subprocess.TimeoutExpired as exc:
        # `lc` itself already enforces --timeout on the test command; a
        # subprocess-level timeout here means `lc` hung outright. Report it
        # like any other failed run rather than letting it crash the whole
        # pass and its "exit codes: 0 always" contract with it.
        exit_code = -1
        stderr = f'lc timed out after {timeout + 60}s (outer wrapper timeout)'
        stdout = exc.stdout or ''  # text=True above means this is already str
    except OSError as exc:
        exit_code = -1
        stderr, stdout = str(exc), ''
    result = {
        'lang': lang,
        'exit_code': exit_code,
        'report': str(report_path),
    }
    if report_path.is_file():
        try:
            payload = json.loads(report_path.read_text(encoding='utf-8'))['reduce']
        except (json.JSONDecodeError, KeyError, OSError):
            payload = None
        if payload is not None:
            result.update({
                'loc_start': payload.get('loc_start', 0),
                'loc_final': payload.get('loc_final', 0),
                'pct': payload.get('hybrid_pct', 0.0),
                'tests_ok': payload.get('tests_ok'),
                'api_ok': payload.get('api_ok'),
                'docs_ok': payload.get('docs_ok'),
                'layers': [
                    {
                        'layer': lr.get('layer'),
                        'loc_before': lr.get('loc_before'),
                        'loc_after': lr.get('loc_after'),
                        'committed': lr.get('committed'),
                    }
                    for lr in payload.get('layer_records', [])
                ],
            })
            return result
    result['error'] = (stderr or stdout or 'no report written')[-2000:]
    return result


def run(
    project_dir: str,
    output_dir: str,
    test_command: str | None,
    timeout: int,
) -> dict:
    root = Path(project_dir)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    lc_cmd = _resolve_lc()
    if lc_cmd is None:
        payload = {'ran': False, 'reason': _SETUP_HINT, 'languages': [],
                   'per_language': [], 'total_loc_removed': 0}
        (out / 'less_code_pass.json').write_text(
            json.dumps(payload, indent=2), encoding='utf-8')
        return payload

    languages = _detect_languages(root)
    if not languages:
        payload = {
            'ran': False,
            'reason': 'no python/javascript/typescript/rust files found',
            'languages': [], 'per_language': [], 'total_loc_removed': 0,
        }
        (out / 'less_code_pass.json').write_text(
            json.dumps(payload, indent=2), encoding='utf-8')
        return payload

    def _effective_test_command(lang: str) -> str | None:
        if test_command:
            return test_command
        if lang == 'python':
            return _default_python_test_command(root)
        return None

    per_language = [
        _run_one(lc_cmd, lang, root, out, _effective_test_command(lang), timeout)
        for lang in languages
    ]
    total_removed = sum(
        max(0, r.get('loc_start', 0) - r.get('loc_final', 0))
        for r in per_language
    )
    payload = {
        'ran': True,
        'languages': languages,
        'per_language': per_language,
        'total_loc_removed': total_removed,
    }
    (out / 'less_code_pass.json').write_text(
        json.dumps(payload, indent=2), encoding='utf-8')
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('project_dir')
    parser.add_argument('output_dir')
    parser.add_argument('--test-command', default=None)
    parser.add_argument('--timeout', type=int, default=600)
    try:
        args = parser.parse_args()
    except SystemExit:
        sys.stderr.write(__doc__)
        return 2

    payload = run(args.project_dir, args.output_dir, args.test_command, args.timeout)
    print(json.dumps({
        'ran': payload['ran'],
        'reason': payload.get('reason'),
        'languages': payload['languages'],
        'total_loc_removed': payload['total_loc_removed'],
        'per_language_summary': [
            {
                'lang': r['lang'],
                'loc_start': r.get('loc_start'),
                'loc_final': r.get('loc_final'),
                'pct': r.get('pct'),
                'tests_ok': r.get('tests_ok'),
                # only set when `lc` never produced a report at all (it
                # could not even be launched, or it crashed outright);
                # None above already distinguishes "did not run" from "ran
                # and found nothing", this adds *why* for the first case
                'error': r.get('error'),
            }
            for r in payload['per_language']
        ],
        'output': str(Path(args.output_dir) / 'less_code_pass.json'),
    }, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
