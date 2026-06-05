#!/usr/bin/env python3
"""
analyze.py — Gather structured facts about a codebase for the teach-me skill.

Outputs JSON to stdout:
  topic            — human-readable project description
  hook_sentence    — single most surprising/interesting fact
  interesting_facts — list of 3-5 noteworthy things
  entry_points     — key files to start exploring
  language         — dominant programming language
  readme_summary   — first 500 chars of README if present
  git_activity     — recent commit summary if .git present
  file_count       — total source files found
  total_lines      — approximate total lines of code
  lang_breakdown   — lines per language
  files            — top 20 files by lines of code
  largest_file     — {path, lines, pct_of_total}
  module_structure — top directories grouped with file count, lines, dominant lang
  has_tests        — whether any test/spec files exist
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from collections import Counter, defaultdict


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
    "Makefile": None,
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
        break

    return name, description, manifest_lang


def read_readme(root: Path) -> str:
    for candidate in ["README.md", "README.rst", "README.txt", "README"]:
        fpath = root / candidate
        if fpath.exists():
            try:
                text = fpath.read_text(errors="ignore")
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

    largest = max(files, key=lambda f: f["lines"])
    largest_pct = int(largest["lines"] / total_lines * 100) if total_lines else 0

    if largest_pct > 60:
        return (
            f"One file — {largest['path']} — contains {largest_pct}% of all the code. "
            f"Everything else is scaffolding around it."
        )

    if lang in ("Python", "JavaScript", "TypeScript"):
        hub_candidates = [f for f in files if "util" in f["path"].lower() or "core" in f["path"].lower() or "base" in f["path"].lower()]
        if hub_candidates:
            hub = hub_candidates[0]
            return f"The file {hub['path']} appears to be the hidden backbone — most things flow through it."

    if git:
        lines = git.strip().splitlines()
        if len(lines) >= 5:
            return (
                f"This project has {len(lines)}+ recent commits — it's actively evolving. "
                f"The latest: \"{lines[0].split(' ', 1)[-1]}\"."
            )

    if len(lang_lines) > 2:
        langs = [f"{k} ({v:,} lines)" for k, v in lang_lines.most_common(3)]
        return f"This isn't a single-language project — it spans {', '.join(langs)}."

    if total_lines > 10_000:
        return (
            f"At {total_lines:,} lines across {file_count} files, this is a substantial system. "
            f"Most of the logic lives in {largest['path']}."
        )

    return f"This is a {total_lines:,}-line {lang} project with {file_count} source files."


def build_interesting_facts(name: str, lang: str, files: list, lang_lines: Counter, entry_points: list) -> list:
    facts = []
    total_lines = sum(lang_lines.values())

    facts.append(f"{total_lines:,} total lines of code across {len(files)} source files")

    if files:
        largest = max(files, key=lambda f: f["lines"])
        facts.append(f"Largest file: {largest['path']} ({largest['lines']:,} lines)")

    if entry_points:
        facts.append(f"Entry point{'s' if len(entry_points) > 1 else ''}: {', '.join(entry_points)}")

    if len(lang_lines) > 1:
        breakdown = ", ".join(f"{k} ({v:,} lines)" for k, v in lang_lines.most_common(3))
        facts.append(f"Language breakdown: {breakdown}")

    test_files = [f for f in files if "test" in f["path"].lower() or "spec" in f["path"].lower()]
    if test_files:
        facts.append(f"{len(test_files)} test file{'s' if len(test_files) != 1 else ''} found")
    else:
        facts.append("No test files found — good thing to ask about!")

    return facts[:5]


def build_module_structure(files: list, lang_lines: Counter) -> list:
    dir_map: dict = defaultdict(lambda: {"file_count": 0, "total_lines": 0, "langs": Counter()})
    for f in files:
        parent = str(Path(f["path"]).parent)
        dir_map[parent]["file_count"] += 1
        dir_map[parent]["total_lines"] += f["lines"]
        dir_map[parent]["langs"][f["lang"]] += 1

    result = []
    for dir_path, info in sorted(dir_map.items(), key=lambda x: -x[1]["total_lines"])[:10]:
        dominant = info["langs"].most_common(1)[0][0] if info["langs"] else "Unknown"
        label = dir_path if dir_path == "." else dir_path + "/"
        result.append({
            "dir": label,
            "file_count": info["file_count"],
            "total_lines": info["total_lines"],
            "dominant_lang": dominant,
        })
    return result


def detect_project_type(files: list, root: Path, readme: str) -> dict:
    paths = [f["path"] for f in files]
    path_set = set(paths)
    readme_lower = readme.lower()

    web_signals: list = []
    web_names = {"app.py", "app.js", "app.ts", "server.py", "server.go", "server.js", "server.ts",
                 "routes.py", "routes.js", "routes.ts", "views.py", "views.js"}
    for p in paths:
        if Path(p).name in web_names:
            web_signals.append(Path(p).name)
        if any(kw in p.lower() for kw in ["routes/", "views/", "controllers/", "handlers/"]):
            web_signals.append(p.split("/")[0] + "/")
    for fw in ["flask", "django", "express", "fastapi", "rails", "spring", "gin", "echo",
               "fiber", "actix", "axum", "phoenix", "laravel", "hono", "nestjs"]:
        if fw in readme_lower:
            web_signals.append(f"{fw} in README")
    pkg_json = root / "package.json"
    if pkg_json.exists():
        try:
            data = json.loads(pkg_json.read_text(errors="ignore"))
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
            for fw in ["express", "koa", "fastify", "hapi", "next", "nuxt", "gatsby", "hono", "@nestjs/core"]:
                if fw in deps:
                    web_signals.append(f"{fw} in package.json")
        except Exception:
            pass

    cli_signals: list = []
    cli_names = {"cli.py", "cli.js", "cli.ts", "cli.go"}
    for p in paths:
        if Path(p).name in cli_names:
            cli_signals.append(Path(p).name)
    top_dirs = {Path(p).parts[0] for p in paths if Path(p).parts}
    if "cmd" in top_dirs:
        cli_signals.append("cmd/ directory")
    if "commands" in top_dirs:
        cli_signals.append("commands/ directory")
    cargo = root / "Cargo.toml"
    if cargo.exists():
        try:
            if "[[bin]]" in cargo.read_text(errors="ignore"):
                cli_signals.append("[[bin]] in Cargo.toml")
        except Exception:
            pass
    cli_keywords = ["import click", "from click import", "import argparse", "cobra.Command",
                    "urfave/cli", "spf13/cobra", "clap::Parser", "clap::Command"]
    for f in files[:40]:
        try:
            content = (root / f["path"]).read_text(errors="ignore")
            for kw in cli_keywords:
                if kw in content:
                    cli_signals.append(kw.split()[1] if " " in kw else kw)
                    break
        except Exception:
            pass

    lib_signals: list = []
    if "src/lib.rs" in path_set:
        lib_signals.append("src/lib.rs present")
    root_inits = [p for p in paths if Path(p).parent == Path(".") and Path(p).name == "__init__.py"]
    if root_inits and not any(Path(p).stem == "main" for p in paths):
        lib_signals.append("root __init__.py, no main.*")
    for kw in ["library", "sdk", "package", "module", "framework"]:
        if kw in readme_lower[:300]:
            lib_signals.append(f"'{kw}' in README")
            break

    data_signals: list = []
    data_dirs = {"pipeline", "etl", "transform", "ingest", "extract", "dags", "flows", "tasks"}
    for d in top_dirs:
        if d.lower() in data_dirs:
            data_signals.append(f"{d}/ directory")
    data_keywords = ["import pandas", "import spark", "from pyspark", "import dbt",
                     "from airflow", "import luigi", "import prefect", "import dagster"]
    for f in files[:40]:
        try:
            content = (root / f["path"]).read_text(errors="ignore")
            for kw in data_keywords:
                if kw in content:
                    data_signals.append(kw.split()[-1] + " usage")
                    break
        except Exception:
            pass

    scores = {
        "web_app": len(set(web_signals)),
        "cli_tool": len(set(cli_signals)),
        "library": len(set(lib_signals)),
        "data_pipeline": len(set(data_signals)),
    }
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return {"project_type": "unknown", "type_signals": []}
    signals_map = {
        "web_app": web_signals,
        "cli_tool": cli_signals,
        "library": lib_signals,
        "data_pipeline": data_signals,
    }
    return {
        "project_type": best,
        "type_signals": list(dict.fromkeys(signals_map[best]))[:5],
    }


def build_teaching_path(files: list, entry_points: list) -> list:
    if not files:
        return []

    def classify(f):
        p = f["path"].lower()
        lines = f["lines"]
        if any(kw in p for kw in ["util", "helper", "common", "shared", "constant", "type", "error", "exception"]):
            return "L1", "utility/helper leaf"
        if "test" in p or "spec" in p or "mock" in p or "fixture" in p:
            return "L1", "test file"
        if lines < 80:
            return "L1", f"small file ({lines} lines)"
        if any(kw in p for kw in ["model", "schema", "entity", "dto", "struct", "domain"]):
            return "L1", "data model"
        if any(kw in p for kw in ["db", "database", "cache", "redis", "http", "client",
                                   "adapter", "repository", "store", "queue", "broker"]):
            return "L2", "integration/adapter"
        if any(kw in p for kw in ["service", "handler", "controller", "middleware",
                                   "route", "api", "cmd", "command"]):
            return "L2", "service/handler layer"
        if lines > 300:
            return "L3", f"large cross-cutting file ({lines} lines)"
        return "L2", "core logic"

    result = []
    seen: set = set()

    for ep in entry_points:
        for f in files:
            if f["path"] == ep and ep not in seen:
                complexity, reason = classify(f)
                result.append({"path": f["path"], "complexity": complexity,
                                "reason": f"entry point — {reason}"})
                seen.add(ep)

    for f in sorted(files, key=lambda x: x["lines"]):
        if f["path"] in seen:
            continue
        p = f["path"].lower()
        if any(kw in p for kw in ["util", "helper", "common", "shared", "constant", "type", "error"]):
            complexity, reason = classify(f)
            result.append({"path": f["path"], "complexity": complexity, "reason": reason})
            seen.add(f["path"])

    for f in sorted(files, key=lambda x: x["lines"]):
        if f["path"] in seen:
            continue
        p = f["path"].lower()
        if any(kw in p for kw in ["model", "schema", "entity", "dto", "struct", "domain"]):
            complexity, reason = classify(f)
            result.append({"path": f["path"], "complexity": complexity, "reason": reason})
            seen.add(f["path"])

    for f in sorted(files, key=lambda x: -x["lines"]):
        if f["path"] in seen:
            continue
        p = f["path"].lower()
        if "test" in p or "spec" in p or "mock" in p:
            continue
        if any(kw in p for kw in ["db", "database", "cache", "redis", "http", "client",
                                   "adapter", "repository", "store"]):
            continue
        complexity, reason = classify(f)
        result.append({"path": f["path"], "complexity": complexity, "reason": reason})
        seen.add(f["path"])

    for f in sorted(files, key=lambda x: x["lines"]):
        if f["path"] in seen:
            continue
        p = f["path"].lower()
        if any(kw in p for kw in ["db", "database", "cache", "redis", "http", "client",
                                   "adapter", "repository", "store"]):
            complexity, reason = classify(f)
            result.append({"path": f["path"], "complexity": complexity, "reason": reason})
            seen.add(f["path"])

    for f in sorted(files, key=lambda x: x["lines"]):
        if f["path"] not in seen:
            complexity, reason = classify(f)
            result.append({"path": f["path"], "complexity": complexity, "reason": reason})
            seen.add(f["path"])

    return result


def build_adaptive_threads(files: list, project_type: str, has_tests: bool) -> list:
    threads = []

    def match_files(keywords):
        return [f["path"] for f in files
                if any(kw in f["path"].lower() for kw in keywords)][:3]

    if project_type == "web_app":
        route_files = match_files(["route", "router", "handler", "controller", "view", "endpoint"])
        threads.append({
            "label": "routing layer",
            "description": "how an HTTP request finds its handler and what middleware runs before it",
            "key_files": route_files or ["routes.*"],
        })
        auth_files = match_files(["auth", "session", "token", "jwt", "login", "permission", "guard"])
        if auth_files:
            threads.append({
                "label": "auth flow",
                "description": "how identity is established, where it is checked, and what happens when it is wrong",
                "key_files": auth_files,
            })
        db_files = match_files(["model", "db", "database", "repository", "store", "migration", "schema"])
        if db_files:
            threads.append({
                "label": "persistence layer",
                "description": "how domain objects become database rows and back, and where the N+1 hides",
                "key_files": db_files,
            })
        mw_files = match_files(["middleware", "error", "exception", "hook"])
        if mw_files:
            threads.append({
                "label": "error and middleware chain",
                "description": "how errors propagate from handler to client and what middleware intercepts them",
                "key_files": mw_files,
            })
        if has_tests:
            threads.append({
                "label": "test structure",
                "description": "what is tested, what is not, and what the gaps reveal about design priorities",
                "key_files": match_files(["test", "spec"]),
            })

    elif project_type == "cli_tool":
        cmd_files = match_files(["cmd", "command", "cli", "arg", "flag", "main"])
        threads.append({
            "label": "command parsing and dispatch",
            "description": "how the user's invocation is parsed, validated, and routed to the right handler",
            "key_files": cmd_files or ["main.*", "cli.*"],
        })
        cfg_files = match_files(["config", "setting", "option", "env", "conf"])
        threads.append({
            "label": "configuration loading",
            "description": "how flags, environment variables, and config files are merged into a single runtime config",
            "key_files": cfg_files or ["config.*"],
        })
        out_files = match_files(["output", "format", "render", "print", "display", "ui", "tui"])
        threads.append({
            "label": "output formatting",
            "description": "how results are formatted for stdout/stderr and how exit codes signal success or failure",
            "key_files": out_files or ["output.*"],
        })
        err_files = match_files(["error", "err", "exception"])
        if err_files:
            threads.append({
                "label": "error and exit-code handling",
                "description": "how errors are caught, reported to the user, and mapped to exit codes",
                "key_files": err_files,
            })

    elif project_type == "library":
        pub_files = match_files(["__init__", "lib", "api", "public", "interface", "mod"])
        threads.append({
            "label": "public API surface",
            "description": "what the library exposes to callers, how the public interface is designed, and what it hides",
            "key_files": pub_files or ["lib.*", "__init__.py"],
        })
        int_files = match_files(["util", "helper", "internal", "private", "impl"])
        threads.append({
            "label": "internal utilities",
            "description": "the building blocks the public API is assembled from, and why they are not exposed",
            "key_files": int_files or ["utils.*"],
        })
        err_files = match_files(["error", "err", "exception", "result"])
        threads.append({
            "label": "error types and propagation",
            "description": "how errors are typed, propagated through the call stack, and surfaced to the caller",
            "key_files": err_files or ["errors.*"],
        })
        if has_tests:
            threads.append({
                "label": "test patterns",
                "description": "how the library tests its own contracts and what the tests reveal about intended usage",
                "key_files": match_files(["test", "spec"]),
            })

    elif project_type == "data_pipeline":
        threads.append({
            "label": "ingestion / source connectors",
            "description": "how raw data enters the pipeline, what sources are supported, and how schema mismatches are handled",
            "key_files": match_files(["extract", "ingest", "source", "reader", "fetch", "connector", "input"]) or ["extract.*"],
        })
        threads.append({
            "label": "transformation logic",
            "description": "how data is reshaped, validated, and enriched between ingestion and output",
            "key_files": match_files(["transform", "process", "map", "filter", "enrich", "clean", "normalize"]) or ["transform.*"],
        })
        threads.append({
            "label": "output / sink connectors",
            "description": "where processed data lands, how idempotency is guaranteed, and how partial writes are handled",
            "key_files": match_files(["load", "sink", "output", "writer", "export", "publish"]) or ["load.*"],
        })
        sched_files = match_files(["schedule", "dag", "flow", "retry", "backfill", "orchestrat"])
        if sched_files:
            threads.append({
                "label": "scheduling and retry logic",
                "description": "how pipeline runs are triggered, retried on failure, and backfilled after outages",
                "key_files": sched_files,
            })

    else:  # unknown
        non_test = [f for f in files if "test" not in f["path"].lower() and "spec" not in f["path"].lower()]
        if non_test:
            largest = max(non_test, key=lambda x: x["lines"])
            threads.append({
                "label": f"{Path(largest['path']).stem} in depth",
                "description": "the largest module — where most of the logic lives",
                "key_files": [largest["path"]],
            })
        entry_files = match_files(["main", "app", "index", "server", "cli"])
        if entry_files:
            threads.append({
                "label": "entry point flow",
                "description": "how execution begins, what is initialized, and how it reaches the core logic",
                "key_files": entry_files,
            })
        if has_tests:
            threads.append({
                "label": "test structure",
                "description": "what is tested, what is not, and what the gaps reveal about design priorities",
                "key_files": match_files(["test", "spec"]),
            })
        else:
            threads.append({
                "label": "missing test coverage",
                "description": "there are no tests — which behaviors would be most valuable to test first, and why",
                "key_files": [],
            })

    return threads


def infer(root_str: str) -> dict:
    root = Path(root_str).resolve()
    files, lang_lines = scan_directory(root)
    proj_name, proj_desc, manifest_lang = read_manifest(root)
    readme = read_readme(root)
    git = read_git_activity(root)
    entry_points = find_entry_points(files, root)

    if manifest_lang:
        lang = manifest_lang
    elif lang_lines:
        lang = lang_lines.most_common(1)[0][0]
    else:
        lang = "Unknown"

    if not proj_name:
        proj_name = root.name

    topic = f"{proj_name} — a {lang} project"
    if proj_desc:
        topic = f"{proj_name}: {proj_desc}"

    hook = build_hook_sentence(proj_name, lang, files, lang_lines, git)
    facts = build_interesting_facts(proj_name, lang, files, lang_lines, entry_points)

    total_lines = sum(lang_lines.values())

    sorted_files = sorted(files, key=lambda x: -x["lines"])
    largest_file = None
    if sorted_files:
        lf = sorted_files[0]
        pct = int(lf["lines"] / total_lines * 100) if total_lines else 0
        largest_file = {"path": lf["path"], "lines": lf["lines"], "pct_of_total": pct}

    has_tests = any(
        "test" in f["path"].lower() or "spec" in f["path"].lower()
        for f in files
    )

    module_structure = build_module_structure(files, lang_lines)
    project_type_info = detect_project_type(files, root, readme)
    teaching_path = build_teaching_path(files, entry_points)
    adaptive_threads = build_adaptive_threads(files, project_type_info["project_type"], has_tests)

    return {
        "topic": topic,
        "hook_sentence": hook,
        "interesting_facts": facts,
        "entry_points": entry_points,
        "language": lang,
        "readme_summary": readme,
        "git_activity": git,
        "file_count": len(files),
        "total_lines": total_lines,
        "lang_breakdown": dict(lang_lines.most_common()),
        "files": [f["path"] for f in sorted_files[:20]],
        "largest_file": largest_file,
        "module_structure": module_structure,
        "has_tests": has_tests,
        "project_type": project_type_info["project_type"],
        "type_signals": project_type_info["type_signals"],
        "teaching_path": teaching_path,
        "adaptive_threads": adaptive_threads,
    }


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    result = infer(target)
    print(json.dumps(result, indent=2))
