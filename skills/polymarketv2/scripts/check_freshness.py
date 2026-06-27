#!/usr/bin/env python3
"""Flag stale reference docs in the polymarketv2 skill.

Greps every references/*.md (and references/openapi/README.md) for its
`last verified: YYYY-MM-DD` marker and reports:
  - files whose marker is older than the threshold (default 90 days), and
  - files missing the marker entirely.

The skill freezes facts at a point in time; Polymarket's v2 docs change quickly,
so this gives a deterministic staleness signal without a manual audit.

No network, stdlib only.

Usage:
    python scripts/check_freshness.py                # threshold 90 days
    python scripts/check_freshness.py --days 30
    python scripts/check_freshness.py --json
Exit code 0 if everything is fresh and marked; 1 otherwise.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

REFS_DIR = Path(__file__).resolve().parent.parent / "references"
MARKER = re.compile(r"last verified:\s*(\d{4})-(\d{2})-(\d{2})", re.IGNORECASE)


def iter_docs() -> list[Path]:
    docs = sorted(REFS_DIR.glob("*.md"))
    readme = REFS_DIR / "openapi" / "README.md"
    if readme.exists():
        docs.append(readme)
    return docs


def find_date(text: str) -> dt.date | None:
    m = MARKER.search(text)
    if not m:
        return None
    try:
        return dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description="Check polymarketv2 reference freshness.")
    ap.add_argument("--days", type=int, default=90, help="staleness threshold in days (default 90)")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--today", help="override today's date (YYYY-MM-DD) for testing")
    args = ap.parse_args()

    today = dt.date.fromisoformat(args.today) if args.today else dt.date.today()
    threshold = dt.timedelta(days=args.days)

    stale: list[dict] = []
    missing: list[str] = []
    fresh = 0

    for path in iter_docs():
        rel = path.relative_to(REFS_DIR).as_posix()
        date = find_date(path.read_text())
        if date is None:
            missing.append(rel)
            continue
        age = (today - date).days
        if today - date > threshold:
            stale.append({"file": rel, "last_verified": date.isoformat(), "age_days": age})
        else:
            fresh += 1

    ok = not stale and not missing
    if args.json:
        print(json.dumps({"ok": ok, "fresh": fresh, "stale": stale, "missing": missing,
                          "threshold_days": args.days, "today": today.isoformat()}, indent=2))
        return 0 if ok else 1

    print(f"{fresh} fresh · {len(stale)} stale · {len(missing)} missing marker "
          f"(threshold {args.days}d, today {today.isoformat()})")
    for s in stale:
        print(f"  STALE  {s['file']} — last verified {s['last_verified']} ({s['age_days']}d ago)")
    for m in missing:
        print(f"  NO MARKER  {m}")
    if ok:
        print("All reference files carry a current `last verified:` marker.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
