#!/usr/bin/env python3
"""
audit_context.py — score existing context docs against best practices.

Usage:
    python3 audit_context.py <project_dir>
    python3 audit_context.py <project_dir> --check-pointers
    python3 audit_context.py <project_dir> --check-globs

Outputs JSON to stdout (or human-readable text for --check-globs).
Stdlib only — no third-party dependencies.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path


# ── Constants ──────────────────────────────────────────────────────────────────

SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "env",
    "dist", "build", "target", ".next", ".nuxt", "coverage",
}


# ── Helpers ──────────────────────────────────────────────────────────────────

def read_file(path: Path) -> list[str]:
    """Read file lines. Returns empty list on error."""
    try:
        return path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return []


def count_lines(path: Path) -> int:
    """Count non-empty lines."""
    return sum(1 for line in read_file(path) if line.strip())


def has_frontmatter(lines: list[str]) -> bool:
    return bool(lines) and lines[0].strip() == "---"


# agentify header: <!-- agentify: generated YYYY-MM-DD | score-before: N | source: X.Y.Z -->
_AGENTIFY_HEADER_RE = re.compile(
    r"<!--\s*agentify:\s*generated\s+(\d{4}-\d{2}-\d{2})"
    r"(?:\s*\|\s*score-before:\s*(\d+))?"
    r"(?:\s*\|\s*source:\s*([\d.]+))?",
    re.IGNORECASE,
)

def parse_agentify_header(lines: list[str]) -> dict | None:
    """Extract agentify provenance header from the first line, or return None."""
    if not lines:
        return None
    m = _AGENTIFY_HEADER_RE.search(lines[0])
    if not m:
        return None
    return {
        "date": m.group(1),
        "score_before": int(m.group(2)) if m.group(2) else None,
        "source_version": m.group(3),
    }


def read_lock_date(root: Path) -> str | None:
    """Read the date from .agentify-lock, or return None."""
    lock_path = root / ".agentify-lock"
    if not lock_path.exists():
        return None
    try:
        data = json.loads(lock_path.read_text(encoding="utf-8"))
        return data.get("date")
    except (json.JSONDecodeError, OSError):
        return None


def count_commits_since(root: Path, since_date: str, path_filter: str) -> int:
    """Count git commits since `since_date` touching `path_filter`. Returns 0 on error."""
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "log", "--oneline",
             f"--since={since_date}", "--", path_filter],
            capture_output=True, text=True, timeout=5,
        )
        return len([l for l in result.stdout.splitlines() if l.strip()])
    except (subprocess.SubprocessError, OSError):
        return 0


def extract_frontmatter(lines: list[str]) -> tuple[dict[str, list[str]], int]:
    """
    Extract simple YAML frontmatter from lines.
    Returns (fields_dict, end_line_index) where fields_dict maps field names
    to lists of values (for list fields) or [single_value].
    end_line_index is the line after the closing ---.
    """
    if not has_frontmatter(lines):
        return {}, 0

    fields: dict[str, list[str]] = {}
    current_key = None
    end_idx = len(lines)

    for i, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            end_idx = i + 1
            break
        if ":" in line and not line.startswith(" ") and not line.startswith("\t"):
            key = line.split(":")[0].strip()
            current_key = key
            val = line.split(":", 1)[1].strip()
            if val.startswith("[") and val.endswith("]"):
                # YAML flow sequence: ["a", "b"] or ['a', 'b'] or [a, b]
                inner = val[1:-1]
                items = [m.group(1) or m.group(2) or m.group(3)
                         for m in re.finditer(r'"([^"]*)"'
                                              r"|'([^']*)'"
                                              r"|([^\s,\[\]\"'][^,\[\]]*[^\s,\[\]\"\']|[^\s,\[\]\"'])",
                                              inner)]
                fields[key] = [i.strip() for i in items if i and i.strip()]
            else:
                fields[key] = [val] if val else []
        elif line.strip().startswith("- ") and current_key:
            val = line.strip()[2:].strip().strip("\"'")
            fields.setdefault(current_key, []).append(val)

    return fields, end_idx


def glob_matches_files(pattern: str, root: Path) -> bool:
    """
    Return True if the pattern matches at least one file under root.
    Supports brace expansion: src/**/*.{ts,tsx} matches .ts and .tsx files.
    """
    import fnmatch

    expanded_patterns = [pattern]

    # Handle brace expansion: {.ts,.tsx} → [.ts, .tsx]
    brace_match = re.search(r'\{([^}]+)\}', pattern)
    if brace_match:
        options = [o.strip() for o in brace_match.group(1).split(",")]
        expanded_patterns = [
            pattern[:brace_match.start()] + opt + pattern[brace_match.end():]
            for opt in options
        ]

    for pat in expanded_patterns:
        pat = pat.lstrip("/")

        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames
                           if d not in SKIP_DIRS and not d.startswith(".")]

            for filename in filenames:
                full_path = Path(dirpath) / filename
                rel_path = str(full_path.relative_to(root))

                # Try direct fnmatch
                if fnmatch.fnmatch(rel_path, pat):
                    return True

                # Handle ** — convert to fnmatch-compatible pattern
                if "**" in pat:
                    parts = pat.split("**")
                    regex_parts = [re.escape(p).replace(r"\*", "[^/]*").replace(r"\?", "[^/]")
                                   for p in parts]
                    regex = ".*".join(regex_parts)
                    regex = "^" + regex + "$"
                    if re.match(regex, rel_path):
                        return True

    return False


# ── CLAUDE.md audit ──────────────────────────────────────────────────────────

def audit_claude_md(path: Path) -> dict:
    """
    Score CLAUDE.md against best practices (100 points total).

    Rubric:
    - 15pts: line count ≤200
    - 10pts: has project name + purpose in first 30 lines
    - 15pts: has key commands section (build/test/run/lint)
    - 15pts: has navigation/pointer map section
    - 15pts: navigation/pointer map is in the last 50 lines
    - 10pts: no buried architecture (no Mermaid diagrams)
    - 10pts: uses @import for modular instructions (new in Claude Code 2026)
    - 10pts: has AGENTS.md integration if AGENTS.md exists in repo
    """
    if not path.exists():
        return {
            "path": str(path),
            "exists": False,
            "score": 0,
            "line_count": 0,
            "issues": ["CLAUDE.md does not exist"],
            "strengths": [],
        }

    lines = read_file(path)
    full_content = "\n".join(lines)
    line_count = sum(1 for l in lines if l.strip())
    score = 0
    issues = []
    strengths = []

    # 15pts: line count ≤200
    if line_count <= 200:
        score += 15
        strengths.append(f"Line count {line_count} within 200-line budget")
    elif line_count <= 300:
        score += 8
        issues.append(f"Line count {line_count} exceeds 200-line budget (moderate overage)")
    else:
        issues.append(f"Line count {line_count} significantly exceeds 200-line budget")

    # 10pts: purpose in first 30 lines
    first_30 = "\n".join(lines[:30]).lower()
    purpose_signals = ["is a", "is an", "provides", "enables", "builds", "generates",
                       "manages", "handles", "implements", "a tool", "a service",
                       "a library", "a framework", "a cli", "a web"]
    if any(sig in first_30 for sig in purpose_signals):
        score += 10
        strengths.append("Project purpose described in first 30 lines")
    else:
        issues.append("Project purpose not clearly stated in first 30 lines (lost-in-middle risk)")

    # 15pts: key commands
    content_lower = full_content.lower()
    has_commands = (
        ("npm run" in content_lower or "cargo " in content_lower or
         "go build" in content_lower or "pytest" in content_lower or
         "make " in content_lower or "just " in content_lower or
         "python" in content_lower or "deno " in content_lower or
         "yarn " in content_lower or "pnpm " in content_lower)
        and
        any(w in content_lower for w in ["build", "test", "run", "start", "install"])
    )
    if has_commands:
        score += 15
        strengths.append("Key commands section present")
    else:
        issues.append("No key commands found (build/test/run/lint) — agents need these")

    # 15pts: navigation/pointer map
    nav_patterns = [
        r"##?\s*(navigation|nav|pointer|map|docs|documentation|find|where)",
        r"\|\s*[^|]+\s*\|\s*(docs?/|\.claude/|see )",
        r"(see|read)\s+`?(docs?/|\.claude/)",
        r"\[.+\]\(.+(\.md|\.txt)\)",
    ]
    has_nav = any(re.search(p, full_content, re.IGNORECASE) for p in nav_patterns)
    if has_nav:
        score += 15
        strengths.append("Navigation/pointer map section found")
    else:
        issues.append("No navigation/pointer map found — agents cannot navigate to deeper docs")

    # 15pts: navigation in last 50 lines
    if has_nav:
        last_50 = "\n".join(lines[-50:])
        nav_in_last_50 = any(re.search(p, last_50, re.IGNORECASE) for p in nav_patterns)
        if nav_in_last_50:
            score += 15
            strengths.append("Navigation section near end of file (optimal recency placement)")
        else:
            issues.append("Navigation section not in last 50 lines — move it to the end for better agent scanning")

    # 10pts: no buried architecture (Mermaid diagrams belong in OVERVIEW)
    has_mermaid = "```mermaid" in full_content
    if not has_mermaid:
        score += 10
        strengths.append("No Mermaid diagrams (correct — architecture belongs in docs/OVERVIEW.md)")
    else:
        issues.append("Mermaid diagram found in CLAUDE.md — move architecture to docs/OVERVIEW.md to save tokens")

    # 10pts: @import usage (modular instructions — new in Claude Code 2026)
    has_imports = bool(re.search(r'^@\S+', full_content, re.MULTILINE))
    if has_imports:
        score += 10
        strengths.append("Uses @import for modular instructions (saves context)")
    else:
        # Only flag as issue if line_count > 150 (the file is big enough to benefit)
        if line_count > 150:
            issues.append("No @import usage — consider importing sub-files to keep CLAUDE.md lean")
        else:
            score += 5
            strengths.append("No @import needed (file is concise)")

    # 10pts: AGENTS.md integration (if AGENTS.md exists)
    root = path.parent
    agents_path = root / "AGENTS.md"
    if agents_path.exists():
        has_agents_ref = "agents.md" in full_content.lower() or "@AGENTS.md" in full_content
        if has_agents_ref:
            score += 10
            strengths.append("References AGENTS.md (interop with other coding agents)")
        else:
            issues.append("AGENTS.md exists in repo but not referenced by CLAUDE.md — add '@AGENTS.md' import")

    return {
        "path": str(path),
        "exists": True,
        "score": score,
        "line_count": line_count,
        "has_imports": bool(re.search(r'^@\S+', full_content, re.MULTILINE)),
        "refers_to_agents_md": agents_path.exists() and ("agents.md" in full_content.lower()),
        "agentify_header": parse_agentify_header(lines),
        "issues": issues,
        "strengths": strengths,
    }


# ── Rules file audit ──────────────────────────────────────────────────────────

def audit_auto_memory(root: Path) -> dict:
    """
    Check if auto memory exists for this project and assess complementarity.
    Auto memory is Claude-managed — this skill never modifies it,
    but generated docs should avoid duplicating its content.
    """
    result = {"exists": False, "path": "", "line_count": 0, "score": 0,
              "issues": [], "strengths": []}

    try:
        home = Path.home()
        memory_base = home / ".claude" / "projects"

        if not memory_base.exists():
            return result

        project_name = root.resolve().name.lower()
        for project_dir in memory_base.iterdir():
            if not project_dir.is_dir():
                continue
            memory_file = project_dir / "memory" / "MEMORY.md"
            if memory_file.exists():
                result["exists"] = True
                result["path"] = str(memory_file)
                lines = read_file(memory_file)
                result["line_count"] = sum(1 for l in lines if l.strip())
                result["strengths"].append(f"Auto memory found ({result['line_count']} lines)")
                result["score"] = 100  # Auto memory is always good — it's Claude-managed
                break

    except (OSError, PermissionError):
        pass

    return result


def audit_rules_files(rules_dir: Path, root: Path) -> list[dict]:
    """
    Score each .claude/rules/*.md file.

    Rubric per file:
    - 30pts: has YAML frontmatter with paths: field (path-scoped)
    - 10pts: is unconditionally always-loaded (has no paths: — scores differently)
    - 20pts: line count ≤100
    - 20pts: has at least one concrete convention
    - 20pts: paths globs match at least one actual file in the repo
    """
    results = []
    if not rules_dir.exists():
        return results

    for f in sorted(rules_dir.glob("*.md")):
        lines = read_file(f)
        line_count = sum(1 for l in lines if l.strip())
        score = 0
        issues = []
        strengths = []

        fm, fm_end = extract_frontmatter(lines)
        has_paths_field = "paths" in fm and bool(fm["paths"])
        has_braces = any("{" in g for g in fm.get("paths", []))

        # 30pts: has frontmatter with paths: (path-scoped rule)
        if has_frontmatter(lines) and has_paths_field:
            score += 30
            brace_note = " (using brace expansion)" if has_braces else ""
            strengths.append(f"Has paths: frontmatter with {len(fm['paths'])} glob(s){brace_note} (path-scoped)")
        elif has_frontmatter(lines):
            score += 5
            issues.append("Has frontmatter but missing paths: field — this rule loads for ALL files, not just relevant ones. Add paths: to scope it.")
        else:
            score += 3  # Always-loaded rules can be fine if intentional
            if line_count > 60:
                issues.append("No YAML frontmatter — rules file will always load. If >60 lines, strongly consider adding paths: to scope it.")

        # 20pts: line count ≤100
        if line_count <= 100:
            score += 20
            strengths.append(f"Line count {line_count} within 100-line budget")
        else:
            issues.append(f"Line count {line_count} exceeds 100-line budget — consider splitting this domain")

        # 20pts: concrete conventions (not just headers)
        body = "\n".join(lines[fm_end:])
        has_conventions = bool(re.search(
            r"(must|should|always|never|use|avoid|do not|don't|prefer|ensure|IMPORTANT)",
            body, re.IGNORECASE
        ))
        if has_conventions:
            score += 20
            strengths.append("Contains concrete conventions (imperative language found)")
        else:
            issues.append("No concrete conventions found — just headers? Add actionable rules.")

        # 20pts: globs match actual files
        paths_match = False
        if has_paths_field:
            paths_match = any(glob_matches_files(g, root) for g in fm["paths"])
            if paths_match:
                score += 20
                strengths.append("Paths globs match actual files in the repo")
            else:
                issues.append(f"Paths globs {fm['paths']} do not match any files in repo — fix the glob patterns")

        results.append({
            "path": str(f.relative_to(root)),
            "score": score,
            "line_count": line_count,
            "has_frontmatter": has_frontmatter(lines),
            "has_paths_field": has_paths_field,
            "is_always_loaded": not has_paths_field,
            "uses_brace_expansion": has_braces,
            "paths_patterns": fm.get("paths", []),
            "paths_match_files": paths_match,
            "issues": issues,
            "strengths": strengths,
        })

    return results


# ── docs/OVERVIEW.md audit ──────────────────────────────────────────────────

def audit_overview(path: Path) -> dict:
    """
    Score docs/OVERVIEW.md.

    Rubric:
    - 25pts: has at least one Mermaid diagram
    - 25pts: line count ≤400
    - 25pts: has components section or table
    - 25pts: has data flow section
    """
    if not path.exists():
        return {
            "path": str(path),
            "exists": False,
            "score": 0,
            "line_count": 0,
            "has_mermaid_diagram": False,
            "issues": ["docs/OVERVIEW.md does not exist"],
            "strengths": [],
        }

    lines = read_file(path)
    line_count = sum(1 for l in lines if l.strip())
    full_content = "\n".join(lines)
    score = 0
    issues = []
    strengths = []

    # 25pts: Mermaid diagram
    has_mermaid = "```mermaid" in full_content
    if has_mermaid:
        score += 25
        strengths.append("Contains Mermaid diagram")
    else:
        issues.append("No Mermaid diagram — add architecture/flow diagrams for visual orientation")

    # 25pts: line count ≤400
    if line_count <= 400:
        score += 25
        strengths.append(f"Line count {line_count} within 400-line budget")
    else:
        issues.append(f"Line count {line_count} exceeds 400-line budget — move detail to component docs")

    # 25pts: components section
    has_components = bool(re.search(
        r"##?\s*(component|module|service|layer|package|architecture)",
        full_content, re.IGNORECASE
    ))
    if has_components:
        score += 25
        strengths.append("Has components/architecture section")
    else:
        issues.append("No components section — add a table listing major components and their responsibilities")

    # 25pts: data flow section
    has_flow = bool(re.search(
        r"(##?\s*(data\s*flow|request\s*flow|flow|sequence|pipeline)|sequenceDiagram)",
        full_content, re.IGNORECASE
    ))
    if has_flow:
        score += 25
        strengths.append("Has data flow section")
    else:
        issues.append("No data flow section — add a sequence diagram or narrative showing the primary request/data path")

    return {
        "path": str(path),
        "exists": True,
        "score": score,
        "line_count": line_count,
        "has_mermaid_diagram": has_mermaid,
        "agentify_header": parse_agentify_header(lines),
        "issues": issues,
        "strengths": strengths,
    }


# ── Component docs audit ──────────────────────────────────────────────────────

def audit_component_docs(docs_dir: Path, root: Path) -> list[dict]:
    """
    Score each docs/{component}.md (excluding OVERVIEW.md and NAVIGATION.md).

    Rubric per file:
    - 30pts: line count ≤300
    - 25pts: has key files section
    - 25pts: has patterns/conventions section
    - 20pts: has "see also" or cross-reference links
    """
    results = []
    if not docs_dir.exists():
        return results

    skip = {"OVERVIEW.md", "NAVIGATION.md", "overview.md", "navigation.md"}
    for f in sorted(docs_dir.glob("*.md")):
        if f.name in skip:
            continue

        lines = read_file(f)
        line_count = sum(1 for l in lines if l.strip())
        full_content = "\n".join(lines)
        score = 0
        issues = []
        strengths = []

        # 30pts: line count ≤300
        if line_count <= 300:
            score += 30
            strengths.append(f"Line count {line_count} within 300-line budget")
        else:
            issues.append(f"Line count {line_count} exceeds 300-line budget — consider splitting")

        # 25pts: key files section
        has_key_files = bool(re.search(
            r"##?\s*(key\s*files?|important\s*files?|files?|structure)",
            full_content, re.IGNORECASE
        ))
        if has_key_files:
            score += 25
            strengths.append("Has key files section")
        else:
            issues.append("No key files section — list the most important files with one-line descriptions")

        # 25pts: patterns section
        has_patterns = bool(re.search(
            r"##?\s*(pattern|convention|approach|usage|how\s+to|guideline)",
            full_content, re.IGNORECASE
        ))
        if has_patterns:
            score += 25
            strengths.append("Has patterns/conventions section")
        else:
            issues.append("No patterns section — document the key conventions used in this component")

        # 20pts: see also / cross-links
        has_see_also = bool(re.search(
            r"(see\s+also|related|cross.?ref|\[.+\]\(.+\.md\))",
            full_content, re.IGNORECASE
        ))
        if has_see_also:
            score += 20
            strengths.append("Has cross-reference links")
        else:
            issues.append("No cross-reference links — add 'See also' links to related component docs")

        results.append({
            "path": str(f.relative_to(root)),
            "score": score,
            "line_count": line_count,
            "agentify_header": parse_agentify_header(lines),
            "issues": issues,
            "strengths": strengths,
        })

    return results


# ── Coordination directory audit ─────────────────────────────────────────────

def audit_coordination_dir(coord_dir: Path, dir_type: str, root: Path) -> dict:
    """
    Score a coordination directory (docs/plans/, docs/specs/, docs/reviews/).

    Rubric (100 pts total):
    - 30pts: README.md exists and is ≤80 lines
    - 30pts: README.md has an "example" or "template" section
    - 20pts: at least one artifact file exists (dir is in active use)
    - 20pts: artifact files have frontmatter with title/status/date fields
    """
    score = 0
    issues = []
    strengths = []

    artifact_files = [f for f in sorted(coord_dir.glob("*.md")) if f.name.lower() != "readme.md"]
    readme_path = coord_dir / "README.md"
    readme_line_count = 0

    # 30pts: README.md exists and ≤80 lines
    if readme_path.exists():
        readme_lines = read_file(readme_path)
        readme_line_count = sum(1 for l in readme_lines if l.strip())
        if readme_line_count <= 80:
            score += 30
            strengths.append(f"README.md exists and is within 80-line budget ({readme_line_count} lines)")
        else:
            score += 15
            issues.append(f"README.md exists but is {readme_line_count} lines (budget: ≤80)")
    else:
        issues.append("No README.md stub — create one explaining the directory purpose and file format")

    # 30pts: README.md has example or template section
    if readme_path.exists():
        readme_content = "\n".join(read_file(readme_path))
        has_example = bool(re.search(r"##?\s*(example|template|format|skeleton)", readme_content, re.IGNORECASE))
        if has_example:
            score += 30
            strengths.append("README.md includes an example/template section")
        else:
            issues.append("README.md has no example section — add a skeleton file format so agents know what to write")

    # 20pts: at least one artifact file exists
    if artifact_files:
        score += 20
        strengths.append(f"{len(artifact_files)} artifact file(s) in use")
    else:
        issues.append(f"No artifact files yet — directory is empty (this is fine for new repos)")

    # 20pts: artifact files have frontmatter with title/status/date
    if artifact_files:
        frontmatter_count = 0
        for f in artifact_files[:5]:  # check up to 5 files
            content = "\n".join(read_file(f))
            has_fm = bool(re.match(r"^---\s*\n", content))
            has_required = all(kw in content for kw in ("title", "status"))
            if has_fm and has_required:
                frontmatter_count += 1
        if frontmatter_count == len(artifact_files[:5]):
            score += 20
            strengths.append("Artifact files have structured frontmatter")
        elif frontmatter_count > 0:
            score += 10
            issues.append(f"Only {frontmatter_count}/{len(artifact_files[:5])} artifact files have frontmatter with title/status")
        else:
            issues.append("Artifact files lack frontmatter — add title/status/date fields for agent discoverability")

    return {
        "path": str(coord_dir.relative_to(root)),
        "dir_type": dir_type,
        "exists": True,
        "score": score,
        "file_count": len(artifact_files),
        "has_readme": readme_path.exists(),
        "readme_line_count": readme_line_count,
        "issues": issues,
        "strengths": strengths,
    }


def audit_coordination_dirs(docs_dir: Path, root: Path) -> list[dict]:
    """Audit all three coordination directories if they exist."""
    results = []
    for dir_type in ("plans", "specs", "reviews"):
        coord_dir = docs_dir / dir_type
        if coord_dir.exists() and coord_dir.is_dir():
            results.append(audit_coordination_dir(coord_dir, dir_type, root))
    return results


# ── Pointer consistency check ──────────────────────────────────────────────

def check_pointers(root: Path) -> list[dict]:
    """
    Extract all file references from CLAUDE.md and .claude/context-map.md,
    then check that each target file exists.

    Patterns matched:
    - "see docs/foo.md"
    - "read .claude/rules/api.md"
    - "→ docs/foo.md"
    - Markdown links: [text](path.md)
    - Table cells: | topic | docs/foo.md |
    """
    results = []
    source_files = [
        root / "CLAUDE.md",
        root / ".claude" / "context-map.md",
        root / "docs" / "OVERVIEW.md",
    ]

    # Pattern to find file references
    file_ref_patterns = [
        r"(?:see|read|→|->)\s+[`']?([a-zA-Z0-9_./-]+\.md)[`']?",
        r"\[(?:[^\]]+)\]\(([a-zA-Z0-9_./-]+\.md)\)",
        r"\|\s*([a-zA-Z0-9_./-]+\.md)\s*\|",
        r"[`']([a-zA-Z0-9_./-]+\.md)[`']",
    ]

    for source_path in source_files:
        if not source_path.exists():
            continue

        content = source_path.read_text(encoding="utf-8", errors="ignore")
        found_refs = set()

        for pattern in file_ref_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                ref = match.group(1)
                # Normalize: remove leading ./
                ref = ref.lstrip("./")
                found_refs.add(ref)

        for ref in found_refs:
            target = root / ref
            results.append({
                "source_file": str(source_path.relative_to(root)),
                "pointer": ref,
                "target_file": ref,
                "exists": target.exists(),
            })

    # Deduplicate by (source, target)
    seen = set()
    deduped = []
    for r in results:
        key = (r["source_file"], r["target_file"])
        if key not in seen:
            seen.add(key)
            deduped.append(r)

    return deduped


# ── Staleness detection ───────────────────────────────────────────────────────

def detect_staleness(root: Path, component_results: list[dict], lock_date: str | None) -> list[dict]:
    """
    For each component doc, count commits to the inferred source directory
    since `lock_date`. Annotates each result with commits_since_lock and is_stale.

    A doc is stale when: score > 80 (kept last time) AND commits_since_lock > 3,
    OR when the agentify_header date is older than lock_date.

    Returns an updated copy of component_results plus a stale_docs summary list.
    """
    if not lock_date:
        for r in component_results:
            r["commits_since_lock"] = 0
            r["is_stale"] = False
        return component_results

    for r in component_results:
        doc_path = r["path"]  # e.g. "docs/api.md"
        # Infer source dir: docs/api.md → look for src/api/, api/, services/api/ etc.
        stem = Path(doc_path).stem  # "api"
        candidate_paths = [stem, f"src/{stem}", f"services/{stem}", f"packages/{stem}"]
        commits = 0
        for candidate in candidate_paths:
            n = count_commits_since(root, lock_date, candidate)
            if n > 0:
                commits = n
                break

        # Also check if header date is older than lock_date (doc predates lock)
        header = r.get("agentify_header")
        header_stale = (
            header is not None
            and header["date"] is not None
            and header["date"] < lock_date
        )

        r["commits_since_lock"] = commits
        r["is_stale"] = (r["score"] > 80 and commits > 3) or header_stale

    return component_results


# ── Full audit ──────────────────────────────────────────────────────────────

def full_audit(root: Path) -> dict:
    """Run all audit checks and return the combined JSON result."""
    claude_md_result = audit_claude_md(root / "CLAUDE.md")
    auto_memory_result = audit_auto_memory(root)
    rules_results = audit_rules_files(root / ".claude" / "rules", root)
    overview_result = audit_overview(root / "docs" / "OVERVIEW.md")
    component_results = audit_component_docs(root / "docs", root)
    coordination_results = audit_coordination_dirs(root / "docs", root)
    pointer_results = check_pointers(root)

    # Staleness check: annotate component docs with git activity since last lock
    lock_date = read_lock_date(root)
    component_results = detect_staleness(root, component_results, lock_date)
    stale_docs = [r["path"] for r in component_results if r.get("is_stale")]

    broken_pointers = [p for p in pointer_results if not p["exists"]]

    # Calculate overall score
    scores = [claude_md_result["score"]]
    scores.append(overview_result["score"] if overview_result["exists"] else 0)
    for r in rules_results:
        scores.append(r["score"])
    for r in component_results:
        scores.append(r["score"])
    for r in coordination_results:
        scores.append(r["score"])

    overall = int(sum(scores) / len(scores)) if scores else 0

    return {
        "claude_md": claude_md_result,
        "auto_memory": auto_memory_result,
        "rules_files": rules_results,
        "overview": overview_result,
        "component_docs": component_results,
        "coordination_dirs": coordination_results,
        "pointers": pointer_results,
        "broken_pointers": broken_pointers,
        "stale_docs": stale_docs,
        "lock_date": lock_date,
        "overall_score": overall,
    }


# ── Entry point ──────────────────────────────────────────────────────────────

def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Audit context docs in a repo and output JSON."
    )
    parser.add_argument("project_dir", help="Root directory of the project to audit")
    parser.add_argument(
        "--check-pointers",
        action="store_true",
        help="Only run pointer consistency check (CLAUDE.md + context-map.md refs)",
    )
    parser.add_argument(
        "--check-globs",
        action="store_true",
        help="Validate that paths: globs in .claude/rules/*.md match real files",
    )
    parser.add_argument(
        "--output", "-o",
        help="Write JSON to this file instead of stdout",
        default=None,
    )
    args = parser.parse_args()

    root = Path(args.project_dir).resolve()
    if not root.is_dir():
        print(f"Error: {root} is not a directory", file=sys.stderr)
        sys.exit(1)

    if args.check_globs:
        # Human-readable glob validation — uses the existing glob_matches_files()
        rules_results = audit_rules_files(root / ".claude" / "rules", root)
        any_issues = False
        for r in rules_results:
            glob_issues = [i for i in r["issues"] if "glob" in i.lower() or "paths" in i.lower()]
            if glob_issues:
                any_issues = True
                print(f"GLOB MISMATCH: {r['path']}")
                for issue in glob_issues:
                    print(f"  - {issue}")
        if not any_issues:
            print("All .claude/rules/ globs match files in the repo.")
        return
    elif args.check_pointers:
        result = {"pointers": check_pointers(root)}
        result["broken_pointers"] = [p for p in result["pointers"] if not p["exists"]]
    else:
        result = full_audit(root)

    output = json.dumps(result, indent=2)

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(output, encoding="utf-8")
    else:
        print(output)


if __name__ == "__main__":
    main()
