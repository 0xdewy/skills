#!/usr/bin/env python3
"""
analyze_repo.py — map repo structure to JSON for agentify Phase 1.

Usage:
    python3 analyze_repo.py <project_dir>
    python3 analyze_repo.py <project_dir> --output /path/to/analysis.json

Outputs JSON to stdout (or --output file if specified).
Stdlib only — no third-party dependencies.
"""

import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path


# ── Constants ──────────────────────────────────────────────────────────────────

SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "env",
    "dist", "build", "target", ".next", ".nuxt", "coverage",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", ".tox",
    "vendor", ".cargo", "pkg", "out", ".turbo", ".swc",
    "htmlcov", ".eggs", "*.egg-info",
}

LANG_EXTENSIONS = {
    ".py": "Python", ".pyi": "Python",
    ".ts": "TypeScript", ".tsx": "TypeScript",
    ".js": "JavaScript", ".jsx": "JavaScript", ".mjs": "JavaScript",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java", ".kt": "Kotlin", ".kts": "Kotlin",
    ".rb": "Ruby",
    ".php": "PHP",
    ".swift": "Swift",
    ".c": "C", ".h": "C",
    ".cpp": "C++", ".cc": "C++", ".cxx": "C++", ".hpp": "C++",
    ".cs": "C#",
    ".ex": "Elixir", ".exs": "Elixir",
    ".hs": "Haskell",
    ".scala": "Scala",
    ".clj": "Clojure",
    ".sh": "Shell", ".bash": "Shell", ".zsh": "Shell",
    ".sql": "SQL",
    ".r": "R", ".R": "R",
    ".lua": "Lua",
    ".ml": "OCaml", ".mli": "OCaml",
    ".dart": "Dart",
    ".vue": "Vue",
    ".svelte": "Svelte",
    ".zig": "Zig",
    ".gleam": "Gleam",
    ".nix": "Nix",
    ".cue": "CUE",
    ".proto": "Protobuf",
    ".graphql": "GraphQL",
    ".prisma": "Prisma",
    ".md": "Markdown",
    ".json": "JSON",
    ".yaml": "YAML", ".yml": "YAML",
    ".toml": "TOML",
}

MANIFEST_FILES = [
    "package.json", "Cargo.toml", "go.mod", "pyproject.toml",
    "setup.py", "setup.cfg", "pom.xml", "build.gradle", "build.gradle.kts",
    "mix.exs", "Gemfile", "composer.json", "pubspec.yaml",
    "Project.toml", "stack.yaml", "cabal.project",
]

JUSTFILE_NAMES = {"justfile", "Justfile", ".justfile"}
TASKFILE_NAMES = {"Taskfile.yml", "Taskfile.yaml"}
ADDITIONAL_BUILD_SYSTEMS = {
    "deno.json": "deno",
    "deno.jsonc": "deno",
    "bun.lockb": "bun",
    "pnpm-lock.yaml": "pnpm",
    "yarn.lock": "yarn",
}

COMPONENT_SIGNALS = [
    "service", "handler", "controller", "model", "repository", "repo",
    "adapter", "gateway", "domain", "api", "cli", "cmd", "server",
    "client", "worker", "processor", "manager", "store", "cache",
    "auth", "user", "payment", "notification", "queue", "event",
    "middleware", "plugin", "module", "core", "engine", "driver",
    "routes", "route", "database", "db", "schema", "migrate",
    "component", "view", "page", "screen", "layout", "state",
    "hook", "provider", "context", "extension", "agent", "skill",
]

UTILITY_DIRS = {
    "util", "utils", "helper", "helpers", "common", "shared", "lib",
    "types", "interfaces", "constants", "config", "test", "tests",
    "spec", "specs", "__tests__", "fixtures", "mocks", "stubs",
    "assets", "static", "public", "resources", "data", "docs",
    "scripts", "tools", "bin", ".claude", "migrations",
}


# ── File scanning ──────────────────────────────────────────────────────────────

def should_skip_dir(name: str) -> bool:
    """Return True if a directory should be skipped during scanning."""
    return name in SKIP_DIRS or name.endswith(".egg-info") or name.startswith(".")


def count_lines(path: Path) -> int:
    """Count non-empty lines in a file. Returns 0 on read error."""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return sum(1 for line in f if line.strip())
    except (OSError, PermissionError):
        return 0


def scan_files(root: Path) -> tuple[list[dict], Counter]:
    """
    Walk the directory tree, collecting source file info.

    Returns:
        (files_list, lang_lines_counter)
        files_list: [{path (relative str), lines, lang}]
        lang_lines_counter: Counter mapping language → total lines
    """
    files = []
    lang_lines = Counter()

    for dirpath, dirnames, filenames in os.walk(root):
        # Skip unwanted directories in-place (modifies list Claude Code traverses)
        dirnames[:] = [d for d in dirnames if not should_skip_dir(d)]

        for filename in filenames:
            ext = Path(filename).suffix.lower()
            lang = LANG_EXTENSIONS.get(ext)
            if lang is None:
                continue

            full_path = Path(dirpath) / filename
            rel_path = str(full_path.relative_to(root))
            lines = count_lines(full_path)

            files.append({
                "path": rel_path,
                "lines": lines,
                "lang": lang,
            })
            lang_lines[lang] += lines

    return files, lang_lines


# ── Project type detection ──────────────────────────────────────────────────────

def detect_project_type(files: list[dict], root: Path) -> dict:
    """
    Detect project type from manifests and directory structure.

    Returns:
        {"project_type": str, "type_signals": [str]}

    Types: monorepo | webapp | service | library | cli | data_pipeline | unknown
    """
    signals = []

    # Check for monorepo indicators
    manifest_count = sum(
        1 for m in MANIFEST_FILES
        for f in files
        if Path(f["path"]).name == m and str(Path(f["path"]).parent) != "."
    )
    has_workspace = any([
        (root / "pnpm-workspace.yaml").exists(),
        (root / "nx.json").exists(),
        (root / "lerna.json").exists(),
        (root / "go.work").exists(),
    ])
    cargo_toml = root / "Cargo.toml"
    if cargo_toml.exists():
        try:
            content = cargo_toml.read_text(encoding="utf-8", errors="ignore")
            if "[workspace]" in content:
                has_workspace = True
        except OSError:
            pass

    if manifest_count > 2 or has_workspace:
        signals.append("multiple manifests or workspace config")
        return {"project_type": "monorepo", "type_signals": signals}

    top_dirs = {Path(f["path"]).parts[0] for f in files if len(Path(f["path"]).parts) > 1}

    # Check agent/skill (SKILL.md, agent configurations)
    skill_signals = {"SKILL.md", "AGENTS.md"}
    agent_config_signals = [".claude/agents/", ".claude/skills/", "SKILL.md"]
    if (set(f.name for f in root.iterdir() if f.is_file()) & skill_signals) or \
       any((root / d).exists() for d in agent_config_signals):
        has_build_system = any((root / m).exists() for m in MANIFEST_FILES)
        if not has_build_system:
            signals.append("SKILL.md or .claude/agents/ detected, no build system")
            return {"project_type": "agent-skill", "type_signals": signals}

    # Check mobile
    mobile_signals = {"ios", "android", "app.json", "eas.json", "capacitor.config.ts"}
    mobile_dirs = {"android", "ios", "app"}
    if (set(f.name for f in root.iterdir() if f.is_file()) & mobile_signals) or \
       (top_dirs & mobile_dirs):
        signals.append(f"mobile platform dirs or config: {mobile_signals}")
        return {"project_type": "mobile", "type_signals": signals}

    # Check Flutter (mobile sub-type)
    if (root / "pubspec.yaml").exists():
        try:
            content = (root / "pubspec.yaml").read_text(encoding="utf-8", errors="ignore")
            if "flutter" in content.lower()[:200]:
                signals.append("Flutter project (pubspec.yaml with flutter)")
                return {"project_type": "mobile", "type_signals": signals}
        except OSError:
            pass

    # Check plugin/extension
    plugin_signals = {
        "extension.js", "package.nls.json", ".vsixmanifest",
        "vsc-extension-quickstart.md",
    }
    plugin_dirs = {"src"}
    plugin_config_in_root = {
        ".vscodeignore", ".vsixmanifest",
    }
    if (set(f.name for f in root.iterdir() if f.is_file()) & plugin_signals):
        signals.append("VS Code extension artifacts detected")
        return {"project_type": "plugin", "type_signals": signals}
    # Check for extension.ts / extension.js as entry point
    for f in files:
        if Path(f["path"]).name in {"extension.ts", "extension.js"}:
            content_lower = ""
            try:
                content_lower = (root / f["path"]).read_text(encoding="utf-8", errors="ignore").lower()
            except OSError:
                pass
            if any(kw in content_lower for kw in ["activate", "deactivate", "extensioncontext", "vscode"]):
                signals.append(f"VS Code extension entry point: {f['path']}")
                return {"project_type": "plugin", "type_signals": signals}

    # Check webapp
    webapp_deps = ["react", "vue", "angular", "svelte", "next", "nuxt",
                   "gatsby", "@angular/core", "solid-js"]
    webapp_dirs = {"pages", "app", "components", "frontend", "ui", "src/pages",
                   "src/app", "src/components"}
    pkg_json = root / "package.json"
    if pkg_json.exists():
        try:
            pkg = json.loads(pkg_json.read_text(encoding="utf-8", errors="ignore"))
            all_deps = {
                **pkg.get("dependencies", {}),
                **pkg.get("devDependencies", {}),
            }
            if any(d in all_deps for d in webapp_deps):
                signals.append("webapp framework dependency")
                return {"project_type": "webapp", "type_signals": signals}
        except (json.JSONDecodeError, OSError):
            pass

    top_dirs = {Path(f["path"]).parts[0] for f in files if len(Path(f["path"]).parts) > 1}
    if top_dirs & webapp_dirs:
        signals.append(f"webapp dirs: {top_dirs & webapp_dirs}")
        return {"project_type": "webapp", "type_signals": signals}

    # Check CLI
    cli_signals = ["cmd", "commands", "cli"]
    if top_dirs & set(cli_signals):
        signals.append(f"CLI dirs: {top_dirs & set(cli_signals)}")
        return {"project_type": "cli", "type_signals": signals}

    # Check data pipeline
    pipeline_signals = {"dbt", "airflow", "prefect", "dagster", "luigi",
                        "pipelines", "transforms", "etl", "dags"}
    if top_dirs & pipeline_signals:
        signals.append(f"pipeline dirs: {top_dirs & pipeline_signals}")
        return {"project_type": "data_pipeline", "type_signals": signals}

    # Check library (no entry point or main server)
    has_lib = (root / "src").exists() or (root / "lib").exists()
    no_server_files = not any(
        Path(f["path"]).name in {"server.py", "server.ts", "server.js",
                                  "main.go", "app.py", "app.ts"}
        for f in files
    )
    if has_lib and no_server_files:
        signals.append("src/ or lib/ with no clear server entry point")
        return {"project_type": "library", "type_signals": signals}

    # Default: service
    signals.append("no monorepo/webapp/cli/pipeline/library signals detected")
    return {"project_type": "service", "type_signals": signals}


# ── Component detection ──────────────────────────────────────────────────────

def detect_components(files: list[dict], root: Path) -> list[dict]:
    """
    Identify directories that represent discrete components worth documenting.

    Returns:
        [{name, path, file_count, lines, dominant_lang, signals}]
    """
    # Aggregate stats per top-2-level directory
    dir_stats: dict[str, dict] = {}
    for f in files:
        parts = Path(f["path"]).parts
        if len(parts) < 2:
            continue

        # Use up to 2 levels deep (e.g., "src/api" rather than just "src")
        dir_key = str(Path(*parts[:2])) if len(parts) >= 2 else parts[0]

        if dir_key not in dir_stats:
            dir_stats[dir_key] = {"file_count": 0, "lines": 0, "langs": Counter()}
        dir_stats[dir_key]["file_count"] += 1
        dir_stats[dir_key]["lines"] += f["lines"]
        dir_stats[dir_key]["langs"][f["lang"]] += f["lines"]

    components = []
    for dir_path, stats in dir_stats.items():
        if stats["file_count"] < 3:
            continue  # Too small to be a component

        dir_name = Path(dir_path).name.lower()

        # Skip utility directories
        if dir_name in UTILITY_DIRS:
            continue

        # Check for component signals
        matched_signals = [s for s in COMPONENT_SIGNALS if s in dir_name]
        is_large = stats["lines"] >= 200

        if not matched_signals and not is_large:
            continue

        dominant_lang = stats["langs"].most_common(1)[0][0] if stats["langs"] else "unknown"
        components.append({
            "name": Path(dir_path).name,
            "path": dir_path,
            "file_count": stats["file_count"],
            "lines": stats["lines"],
            "dominant_lang": dominant_lang,
            "signals": matched_signals,
        })

    # Sort by line count descending (most significant components first)
    return sorted(components, key=lambda c: c["lines"], reverse=True)[:10]


# ── Existing docs ──────────────────────────────────────────────────────────────

def read_existing_docs(root: Path) -> list[dict]:
    """Find and describe existing documentation files."""
    docs = []

    # Standard top-level docs
    standard_docs = [
        "CLAUDE.md", "CLAUDE.local.md", "README.md", "CONTRIBUTING.md",
        ".claude/context-map.md", "AGENTS.md",
    ]
    for rel_path in standard_docs:
        full_path = root / rel_path
        docs.append({
            "path": rel_path,
            "exists": full_path.exists(),
            "line_count": count_lines(full_path) if full_path.exists() else 0,
            "has_frontmatter": _has_frontmatter(full_path) if full_path.exists() else False,
        })

    # docs/ directory
    docs_dir = root / "docs"
    if docs_dir.exists():
        for f in sorted(docs_dir.glob("*.md")):
            docs.append({
                "path": str(f.relative_to(root)),
                "exists": True,
                "line_count": count_lines(f),
                "has_frontmatter": _has_frontmatter(f),
            })

    # .claude/rules/
    rules_dir = root / ".claude" / "rules"
    if rules_dir.exists():
        for f in sorted(rules_dir.glob("*.md")):
            docs.append({
                "path": str(f.relative_to(root)),
                "exists": True,
                "line_count": count_lines(f),
                "has_frontmatter": _has_frontmatter(f),
            })

    return docs


PACKAGE_MANIFESTS = {"package.json", "Cargo.toml", "pyproject.toml", "go.mod", "build.gradle", "pom.xml"}

def detect_service_packages(root: Path, component_dirs: list[dict]) -> list[dict]:
    """
    Find all subdirectories (up to 2 levels deep) that have their own package
    manifest. Used for monorepo doc generation. Falls back to component_dirs
    if no sub-manifests found.
    """
    services = []
    seen = set()

    # Scan up to 2 levels deep for subdirs with their own manifest
    for depth1 in sorted(root.iterdir()):
        if not depth1.is_dir() or should_skip_dir(depth1.name):
            continue
        manifest1 = next((m for m in PACKAGE_MANIFESTS if (depth1 / m).exists()), None)
        if manifest1 and str(depth1.name) not in seen:
            seen.add(str(depth1.name))
            services.append({
                "name": depth1.name,
                "path": str(depth1.relative_to(root)),
                "manifest": manifest1,
            })
        # Check one level deeper (e.g. packages/api/)
        for depth2 in sorted(depth1.iterdir()):
            if not depth2.is_dir() or should_skip_dir(depth2.name):
                continue
            manifest2 = next((m for m in PACKAGE_MANIFESTS if (depth2 / m).exists()), None)
            if manifest2 and str(depth2.relative_to(root)) not in seen:
                seen.add(str(depth2.relative_to(root)))
                services.append({
                    "name": depth2.name,
                    "path": str(depth2.relative_to(root)),
                    "manifest": manifest2,
                })

    # Remove the root if the root itself has a manifest (monorepo root)
    # Only keep sub-packages, not the repo root itself
    services = [s for s in services if s["path"] != "."]
    return services


def detect_multiagent_signals(root: Path) -> bool:
    """Return True if this repo shows signals of multi-agent coordination."""
    signals = [
        (root / "AGENTS.md").exists(),
        (root / ".claude" / "agents").exists(),
        (root / "docs" / "plans").exists(),
        (root / "docs" / "specs").exists(),
    ]
    return any(signals)


def read_coordination_summary(root: Path) -> dict:
    """Detect docs/plans/, docs/specs/, docs/reviews/ and return a summary dict."""
    summary = {}
    docs_dir = root / "docs"
    for dir_name in ("plans", "specs", "reviews"):
        coord_path = docs_dir / dir_name
        if coord_path.exists() and coord_path.is_dir():
            all_md = list(coord_path.glob("*.md"))
            artifact_files = [f for f in all_md if f.name.lower() != "readme.md"]
            summary[dir_name] = {
                "exists": True,
                "file_count": len(artifact_files),
                "has_readme": (coord_path / "README.md").exists(),
            }
        else:
            summary[dir_name] = {"exists": False, "file_count": 0, "has_readme": False}
    return summary


def read_auto_memory(root: Path) -> dict:
    """
    Try to locate auto memory for this project.
    Claude Code stores auto memory at:
    ~/.claude/projects/<project>/memory/MEMORY.md
    """
    result = {"exists": False, "path": "", "line_count": 0, "has_memory": False}

    try:
        home = Path.home()
        memory_base = home / ".claude" / "projects"

        if not memory_base.exists():
            return result

        # Try to find the project dir. It's derived from the git repo path,
        # but we can scan for matching project names
        project_name = root.resolve().name

        for project_dir in memory_base.iterdir():
            if not project_dir.is_dir():
                continue
            memory_file = project_dir / "memory" / "MEMORY.md"
            if memory_file.exists():
                # Check if this is likely our project — the dir name often matches
                if project_name.lower() in project_dir.name.lower():
                    result["exists"] = True
                    result["path"] = str(memory_file)
                    result["line_count"] = count_lines(memory_file)
                    result["has_memory"] = True
                    break
                result["has_memory"] = True
    except (OSError, PermissionError):
        pass

    return result


def _has_frontmatter(path: Path) -> bool:
    """Return True if the file starts with '---' YAML frontmatter."""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.readline().strip() == "---"
    except OSError:
        return False


def read_existing_rules(root: Path) -> list[dict]:
    """Find .claude/rules/ files and extract their paths: globs."""
    rules = []
    rules_dir = root / ".claude" / "rules"
    if not rules_dir.exists():
        return rules

    for f in sorted(rules_dir.glob("*.md")):
        paths_globs = _extract_frontmatter_paths(f)
        rules.append({
            "path": str(f.relative_to(root)),
            "line_count": count_lines(f),
            "paths_globs": paths_globs,
        })

    return rules


def _extract_frontmatter_paths(path: Path) -> list[str]:
    """Extract the paths: list from YAML frontmatter."""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # Simple frontmatter extraction (no PyYAML needed)
        if not content.startswith("---"):
            return []

        end = content.find("---", 3)
        if end == -1:
            return []

        frontmatter = content[3:end]
        paths = []
        in_paths = False
        for line in frontmatter.splitlines():
            if line.strip().startswith("paths:"):
                in_paths = True
                continue
            if in_paths:
                if line.strip().startswith("- "):
                    paths.append(line.strip()[2:].strip().strip('"\''))
                elif line.strip() and not line.startswith(" ") and not line.startswith("\t"):
                    break
        return paths
    except OSError:
        return []


# ── Git history ──────────────────────────────────────────────────────────────

def read_git_history(root: Path) -> dict:
    """
    Return recent commit messages and the hottest directories.

    Hot dirs: directories with the most file changes in the last 90 days.
    """
    result = {"recent_commits": [], "hot_dirs": []}

    try:
        # Recent commits
        proc = subprocess.run(
            ["git", "log", "--oneline", "-20"],
            capture_output=True, text=True, cwd=str(root), timeout=10,
        )
        if proc.returncode == 0:
            result["recent_commits"] = proc.stdout.strip().splitlines()

        # Hot directories
        proc = subprocess.run(
            ["git", "log", "--name-only", "--format=", "--since=90.days", "-200"],
            capture_output=True, text=True, cwd=str(root), timeout=15,
        )
        if proc.returncode == 0:
            dir_counts: Counter = Counter()
            for line in proc.stdout.strip().splitlines():
                line = line.strip()
                if line and "/" in line:
                    top_dir = line.split("/")[0]
                    if not should_skip_dir(top_dir):
                        dir_counts[top_dir] += 1
            result["hot_dirs"] = [d for d, _ in dir_counts.most_common(5)]

    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    return result


# ── Key commands ──────────────────────────────────────────────────────────────

def read_key_commands(root: Path) -> dict:
    """
    Extract build/test/run/lint commands from common project manifests.

    Returns:
        {"build": str, "test": str, "run": str, "lint": str, "extra": [str]}
    """
    commands = {"build": "", "test": "", "run": "", "lint": "", "extra": []}

    # package.json scripts
    pkg_json = root / "package.json"
    if pkg_json.exists():
        try:
            pkg = json.loads(pkg_json.read_text(encoding="utf-8", errors="ignore"))
            scripts = pkg.get("scripts", {})
            commands["build"] = _first_match(scripts, ["build", "compile", "bundle"])
            commands["test"] = _first_match(scripts, ["test", "test:unit", "jest", "vitest"])
            commands["run"] = _first_match(scripts, ["start", "dev", "serve", "watch"])
            commands["lint"] = _first_match(scripts, ["lint", "check", "typecheck", "format"])
            # Prefix with "npm run"
            for key in ["build", "test", "run", "lint"]:
                if commands[key]:
                    commands[key] = f"npm run {commands[key]}"
        except (json.JSONDecodeError, OSError):
            pass
        return commands

    # Makefile targets
    makefile = root / "Makefile"
    if makefile.exists():
        try:
            content = makefile.read_text(encoding="utf-8", errors="ignore")
            targets = re.findall(r"^([a-z][a-z0-9_-]*)\s*:", content, re.MULTILINE)
            commands["build"] = f"make {_first_match_list(targets, ['build', 'compile', 'all'])}"
            commands["test"] = f"make {_first_match_list(targets, ['test', 'tests', 'check'])}"
            commands["run"] = f"make {_first_match_list(targets, ['run', 'serve', 'start', 'dev'])}"
            commands["lint"] = f"make {_first_match_list(targets, ['lint', 'fmt', 'format', 'vet'])}"
            for key in list(commands.keys()):
                if commands[key] == "make ":
                    commands[key] = ""
        except OSError:
            pass

    # justfile (growing Makefile alternative)
    for just_name in JUSTFILE_NAMES:
        justfile = root / just_name
        if justfile.exists():
            try:
                content = justfile.read_text(encoding="utf-8", errors="ignore")
                targets = re.findall(r"^([a-z][a-z0-9_-]*)\s*:", content, re.MULTILINE)
                # Remove the first line if it's a shebang or recipe
                targets = [t for t in targets if t not in ("set", "export", "alias")]
                if not commands["build"] or commands["build"] == "make ":
                    commands["build"] = f"just {_first_match_list(targets, ['build', 'compile', 'all'])}"
                commands["test"] = f"just {_first_match_list(targets, ['test', 'tests', 'check'])}" or commands["test"]
                commands["run"] = f"just {_first_match_list(targets, ['run', 'serve', 'start', 'dev'])}" or commands["run"]
                commands["lint"] = f"just {_first_match_list(targets, ['lint', 'fmt', 'format', 'vet'])}" or commands["lint"]
                for key in list(commands.keys()):
                    if commands[key] == "just ":
                        commands[key] = ""
            except OSError:
                pass
            break

    # Deno
    if (root / "deno.json").exists() or (root / "deno.jsonc").exists():
        commands["build"] = "deno compile"
        commands["test"] = "deno test"
        commands["run"] = "deno run main.ts"
        commands["lint"] = "deno lint && deno fmt --check"
        return commands

    # Go (go.work for monorepos too)
    if (root / "go.mod").exists() or (root / "go.work").exists():
        commands["build"] = "go build ./..."
        commands["test"] = "go test ./..."
        commands["run"] = "go run ."
        commands["lint"] = "go vet ./..."
        return commands

    # go.mod (Go)
    if (root / "go.mod").exists():
        commands["build"] = "go build ./..."
        commands["test"] = "go test ./..."
        commands["run"] = "go run ."
        commands["lint"] = "go vet ./..."
        return commands

    # pyproject.toml (Python)
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        try:
            content = pyproject.read_text(encoding="utf-8", errors="ignore")
            # taskipy
            if "[tool.taskipy.tasks]" in content:
                tasks = re.findall(r'^(\w+)\s*=', content, re.MULTILINE)
                commands["build"] = f"task {_first_match_list(tasks, ['build', 'compile'])}" if _first_match_list(tasks, ['build', 'compile']) else ""
                commands["test"] = f"task {_first_match_list(tasks, ['test'])}" if _first_match_list(tasks, ['test']) else "pytest"
                commands["lint"] = f"task {_first_match_list(tasks, ['lint', 'check', 'format'])}" if _first_match_list(tasks, ['lint', 'check', 'format']) else ""
            else:
                commands["test"] = "pytest"
                commands["lint"] = "ruff check . && mypy ."
        except OSError:
            commands["test"] = "pytest"

    return commands


def _first_match(d: dict, keys: list[str]) -> str:
    for k in keys:
        if k in d:
            return k
    return ""


def _first_match_list(items: list[str], targets: list[str]) -> str:
    for t in targets:
        if t in items:
            return t
    return ""


# ── Entry point ──────────────────────────────────────────────────────────────

def analyze(root: Path) -> dict:
    """Run full analysis and return the JSON-serializable result dict."""
    files, lang_lines = scan_files(root)
    total_lines = sum(lang_lines.values())
    file_count = len(files)

    # Size bucket
    if total_lines < 5_000:
        size_bucket = "small"
    elif total_lines < 50_000:
        size_bucket = "medium"
    else:
        size_bucket = "large"

    type_info = detect_project_type(files, root)
    components = detect_components(files, root)
    existing_docs = read_existing_docs(root)
    existing_rules = read_existing_rules(root)
    auto_memory = read_auto_memory(root)
    git_info = read_git_history(root)
    key_commands = read_key_commands(root)

    # Top-level directories
    top_dir_stats: dict[str, dict] = {}
    for f in files:
        parts = Path(f["path"]).parts
        if not parts:
            continue
        top = parts[0]
        if top not in top_dir_stats:
            top_dir_stats[top] = {"file_count": 0, "lines": 0, "langs": Counter()}
        top_dir_stats[top]["file_count"] += 1
        top_dir_stats[top]["lines"] += f["lines"]
        top_dir_stats[top]["langs"][f["lang"]] += f["lines"]

    top_dirs = [
        {
            "path": k,
            "file_count": v["file_count"],
            "lines": v["lines"],
            "dominant_lang": v["langs"].most_common(1)[0][0] if v["langs"] else "unknown",
        }
        for k, v in sorted(top_dir_stats.items(), key=lambda x: x[1]["lines"], reverse=True)
        if not should_skip_dir(k)
    ]

    # Entry points
    entry_signals = {
        "main.go", "main.py", "main.ts", "main.js",
        "index.ts", "index.js", "app.ts", "app.py", "app.js",
        "server.ts", "server.js", "server.py",
        "src/main.ts", "src/main.js", "src/index.ts", "src/app.ts",
    }
    entry_points = [f["path"] for f in files if f["path"] in entry_signals]

    # README summary — find description section, not just first 500 chars
    readme_summary = ""
    for readme_name in ["README.md", "readme.md", "README.rst"]:
        readme_path = root / readme_name
        if readme_path.exists():
            try:
                text = readme_path.read_text(encoding="utf-8", errors="ignore")
                # Find the first meaningful section (skip badges, logo links)
                lines = text.splitlines()
                description_lines = []
                in_first_section = False
                for line in lines:
                    stripped = line.strip()
                    # Skip badge images, CI status, empty lines before we start
                    if not in_first_section:
                        if stripped.startswith("![") or stripped.startswith("[!["):
                            continue
                        if stripped.startswith("# ") or stripped.startswith("## "):
                            in_first_section = True
                            continue
                        if stripped.startswith("<") or stripped.startswith("[") and "]" in stripped and "(" in stripped and stripped.count("[") <= 2:
                            continue
                        if not stripped:
                            continue
                        in_first_section = True
                    if stripped.startswith("## "):
                        break
                    if stripped:
                        description_lines.append(stripped)
                if description_lines:
                    readme_summary = " ".join(description_lines)[:500]
                else:
                    # Fallback to first 500 non-empty characters
                    clean = " ".join(text.split())[:500]
                    readme_summary = clean
            except OSError:
                pass
            break

    # Project name from manifest or directory name
    project_name = root.name
    for manifest in ["package.json", "Cargo.toml", "pyproject.toml"]:
        manifest_path = root / manifest
        if manifest_path.exists():
            try:
                content = manifest_path.read_text(encoding="utf-8", errors="ignore")
                if manifest == "package.json":
                    pkg = json.loads(content)
                    project_name = pkg.get("name", project_name)
                elif manifest == "Cargo.toml":
                    m = re.search(r'name\s*=\s*"([^"]+)"', content)
                    if m:
                        project_name = m.group(1)
                elif manifest == "pyproject.toml":
                    m = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
                    if m:
                        project_name = m.group(1)
            except (json.JSONDecodeError, OSError):
                pass
            break

    return {
        "project_name": project_name,
        "project_type": type_info["project_type"],
        "type_signals": type_info["type_signals"],
        "primary_language": lang_lines.most_common(1)[0][0] if lang_lines else "unknown",
        "lang_breakdown": dict(lang_lines.most_common(5)),
        "total_lines": total_lines,
        "file_count": file_count,
        "size_bucket": size_bucket,
        "top_dirs": top_dirs[:8],
        "entry_points": entry_points,
        "component_dirs": components,
        "existing_docs": existing_docs,
        "existing_rules": existing_rules,
        "auto_memory": auto_memory,
        "has_agents_md": (root / "AGENTS.md").exists(),
        "has_claude_local_md": (root / "CLAUDE.local.md").exists(),
        "readme_summary": readme_summary,
        "git_log_summary": git_info["recent_commits"],
        "hot_dirs": git_info["hot_dirs"],
        "key_commands": key_commands,
        "coordination_summary": read_coordination_summary(root),
        "has_multiagent_signals": detect_multiagent_signals(root),
        "service_packages": detect_service_packages(root, components),
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Analyze a repo structure and output JSON for agentify."
    )
    parser.add_argument("project_dir", help="Root directory of the project to analyze")
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

    result = analyze(root)
    output = json.dumps(result, indent=2)

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(output, encoding="utf-8")
    else:
        print(output)


if __name__ == "__main__":
    main()
