#!/usr/bin/env python3
"""Describe the changed files and both sides of each hunk in a merge-base diff."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], capture_output=True, text=True, stdin=subprocess.DEVNULL
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def resolve_base(explicit: str | None) -> str:
    if explicit:
        return explicit
    if os.environ.get("PR_BASE_SHA"):
        return os.environ["PR_BASE_SHA"]

    candidates = []
    try:
        origin_head = git("symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD")
        if origin_head:
            candidates.append(origin_head)
    except RuntimeError:
        pass
    candidates.extend(["origin/main", "main", "origin/master", "master"])
    for candidate in candidates:
        try:
            git("rev-parse", "--verify", f"{candidate}^{{commit}}")
            return candidate
        except RuntimeError:
            continue
    raise RuntimeError("could not infer a base ref; pass --base <ref-or-sha>")


def parse_name_status(text: str) -> list[dict]:
    files = []
    fields = text.split("\0")
    index = 0
    while index < len(fields):
        status = fields[index]
        index += 1
        if not status or index >= len(fields):
            continue
        if status.startswith(("R", "C")) and index + 1 < len(fields):
            old_path, path = fields[index], fields[index + 1]
            index += 2
            files.append({"path": path, "old_path": old_path, "status": status})
        else:
            files.append({"path": fields[index], "status": status})
            index += 1
    return files


def parse_numstat(text: str) -> dict[str, dict[str, int | None]]:
    stats = {}
    fields = text.split("\0")
    index = 0
    while index < len(fields):
        parts = fields[index].split("\t")
        if len(parts) < 3:
            index += 1
            continue
        added, deleted, path = parts[0], parts[1], parts[2]
        if not path and index + 2 < len(fields):
            path = fields[index + 2]
            index += 3
        else:
            index += 1
        stats[path] = {
            "additions": int(added) if added.isdigit() else None,
            "deletions": int(deleted) if deleted.isdigit() else None,
        }
    return stats


def _count(value: str | None) -> int:
    return 1 if value is None else int(value)


def git_unquote(token: str) -> str:
    """Decode a Git C-quoted path token, including its surrounding quotes."""
    if len(token) < 2 or not token.startswith('"') or not token.endswith('"'):
        return token
    body = token[1:-1]
    out = bytearray()
    index = 0
    simple = {"a": 7, "b": 8, "t": 9, "n": 10, "v": 11, "f": 12, "r": 13, "\\": 92, '"': 34}
    while index < len(body):
        char = body[index]
        if char != "\\":
            out += char.encode("utf-8")
            index += 1
            continue
        index += 1
        if index >= len(body):
            break
        esc = body[index]
        if esc in simple:
            out.append(simple[esc])
            index += 1
            continue
        if "0" <= esc <= "7":
            digits = esc
            index += 1
            while index < len(body) and len(digits) < 3 and "0" <= body[index] <= "7":
                digits += body[index]
                index += 1
            out.append(int(digits, 8))
            continue
        out += esc.encode("utf-8")
        index += 1
    return out.decode("utf-8", "surrogateescape")


def header_path(line: str) -> str | None:
    """Return the repo path from a --- or +++ header. /dev/null has no path."""
    body = line[4:]
    if body.startswith('"'):
        end = 1
        while end < len(body):
            if body[end] == "\\":
                end += 2
                continue
            if body[end] == '"':
                end += 1
                break
            end += 1
        body = git_unquote(body[:end])
    else:
        body = body.split("\t", 1)[0]
    if body == "/dev/null" or not body.startswith(("a/", "b/")):
        return None
    return body[2:]


def parse_hunks(patch: str) -> dict[str, list[dict[str, int]]]:
    """Key hunks by the surviving path, or the old path when the file was deleted."""
    hunks: dict[str, list[dict[str, int]]] = {}
    old_path = None
    new_path = None
    for line in patch.splitlines():
        if line.startswith("diff --git "):
            old_path = None
            new_path = None
        elif line.startswith("--- "):
            old_path = header_path(line)
        elif line.startswith("+++ "):
            new_path = header_path(line)
        else:
            match = HUNK_RE.match(line)
            path = new_path if new_path is not None else old_path
            if not match or path is None:
                continue
            hunks.setdefault(path, []).append({
                "old_start": int(match.group(1)),
                "old_count": _count(match.group(2)),
                "new_start": int(match.group(3)),
                "new_count": _count(match.group(4)),
            })
    return hunks


def build_scope(base: str | None, head: str) -> dict:
    resolved_base = resolve_base(base)
    git("rev-parse", "--verify", f"{head}^{{commit}}")
    merge_base = git("merge-base", resolved_base, head)
    diff_range = f"{merge_base}..{head}"
    files = parse_name_status(git("diff", "--name-status", "-z", "--find-renames", diff_range))
    stats = parse_numstat(git("diff", "--numstat", "-z", "--find-renames", diff_range))
    hunks = parse_hunks(git("diff", "--unified=0", "--find-renames", diff_range))
    for item in files:
        item.update(stats.get(item["path"], {"additions": 0, "deletions": 0}))
        item["hunks"] = hunks.get(item["path"], [])
    return {
        "base": resolved_base,
        "head": git("rev-parse", head),
        "merge_base": merge_base,
        "files": files,
        "files_changed": len(files),
        "additions": sum(item["additions"] or 0 for item in files),
        "deletions": sum(item["deletions"] or 0 for item in files),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", help="Base branch/ref/SHA; inferred when omitted")
    parser.add_argument("--head", default="HEAD", help="Head ref (default: HEAD)")
    parser.add_argument("--output", help="Write JSON to this path instead of stdout")
    args = parser.parse_args()
    try:
        scope = build_scope(args.base, args.head)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    rendered = json.dumps(scope, indent=2)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + "\n")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
