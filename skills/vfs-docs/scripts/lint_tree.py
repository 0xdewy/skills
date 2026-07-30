#!/usr/bin/env python3
"""
lint_tree.py — check a docs/ tree against the vfs-docs conventions.

Usage:
    python3 lint_tree.py <docs_dir>
    python3 lint_tree.py <docs_dir> --json

Errors (exit 1): index/navigation files, non-kebab-case names, empty or
single-child directories, directories missing their sibling summary file.
Warnings (exit 0): generic filenames, date-prefixed names, unresolved
cross-references (--links only), trees deeper than 4 levels.

Stdlib only — no third-party dependencies.
"""

import argparse
import json
import re
import sys
from pathlib import Path


# ── Constants ─────────────────────────────────────────────────────────────────

# Stems that are index files by another name — the tree is the only index.
FORBIDDEN_STEMS = {
    "readme", "index", "navigation", "toc", "contents", "context-map",
    "start-here", "sitemap",
}

# Stems that name a container instead of the content.
GENERIC_STEMS = {
    "notes", "note", "misc", "stuff", "temp", "tmp", "doc", "docs",
    "document", "general", "other", "info", "details", "important",
    "overview",
}

# kebab-case: lowercase alphanumeric runs joined by single dashes.
KEBAB_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

# Leading date prefix (2024-07-14-foo) — names the occasion, not the content.
DATE_PREFIX_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-")

# An internal cross-reference: a lowercase kebab path ending in .md, found
# either in backticks or as a markdown link target. Capitalized .md names
# (README.md, SPEC.md, AGENTS.md, SKILL.md) are intentionally excluded — they
# are repo-root files, not docs-internal links.
LINK_TICK_RE = re.compile(r"`([a-z0-9][a-z0-9/-]*\.md)`")
LINK_MD_RE = re.compile(r"\]\(([a-z0-9][a-z0-9/-]*\.md)\)")

MAX_DEPTH = 4


# ── Checks ────────────────────────────────────────────────────────────────────

def check_name(rel: Path, is_dir: bool, errors: list, warnings: list) -> None:
    stem = rel.name if is_dir else rel.stem
    if not is_dir and stem.lower() in FORBIDDEN_STEMS:
        errors.append((rel, "index file — the tree is the only index; "
                            "move its links into names and summaries"))
        return
    if not KEBAB_RE.match(stem):
        errors.append((rel, f"'{stem}' is not kebab-case"))
    if DATE_PREFIX_RE.match(stem):
        warnings.append((rel, "date-prefixed name — leads with the occasion, "
                              "not the content; lead with the claim and keep "
                              "the date inside the file"))
    if stem.lower() in GENERIC_STEMS:
        warnings.append((rel, f"'{stem}' names a container, not the content — "
                              "state the claim or topic"))


def check_file(root: Path, rel: Path, errors: list, warnings: list,
               all_paths: set, by_basename: dict, check_links: bool) -> None:
    check_name(rel, is_dir=False, errors=errors, warnings=warnings)
    if not check_links or rel.suffix != ".md":
        return
    # Cross-reference check (opt-in). In trees that document a filesystem,
    # path-shaped tokens are often runtime paths, not docs links (a docs `session/`
    # dir and a runtime `session/` dir collide on the name). So this is advisory:
    # every miss is a warning to review, never a hard error. Path-qualified refs
    # (a/b.md) resolve root-relative or relative to the file's directory; bare
    # names (foo.md) resolve by basename anywhere in the tree.
    try:
        text = (root / rel).read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return
    refs: set[str] = set()
    for m in LINK_TICK_RE.finditer(text):
        refs.add(m.group(1))
    for m in LINK_MD_RE.finditer(text):
        refs.add(m.group(1))
    file_dir = rel.parent.as_posix()
    for ref in sorted(refs):
        if "/" in ref:
            candidates = {ref}
            if file_dir != ".":
                candidates.add(f"{file_dir}/{ref}")
            if not (candidates & all_paths):
                warnings.append((rel, f"unresolved path reference '{ref}' — "
                                      "not a docs file; fix the link if it was "
                                      "meant as one, else ignore (runtime path)"))
        elif ref not in by_basename:
            warnings.append((rel, f"unresolved reference '{ref}' — no docs "
                                  "file by that name (verify it is external)"))


def check_dir(root: Path, rel: Path, errors: list, warnings: list) -> None:
    check_name(rel, is_dir=True, errors=errors, warnings=warnings)
    entries = [p for p in (root / rel).iterdir()
               if not p.name.startswith(".")]
    if len(entries) == 0:
        errors.append((rel, "empty directory — the tree holds meaning, "
                            "not scaffolding"))
    elif len(entries) == 1:
        errors.append((rel, "single-child directory — fold the child back "
                            "into the parent level"))
    summary = root / rel.parent / (rel.name + ".md")
    if not summary.is_file():
        errors.append((rel, f"missing sibling summary '{rel}.md' — every "
                            "directory pairs with a one-screen summary file"))
    if len(rel.parts) >= MAX_DEPTH:
        warnings.append((rel, f"depth {len(rel.parts) + 1} content — levels "
                              "beyond 4 usually add a name without meaning"))


# ── Main ──────────────────────────────────────────────────────────────────────

def lint(root: Path, check_links: bool = False) -> tuple[list, list]:
    errors: list[tuple[Path, str]] = []
    warnings: list[tuple[Path, str]] = []

    # Index every file once for cross-reference resolution.
    all_paths: set[str] = set()             # posix rel paths of every file
    by_basename: dict[str, set[str]] = {}   # basename -> posix rel paths
    if check_links:
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if any(part.startswith(".") for part in path.relative_to(root).parts):
                continue
            relp = path.relative_to(root).as_posix()
            all_paths.add(relp)
            by_basename.setdefault(path.name, set()).add(relp)

    for path in sorted(root.rglob("*")):
        if any(part.startswith(".") for part in path.relative_to(root).parts):
            continue
        rel = path.relative_to(root)
        if path.is_dir():
            check_dir(root, rel, errors, warnings)
        else:
            check_file(root, rel, errors, warnings, all_paths, by_basename,
                       check_links)
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Lint a docs/ tree against the vfs-docs conventions.")
    parser.add_argument("docs_dir", help="Path to the docs tree root")
    parser.add_argument("--links", action="store_true",
                        help="Also check cross-references resolve to a docs "
                             "file (advisory warnings; noisy in trees that "
                             "document a runtime filesystem)")
    parser.add_argument("--json", action="store_true", dest="as_json",
                        help="Emit machine-readable JSON")
    args = parser.parse_args()

    root = Path(args.docs_dir)
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2

    errors, warnings = lint(root, check_links=args.links)

    if args.as_json:
        print(json.dumps({
            "errors": [{"path": str(p), "message": m} for p, m in errors],
            "warnings": [{"path": str(p), "message": m} for p, m in warnings],
            "summary": {"errors": len(errors), "warnings": len(warnings)},
        }, indent=2))
    else:
        for rel, msg in errors:
            print(f"ERROR  {rel} — {msg}")
        for rel, msg in warnings:
            print(f"WARN   {rel} — {msg}")
        status = "clean" if not errors and not warnings else \
            f"{len(errors)} errors, {len(warnings)} warnings"
        print(f"lint: {status}")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
