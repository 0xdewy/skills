#!/usr/bin/env python3
"""
context-infer.py — Auto-detect what to teach about from a directory.

Outputs JSON to stdout:
  topic          — human-readable project description
  hook_sentence  — the single most surprising/interesting fact
  interesting_facts — list of 3-5 noteworthy things
  entry_points   — key files to start exploring
  language       — dominant programming language
  readme_summary — first 400 chars of README if present
  git_activity   — recent commit summary if .git present
  file_count     — total source files found
  total_lines    — approximate total lines of code
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from collections import Counter


MANIFEST_FILES = {
    "package.json": "JavaScript/TypeScript (Node.js)",
    "Cargo.toml": "Rust",
    "go.mod": "Go",
    "pyproject.toml": "Python",
    "setup.py": "Python",
    "setup.cfg": "Python",
    "pom.xml": "Java (Maven)",
    "build.gradle": "Java/Kotlin (Gradle)",
    "build.gradle.kts": "Kotlin (Gradle)",
    "mix.exs": "Elixir",
    "composer.json": "PHP",
    "Gemfile": "Ruby",
    "pubspec.yaml": "Dart/Flutter",
    "Package.swift": "Swift",
    "*.csproj": "C#",
    "CMakeLists.txt": "C/C++",
    "Makefile": None,  # generic
}

LANG_EXTENSIONS = {
    ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
    ".jsx": "JavaScript", ".tsx": "TypeScript", ".go": "Go",
    ".rs": "Rust", ".java": "Java", ".kt": "Kotlin",
    ".rb": "Ruby", ".php": "PHP", ".cs": "C#",
    ".cpp": "C++", ".cc": "C++", ".c": "C", ".h": "C/C++",
    ".swift": "Swift", ".ex": "Elixir", ".exs": "Elixir",
    ".hs": "Haskell", ".ml": "OCaml", ".clj": "Clojure",
    ".scala": "Scala", ".lua": "Lua", ".r": "R",
    ".dart": "Dart", ".vue": "Vue", ".svelte": "Svelte",
    ".sol": "Solidity",
}

SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", ".pytest_cache",
    "dist", "build", "target", ".next", ".nuxt", "vendor",
    "venv", ".venv", "env", ".env", "coverage", ".nyc_output",
    "out", ".cache", "tmp", ".tmp", "public", "static",
}

ENTRY_POINT_NAMES = {
    "main.py", "main.go", "main.rs", "main.js", "main.ts",
    "index.js", "index.ts", "app.py", "app.js", "app.ts",
    "server.py", "server.go", "server.js", "server.ts",
    "cmd/main.go", "src/main.rs", "src/lib.rs",
    "src/main.py", "src/index.js", "src/index.ts",
}


def scan_directory(root: Path):
    files = []
    lang_lines: Counter = Counter()
    skip = SKIP_DIRS

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip and not d.startswith(".")]
        for fname in filenames:
            fpath = Path(dirpath) / fname
            ext = fpath.suffix.lower()
            if ext not in LANG_EXTENSIONS:
                continue
            try:
                text = fpath.read_text(errors="ignore")
                lines = text.count("\n") + 1
                lang_lines[LANG_EXTENSIONS[ext]] += lines
                rel = str(fpath.relative_to(root))
                files.append({"path": rel, "lines": lines, "lang": LANG_EXTENSIONS[ext]})
            except (OSError, PermissionError):
                pass

    return files, lang_lines


def read_manifest(root: Path):
    name = None
    description = None
    manifest_lang = None

    for fname, lang in MANIFEST_FILES.items():
        if "*" in fname:
            continue
        fpath = root / fname
        if not fpath.exists():
            continue
        manifest_lang = lang
        try:
            if fname == "package.json":
                data = json.loads(fpath.read_text(errors="ignore"))
                name = data.get("name")
                description = data.get("description")
            elif fname == "Cargo.toml":
                for line in fpath.read_text(errors="ignore").splitlines():
                    if line.startswith("name"):
                        name = line.split("=")[1].strip().strip('"')
                    if line.startswith("description"):
                        description = line.split("=")[1].strip().strip('"')
            elif fname == "go.mod":
                first_line = fpath.read_text(errors="ignore").splitlines()[0]
                name = first_line.replace("module", "").strip().split("/")[-1]
            elif fname == "pyproject.toml":
                for line in fpath.read_text(errors="ignore").splitlines():
                    if line.startswith("name"):
                        name = line.split("=")[1].strip().strip('"\'')
                    if line.startswith("description"):
                        description = line.split("=")[1].strip().strip('"\'')
        except Exception:
            pass
        break  # use first manifest found

    return name, description, manifest_lang


def read_readme(root: Path) -> str:
    for candidate in ["README.md", "README.rst", "README.txt", "README"]:
        fpath = root / candidate
        if fpath.exists():
            try:
                text = fpath.read_text(errors="ignore")
                # strip markdown headers/badges for cleaner summary
                lines = [l for l in text.splitlines() if l.strip() and not l.startswith("![")]
                return " ".join(" ".join(lines[:15]).split())[:500]
            except Exception:
                pass
    return ""


def read_git_activity(root: Path) -> str:
    git_dir = root / ".git"
    if not git_dir.exists():
        return ""
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "log", "--oneline", "-8"],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip()
    except Exception:
        return ""


def find_entry_points(files: list, root: Path) -> list:
    found = []
    for f in files:
        if Path(f["path"]).name in ENTRY_POINT_NAMES or f["path"] in ENTRY_POINT_NAMES:
            found.append(f["path"])
    # also look for files with "main" in name
    if not found:
        for f in files:
            if "main" in Path(f["path"]).stem.lower():
                found.append(f["path"])
    return found[:5]


def build_hook_sentence(name: str, lang: str, files: list, lang_lines: Counter, git: str) -> str:
    total_lines = sum(lang_lines.values())
    file_count = len(files)

    if file_count == 0:
        return "This directory appears empty — nothing to explore yet."

    if file_count == 1:
        return f"The entire {name or 'project'} fits in a single {files[0]['lines']}-line file."

    # find the largest file
    largest = max(files, key=lambda f: f["lines"])
    largest_pct = int(largest["lines"] / total_lines * 100) if total_lines else 0

    if largest_pct > 60:
        return (
            f"One file — {largest['path']} — contains {largest_pct}% of all the code. "
            f"Everything else is scaffolding around it."
        )

    # find the most central file (most imports — heuristic via name)
    if lang in ("Python", "JavaScript", "TypeScript"):
        hub_candidates = [f for f in files if "util" in f["path"].lower() or "core" in f["path"].lower() or "base" in f["path"].lower()]
        if hub_candidates:
            hub = hub_candidates[0]
            return f"The file {hub['path']} appears to be the hidden backbone — most things flow through it."

    # git-based hook
    if git:
        lines = git.strip().splitlines()
        if len(lines) >= 5:
            return (
                f"This project has {len(lines)}+ recent commits — it's actively evolving. "
                f"The latest: \"{lines[0].split(' ', 1)[-1]}\"."
            )

    # language diversity hook
    if len(lang_lines) > 2:
        langs = [f"{k} ({v:,} lines)" for k, v in lang_lines.most_common(3)]
        return f"This isn't a single-language project — it spans {', '.join(langs)}."

    # size-based hook
    if total_lines > 10_000:
        return (
            f"At {total_lines:,} lines across {file_count} files, this is a substantial system. "
            f"Most of the logic lives in {largest['path']}."
        )

    return f"This is a {total_lines:,}-line {lang} project with {file_count} source files."


def build_interesting_facts(name: str, lang: str, files: list, lang_lines: Counter, entry_points: list) -> list:
    facts = []
    total_lines = sum(lang_lines.values())

    # size fact
    facts.append(f"{total_lines:,} total lines of code across {len(files)} source files")

    # largest file
    if files:
        largest = max(files, key=lambda f: f["lines"])
        facts.append(f"Largest file: {largest['path']} ({largest['lines']:,} lines)")

    # entry points
    if entry_points:
        facts.append(f"Entry point{'s' if len(entry_points) > 1 else ''}: {', '.join(entry_points)}")

    # language breakdown
    if len(lang_lines) > 1:
        breakdown = ", ".join(f"{k} ({v:,} lines)" for k, v in lang_lines.most_common(3))
        facts.append(f"Language breakdown: {breakdown}")

    # test coverage signal
    test_files = [f for f in files if "test" in f["path"].lower() or "spec" in f["path"].lower()]
    if test_files:
        facts.append(f"{len(test_files)} test file{'s' if len(test_files) != 1 else ''} found")
    else:
        facts.append("No test files found — good thing to ask about!")

    return facts[:5]


def infer(root_str: str) -> dict:
    root = Path(root_str).resolve()
    files, lang_lines = scan_directory(root)
    proj_name, proj_desc, manifest_lang = read_manifest(root)
    readme = read_readme(root)
    git = read_git_activity(root)
    entry_points = find_entry_points(files, root)

    # dominant language
    if manifest_lang:
        lang = manifest_lang
    elif lang_lines:
        lang = lang_lines.most_common(1)[0][0]
    else:
        lang = "Unknown"

    # project name fallback
    if not proj_name:
        proj_name = root.name

    # build outputs
    topic = f"{proj_name} — a {lang} project"
    if proj_desc:
        topic = f"{proj_name}: {proj_desc}"

    hook = build_hook_sentence(proj_name, lang, files, lang_lines, git)
    facts = build_interesting_facts(proj_name, lang, files, lang_lines, entry_points)

    return {
        "topic": topic,
        "hook_sentence": hook,
        "interesting_facts": facts,
        "entry_points": entry_points,
        "language": lang,
        "readme_summary": readme,
        "git_activity": git,
        "file_count": len(files),
        "total_lines": sum(lang_lines.values()),
        "lang_breakdown": dict(lang_lines.most_common()),
        "files": [f["path"] for f in sorted(files, key=lambda x: -x["lines"])[:20]],
    }


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    result = infer(target)
    print(json.dumps(result, indent=2))
