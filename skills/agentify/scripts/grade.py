#!/usr/bin/env python3
"""
grade.py — automated grader for agentify evals.

Given a project_dir where agentify has been run, checks file-based
eval expectations and emits a grading.json summary.

Not all expectations are file-checkable (e.g. "Phase 3 pauses for
confirmation" requires human review). grade.py focuses on verifiable
file outcomes: existence, line counts, content patterns, lock schema.

Usage:
    python3 grade.py <project_dir> [--output grading.json]

Stdlib only — no third-party dependencies.
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import NamedTuple


# ── Result type ───────────────────────────────────────────────────────────────

class CheckResult(NamedTuple):
    check: str
    passed: bool
    detail: str
    skipped: bool = False


# ── Individual check functions ────────────────────────────────────────────────

def check_file_exists(project_dir: Path, rel_path: str) -> CheckResult:
    path = project_dir / rel_path
    exists = path.exists()
    return CheckResult(
        check=f"{rel_path} exists",
        passed=exists,
        detail="" if exists else f"{rel_path} not found",
    )


def check_file_line_count(project_dir: Path, rel_path: str, max_lines: int) -> CheckResult:
    path = project_dir / rel_path
    if not path.exists():
        return CheckResult(check=f"{rel_path} ≤{max_lines} lines", passed=False,
                           detail=f"{rel_path} does not exist")
    try:
        lines = [l for l in path.read_text(encoding="utf-8", errors="ignore").splitlines() if l.strip()]
        n = len(lines)
        passed = n <= max_lines
        return CheckResult(
            check=f"{rel_path} ≤{max_lines} lines",
            passed=passed,
            detail=f"{n} lines" if passed else f"{n} lines (exceeds {max_lines})",
        )
    except OSError as e:
        return CheckResult(check=f"{rel_path} ≤{max_lines} lines", passed=False, detail=str(e))


def check_file_contains(project_dir: Path, rel_path: str, pattern: str,
                        description: str, invert: bool = False) -> CheckResult:
    path = project_dir / rel_path
    if not path.exists():
        return CheckResult(check=description, passed=False, detail=f"{rel_path} does not exist")
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
        found = bool(re.search(pattern, content, re.IGNORECASE | re.MULTILINE))
        passed = (not found) if invert else found
        detail = "" if passed else (
            f"Pattern not found: {pattern!r}" if not invert
            else f"Forbidden pattern found: {pattern!r}"
        )
        return CheckResult(check=description, passed=passed, detail=detail)
    except OSError as e:
        return CheckResult(check=description, passed=False, detail=str(e))


def check_lock_file(project_dir: Path) -> list[CheckResult]:
    """Check .agentify-lock exists and has expected schema."""
    lock_path = project_dir / ".agentify-lock"
    if not lock_path.exists():
        return [CheckResult(check=".agentify-lock exists", passed=False, detail="not found")]

    results = [CheckResult(check=".agentify-lock exists", passed=True, detail="")]
    try:
        data = json.loads(lock_path.read_text(encoding="utf-8"))
        for key in ("date", "skill_version", "project_name", "project_type",
                    "files_created", "files_updated", "files_kept"):
            present = key in data
            results.append(CheckResult(
                check=f".agentify-lock has '{key}' field",
                passed=present,
                detail="" if present else f"missing key: {key}",
            ))
    except (json.JSONDecodeError, OSError) as e:
        results.append(CheckResult(check=".agentify-lock valid JSON", passed=False, detail=str(e)))
    return results


def check_rules_directory(project_dir: Path) -> list[CheckResult]:
    """Check .claude/rules/ has at least one file with paths: frontmatter."""
    rules_dir = project_dir / ".claude" / "rules"
    if not rules_dir.exists():
        return [CheckResult(check=".claude/rules/ directory exists", passed=False,
                            detail=".claude/rules/ not found")]
    results = [CheckResult(check=".claude/rules/ directory exists", passed=True, detail="")]
    rule_files = list(rules_dir.glob("*.md"))
    if not rule_files:
        results.append(CheckResult(check="At least one rules file created", passed=False,
                                   detail=".claude/rules/ is empty"))
        return results
    results.append(CheckResult(check="At least one rules file created", passed=True,
                               detail=f"{len(rule_files)} file(s)"))
    has_paths = False
    for f in rule_files:
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
            if "paths:" in content:
                has_paths = True
                break
        except OSError:
            pass
    results.append(CheckResult(
        check="At least one rules file has paths: frontmatter",
        passed=has_paths,
        detail="" if has_paths else "No rules file has a paths: field in frontmatter",
    ))
    return results


def check_pointers(project_dir: Path, audit_script: Path) -> CheckResult:
    """Run --check-pointers and verify no broken pointers."""
    if not audit_script.exists():
        return CheckResult(check="No broken pointers in CLAUDE.md/context-map.md",
                           passed=False, detail=f"audit_context.py not found at {audit_script}",
                           skipped=True)
    try:
        result = subprocess.run(
            [sys.executable, str(audit_script), str(project_dir), "--check-pointers"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            return CheckResult(check="No broken pointers", passed=False, detail=result.stderr[:200])
        data = json.loads(result.stdout)
        broken = data.get("broken_pointers", [])
        if broken:
            summary = ", ".join(f"{p['source_file']}→{p['pointer']}" for p in broken[:3])
            return CheckResult(check="No broken pointers", passed=False,
                               detail=f"{len(broken)} broken: {summary}")
        return CheckResult(check="No broken pointers", passed=True, detail="")
    except (subprocess.SubprocessError, json.JSONDecodeError, OSError) as e:
        return CheckResult(check="No broken pointers", passed=False, detail=str(e), skipped=True)


def check_globs(project_dir: Path, audit_script: Path) -> CheckResult:
    """Run --check-globs and verify no mismatches."""
    if not audit_script.exists():
        return CheckResult(check="All .claude/rules/ globs match files",
                           passed=False, detail="audit_context.py not found", skipped=True)
    rules_dir = project_dir / ".claude" / "rules"
    if not rules_dir.exists():
        return CheckResult(check="All .claude/rules/ globs match files",
                           passed=True, detail="no rules dir (skip)", skipped=True)
    try:
        result = subprocess.run(
            [sys.executable, str(audit_script), str(project_dir), "--check-globs"],
            capture_output=True, text=True, timeout=30,
        )
        passed = "GLOB MISMATCH" not in result.stdout
        detail = result.stdout.strip() if not passed else ""
        return CheckResult(check="All .claude/rules/ globs match files", passed=passed, detail=detail)
    except (subprocess.SubprocessError, OSError) as e:
        return CheckResult(check="All .claude/rules/ globs match files",
                           passed=False, detail=str(e), skipped=True)


# ── Standard check suite ──────────────────────────────────────────────────────

def run_standard_checks(project_dir: Path, audit_script: Path) -> list[CheckResult]:
    """
    Run the standard set of file-based checks applicable to every agentify run.
    Returns a flat list of CheckResult items.
    """
    results: list[CheckResult] = []

    # CLAUDE.md
    results.append(check_file_exists(project_dir, "CLAUDE.md"))
    results.append(check_file_line_count(project_dir, "CLAUDE.md", 200))
    results.append(check_file_contains(project_dir, "CLAUDE.md",
        r"```mermaid", "CLAUDE.md does NOT contain Mermaid diagrams", invert=True))
    results.append(check_file_contains(project_dir, "CLAUDE.md",
        r"\|\s*\S.+\|\s*\S",  # at least one markdown table row
        "CLAUDE.md has a navigation table"))
    results.append(check_file_contains(project_dir, "CLAUDE.md",
        r"<!-- agentify:", "CLAUDE.md has agentify header"))

    # .claude/rules/
    results.extend(check_rules_directory(project_dir))
    results.append(check_globs(project_dir, audit_script))

    # .claude/context-map.md
    results.append(check_file_exists(project_dir, ".claude/context-map.md"))
    results.append(check_file_line_count(project_dir, ".claude/context-map.md", 150))

    # docs/OVERVIEW.md
    results.append(check_file_exists(project_dir, "docs/OVERVIEW.md"))
    results.append(check_file_line_count(project_dir, "docs/OVERVIEW.md", 400))
    results.append(check_file_contains(project_dir, "docs/OVERVIEW.md",
        r"```mermaid", "docs/OVERVIEW.md contains Mermaid diagram"))

    # docs/NAVIGATION.md
    results.append(check_file_exists(project_dir, "docs/NAVIGATION.md"))

    # .agentify-lock
    results.extend(check_lock_file(project_dir))

    # Pointer integrity
    results.append(check_pointers(project_dir, audit_script))

    return results


def run_coordination_checks(project_dir: Path) -> list[CheckResult]:
    """Checks for when coordination dirs were expected to be created."""
    results = []
    for dir_name in ("plans", "specs", "reviews"):
        readme = f"docs/{dir_name}/README.md"
        results.append(check_file_exists(project_dir, readme))
        results.append(check_file_line_count(project_dir, readme, 80))
        results.append(check_file_contains(project_dir, readme,
            r"(example|template|format|skeleton)",
            f"docs/{dir_name}/README.md has example/template section"))
    results.append(check_file_contains(project_dir, "CLAUDE.md",
        r"docs/plans", "CLAUDE.md navigation has docs/plans/ entry"))
    results.append(check_file_contains(project_dir, "CLAUDE.md",
        r"docs/specs", "CLAUDE.md navigation has docs/specs/ entry"))
    results.append(check_file_contains(project_dir, "CLAUDE.md",
        r"docs/reviews", "CLAUDE.md navigation has docs/reviews/ entry"))
    return results


def run_no_coordination_checks(project_dir: Path) -> list[CheckResult]:
    """Checks for when coordination dirs should NOT have been created."""
    results = []
    for dir_name in ("plans", "specs", "reviews"):
        path = project_dir / "docs" / dir_name
        exists = path.exists()
        results.append(CheckResult(
            check=f"docs/{dir_name}/ NOT created",
            passed=not exists,
            detail="" if not exists else f"docs/{dir_name}/ exists but should not",
        ))
    return results


# ── Grader entry point ────────────────────────────────────────────────────────

def grade(project_dir: Path, output_path: Path | None = None) -> dict:
    """Run all file-based checks and return (and optionally write) grading.json."""
    skill_dir = Path(__file__).parent.parent
    audit_script = skill_dir / "scripts" / "audit_context.py"

    results = run_standard_checks(project_dir, audit_script)

    # Check for coordination dirs presence to decide which optional suite to run
    lock_path = project_dir / ".agentify-lock"
    if lock_path.exists():
        try:
            lock_data = json.loads(lock_path.read_text(encoding="utf-8"))
            coord_dirs = lock_data.get("coordination_dirs")
            if coord_dirs:
                results.extend(run_coordination_checks(project_dir))
        except (json.JSONDecodeError, OSError):
            pass

    passed = sum(1 for r in results if r.passed and not r.skipped)
    failed = sum(1 for r in results if not r.passed and not r.skipped)
    skipped = sum(1 for r in results if r.skipped)
    total = passed + failed
    score = int(passed / total * 100) if total > 0 else 0

    summary = {
        "project_dir": str(project_dir),
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "pass": passed,
        "fail": failed,
        "skip": skipped,
        "score": score,
        "results": [
            {
                "check": r.check,
                "passed": r.passed,
                "detail": r.detail,
                **({"skipped": True} if r.skipped else {}),
            }
            for r in results
        ],
    }

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"Wrote {output_path}")
    else:
        print(json.dumps(summary, indent=2))

    # Human-readable summary
    print(f"\nGrade: {score}/100  ({passed} pass, {failed} fail, {skipped} skip)",
          file=sys.stderr)
    for r in results:
        if not r.passed and not r.skipped:
            print(f"  FAIL: {r.check}" + (f" — {r.detail}" if r.detail else ""),
                  file=sys.stderr)

    return summary


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Grade an agentify run against file-based eval expectations."
    )
    parser.add_argument("project_dir", help="Directory where agentify was run")
    parser.add_argument("--output", "-o", default=None,
                        help="Write grading.json to this path (default: stdout)")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    if not project_dir.is_dir():
        print(f"Error: {project_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    output_path = Path(args.output) if args.output else None
    summary = grade(project_dir, output_path)
    sys.exit(0 if summary["fail"] == 0 else 1)


if __name__ == "__main__":
    main()
