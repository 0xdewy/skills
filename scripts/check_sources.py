#!/usr/bin/env python3
"""Parse repository Python, shell, and eval JSON without creating caches."""

from __future__ import annotations

import ast
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IGNORED_PARTS = {".git", ".venv", ".pytest_cache", "__pycache__"}


def included(path: Path) -> bool:
    return not any(part in IGNORED_PARTS or part.startswith(".retired-") for part in path.parts)


def main() -> int:
    python_files = [
        path
        for base in (ROOT / "skills", ROOT / "scripts", ROOT / "tests")
        for path in base.rglob("*.py")
        if included(path.relative_to(ROOT))
    ]
    for path in python_files:
        ast.parse(path.read_text(), filename=str(path.relative_to(ROOT)))

    json_files = list((ROOT / "skills").glob("*/evals/evals.json"))
    for path in json_files:
        json.loads(path.read_text())

    shell_files = [
        path for path in ROOT.rglob("*.sh") if included(path.relative_to(ROOT))
    ]
    for path in shell_files:
        subprocess.run(["bash", "-n", str(path)], check=True)

    print(
        f"OK: parsed {len(python_files)} Python, {len(json_files)} JSON, "
        f"and {len(shell_files)} shell files"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
