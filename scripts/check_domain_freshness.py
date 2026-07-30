#!/usr/bin/env python3
"""Validate age and integrity of volatile domain-skill references."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MARKER = re.compile(r"last verified:\s*(\d{4}-\d{2}-\d{2})", re.I)
SOURCE = re.compile(r"https?://", re.I)


def age_problem(value: str, today: dt.date, days: int) -> str | None:
    try:
        date = dt.date.fromisoformat(value[:10])
    except (TypeError, ValueError):
        return f"invalid date {value!r}"
    age = (today - date).days
    if age < 0:
        return f"date is {abs(age)}d in the future"
    if age > days:
        return f"stale by {age - days}d (verified {date}, age {age}d)"
    return None


def check_marked_docs(paths: list[Path], label: str, today: dt.date, days: int,
                      root: Path) -> list[str]:
    issues = []
    for path in paths:
        rel = path.relative_to(root)
        text = path.read_text(errors="replace")
        match = MARKER.search(text)
        if not match:
            issues.append(f"{label}: {rel} missing Last verified marker")
        else:
            problem = age_problem(match.group(1), today, days)
            if problem:
                issues.append(f"{label}: {rel} {problem}")
        if not SOURCE.search(text):
            issues.append(f"{label}: {rel} missing HTTP source URL")
    return issues


def check_polymarket(root: Path, today: dt.date, days: int) -> list[str]:
    refs = root / "skills" / "polymarketv2" / "references"
    paths = sorted(refs.glob("*.md"))
    openapi = refs / "openapi" / "README.md"
    if openapi.exists():
        paths.append(openapi)
    return check_marked_docs(paths, "polymarketv2", today, days, root)


def check_rust_evm(root: Path, today: dt.date, days: int) -> list[str]:
    refs = root / "skills" / "rust-evm" / "references"
    return check_marked_docs(sorted(refs.glob("*.md")), "rust-evm", today, days, root)


def check_hyperliquid(root: Path, today: dt.date, days: int) -> list[str]:
    skill = root / "skills" / "hyperliquid"
    refs = skill / "references"
    manifest_path = refs / "source-map.json"
    issues = []
    try:
        manifest = json.loads(manifest_path.read_text())
    except (OSError, ValueError) as exc:
        return [f"hyperliquid: invalid source-map.json: {exc}"]

    generated = manifest.get("generated_at", "")
    problem = age_problem(generated, today, days)
    if problem:
        issues.append(f"hyperliquid: source-map.json {problem}")

    llms = refs / "llms.txt"
    actual_digest = hashlib.sha256(llms.read_bytes()).hexdigest() if llms.is_file() else None
    if actual_digest != manifest.get("llms_sha256"):
        issues.append("hyperliquid: llms.txt digest does not match source-map.json")

    pages = manifest.get("pages")
    if not isinstance(pages, list):
        return issues + ["hyperliquid: source-map pages must be a list"]
    if manifest.get("page_count") != len(pages):
        issues.append("hyperliquid: page_count does not match pages")
    ok_count = sum(page.get("status") == "ok" for page in pages if isinstance(page, dict))
    if manifest.get("ok_count") != ok_count or manifest.get("error_count") != len(pages) - ok_count:
        issues.append("hyperliquid: status counts do not match pages")

    seen_urls, seen_paths = set(), set()
    for page in pages:
        if not isinstance(page, dict):
            issues.append("hyperliquid: non-object page entry")
            continue
        url, raw_path = page.get("url"), page.get("local_path")
        if url in seen_urls:
            issues.append(f"hyperliquid: duplicate URL {url}")
        seen_urls.add(url)
        if raw_path in seen_paths:
            issues.append(f"hyperliquid: duplicate local path {raw_path}")
        seen_paths.add(raw_path)
        rel = Path(raw_path or "")
        if not raw_path or rel.is_absolute() or ".." in rel.parts:
            issues.append(f"hyperliquid: unsafe local path {raw_path!r}")
            continue
        local = (skill / rel).resolve()
        if skill.resolve() not in local.parents or not local.is_file():
            issues.append(f"hyperliquid: missing mirrored page {raw_path!r}")
            continue
        header = local.read_text(errors="replace")[:1000]
        if f"source_url: {url}" not in header:
            issues.append(f"hyperliquid: source URL mismatch in {raw_path!r}")
        if page.get("status") != "ok":
            issues.append(f"hyperliquid: failed mirror entry {url}")
    return issues


def run_checks(root: Path, today: dt.date, days: int) -> dict:
    checks = {
        "polymarketv2": check_polymarket(root, today, days),
        "hyperliquid": check_hyperliquid(root, today, days),
        "rust-evm": check_rust_evm(root, today, days),
    }
    return {
        "ok": not any(checks.values()),
        "today": today.isoformat(),
        "threshold_days": days,
        "checks": checks,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--today", help="override date for deterministic tests")
    ap.add_argument("--days", type=int, default=90)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    today = dt.date.fromisoformat(args.today) if args.today else dt.date.today()
    result = run_checks(args.root.resolve(), today, args.days)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for name, issues in result["checks"].items():
            print(f"{name}: {'fresh' if not issues else f'{len(issues)} issue(s)'}")
            for issue in issues:
                print(f"  {issue}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
