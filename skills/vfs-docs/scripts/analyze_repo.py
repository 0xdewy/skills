#!/usr/bin/env python3
"""
analyze_repo.py — the facts a docs tree design needs, as JSON.

Usage:
    python3 analyze_repo.py <project_dir> [--output FILE]

Reports:
    site_generators  docs tooling whose index files and nav config are
                     load-bearing; a docs/ that feeds one is not restructured
    areas            code directories by size, which the tree's top level
                     should mirror
    docs             every existing doc with its headings: what must be
                     preserved, and where a multi-topic file can split

Stdlib only — no third-party dependencies.
"""

import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", "target"}
LOCKFILES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "Cargo.lock",
    "poetry.lock", "uv.lock", "go.sum",
}
DOC_EXTS = {".md", ".mdx", ".rst", ".adoc"}
SITE_FILES = {
    "mkdocs.yml": "MkDocs", "mkdocs.yaml": "MkDocs",
    "docusaurus.config.js": "Docusaurus", "docusaurus.config.ts": "Docusaurus",
    "docusaurus.config.mjs": "Docusaurus",
    "book.toml": "mdBook", "antora.yml": "Antora", "hugo.toml": "Hugo",
    "_config.yml": "Jekyll or GitHub Pages",
    ".readthedocs.yaml": "Read the Docs", ".readthedocs.yml": "Read the Docs",
}
SITE_DIRS = {".vitepress": "VitePress", ".vuepress": "VuePress"}
MAX_AREAS, MAX_DOCS, MAX_HEADINGS = 15, 200, 40


def list_files(root: Path) -> list[Path]:
    """Tracked and untracked-but-not-ignored files; a plain walk outside git."""
    cmd = ["git", "-C", str(root), "ls-files", "-z", "--cached", "--others", "--exclude-standard"]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
        return [Path(p) for p in out.split("\0") if p and (root / p).is_file()]
    except (OSError, subprocess.CalledProcessError):
        rel = (p.relative_to(root) for p in root.rglob("*") if p.is_file())
        return [p for p in rel if not SKIP_DIRS.intersection(p.parts)]


def read_text(path: Path) -> str:
    """File content, or "" for binary and unreadable files."""
    try:
        data = path.read_bytes()
    except OSError:
        return ""
    return "" if b"\0" in data[:1024] else data.decode("utf-8", errors="ignore")


def site_generators(files: list[Path]) -> list[dict]:
    found = []
    for p in files:
        name = SITE_FILES.get(p.name)
        if p.name == "conf.py" and {"docs", "doc"} & set(p.parts):
            name = "Sphinx"
        for part in p.parts[:-1]:
            name = name or SITE_DIRS.get(part)
        if name and name not in [f["name"] for f in found]:
            found.append({"name": name, "marker": str(p)})
    return found


def areas(root: Path, files: list[Path]) -> list[dict]:
    """Code size per directory, two levels deep (src/api, not just src)."""
    stats: dict[str, dict] = {}
    for p in files:
        if len(p.parts) < 2 or p.suffix in DOC_EXTS or p.name in LOCKFILES:
            continue
        s = stats.setdefault(str(Path(*p.parts[:-1][:2])), {"files": 0, "lines": 0, "exts": Counter()})
        lines = read_text(root / p).count("\n")
        s["files"] += 1
        s["lines"] += lines
        s["exts"][p.suffix or p.name] += lines
    ranked = sorted(stats.items(), key=lambda kv: -kv[1]["lines"])[:MAX_AREAS]
    return [
        {"path": k, "files": v["files"], "lines": v["lines"], "top_ext": v["exts"].most_common(1)[0][0]}
        for k, v in ranked
    ]


def headings(text: str) -> list[str]:
    """Markdown headings to level 3, ignoring fenced code."""
    found, fenced = [], False
    for line in text.splitlines():
        if line.lstrip().startswith(("```", "~~~")):
            fenced = not fenced
        elif not fenced and line.startswith(("# ", "## ", "### ")):
            found.append(line.strip())
    return found[:MAX_HEADINGS]


def docs(root: Path, files: list[Path]) -> list[dict]:
    """Existing docs, docs/ first, then the repo root, then everything else."""
    found = sorted(
        (p for p in files if p.suffix in DOC_EXTS),
        key=lambda p: (p.parts[0] != "docs", len(p.parts) > 1, str(p)),
    )
    out = []
    for p in found:
        text = read_text(root / p)
        out.append({"path": str(p), "lines": text.count("\n"), "headings": headings(text)})
    return out


def analyze(root: Path) -> dict:
    files = list_files(root)
    all_docs = docs(root, files)
    return {
        "site_generators": site_generators(files),
        "areas": areas(root, files),
        "docs": all_docs[:MAX_DOCS],
        "docs_omitted": max(0, len(all_docs) - MAX_DOCS),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Repo facts for vfs-docs tree design, as JSON.")
    parser.add_argument("project_dir")
    parser.add_argument("--output", "-o", help="write JSON here instead of stdout")
    args = parser.parse_args()

    root = Path(args.project_dir).resolve()
    if not root.is_dir():
        sys.exit(f"Error: {root} is not a directory")

    output = json.dumps(analyze(root), indent=2)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(output, encoding="utf-8")
    else:
        print(output)


if __name__ == "__main__":
    main()
