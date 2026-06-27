#!/usr/bin/env python3
"""Deterministic local search over the polymarketv2 reference docs.

Lets an agent find the right reference file + heading for a query without
loading every file. Ranks matches from two sources:

  1. The alias table in references/source-map.json (includes common WRONG/legacy
     terms that route to the correct v2 doc).
  2. Markdown headings (and their first line of body) across references/*.md.

No network, stdlib only.

Usage:
    python scripts/search_refs.py "balance allowance signature_type 3"
    python scripts/search_refs.py --json "place an order python"
    python scripts/search_refs.py --limit 3 "geoblock"
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REFS_DIR = Path(__file__).resolve().parent.parent / "references"
SOURCE_MAP = REFS_DIR / "source-map.json"

_WORD = re.compile(r"[a-z0-9_./@+-]+")


def tokenize(text: str) -> list[str]:
    return _WORD.findall(text.lower())


def slug(heading: str) -> str:
    s = heading.strip().lower()
    s = re.sub(r"[`*]", "", s)
    s = re.sub(r"[^a-z0-9\s_-]", "", s)
    s = re.sub(r"\s+", "-", s).strip("-")
    return s


def load_alias_entries() -> list[dict]:
    if not SOURCE_MAP.exists():
        return []
    data = json.loads(SOURCE_MAP.read_text())
    return data.get("entries", [])


def first_body_line(lines: list[str], start: int) -> str:
    for ln in lines[start + 1 :]:
        t = ln.strip()
        if t and not t.startswith("#"):
            return re.sub(r"\s+", " ", t)[:140]
    return ""


def scan_headings(path: Path) -> list[dict]:
    out: list[dict] = []
    lines = path.read_text().splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if not m:
            continue
        heading = m.group(2).strip()
        out.append(
            {
                "file": path.name,
                "heading": heading,
                "anchor": slug(heading),
                "snippet": first_body_line(lines, i) or heading,
                "terms": tokenize(heading),
            }
        )
    return out


def score(query_tokens: set[str], terms: list[str], phrase_text: str, query: str) -> float:
    if not query_tokens:
        return 0.0
    term_text = " ".join(terms)
    s = 0.0
    for qt in query_tokens:
        if qt in terms:
            s += 2.0
        elif any(qt in t or t in qt for t in terms):
            s += 1.0
    # phrase bonus: whole query substring appears
    if query and query in phrase_text:
        s += 3.0
    return s


def search(query: str, limit: int) -> list[dict]:
    q = query.lower().strip()
    q_tokens = set(tokenize(query))
    results: list[dict] = []

    for e in load_alias_entries():
        terms = [t.lower() for t in e.get("terms", [])]
        phrase_text = " ".join(terms)
        sc = score(q_tokens, [t for term in terms for t in tokenize(term)], phrase_text, q)
        if sc > 0:
            results.append(
                {
                    "kind": "alias",
                    "file": e["file"],
                    "anchor": e.get("anchor", ""),
                    "heading": e.get("anchor", ""),
                    "snippet": "matched terms: " + ", ".join(terms[:8]),
                    "source_url": e.get("source_url", ""),
                    "score": sc,
                }
            )

    if REFS_DIR.exists():
        for path in sorted(REFS_DIR.glob("*.md")):
            for h in scan_headings(path):
                sc = score(q_tokens, h["terms"], h["snippet"].lower(), q)
                if sc > 0:
                    results.append(
                        {
                            "kind": "heading",
                            "file": h["file"],
                            "anchor": h["anchor"],
                            "heading": h["heading"],
                            "snippet": h["snippet"],
                            "source_url": "",
                            "score": sc,
                        }
                    )

    # de-dupe by (file, anchor), keep best score
    best: dict[tuple[str, str], dict] = {}
    for r in results:
        key = (r["file"], r["anchor"])
        if key not in best or r["score"] > best[key]["score"]:
            best[key] = r
    ranked = sorted(best.values(), key=lambda r: (-r["score"], r["file"], r["anchor"]))
    return ranked[:limit]


def main() -> int:
    ap = argparse.ArgumentParser(description="Search polymarketv2 reference docs.")
    ap.add_argument("query", nargs="+", help="search terms")
    ap.add_argument("--limit", type=int, default=6, help="max results (default 6)")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    args = ap.parse_args()

    query = " ".join(args.query)
    hits = search(query, args.limit)

    if args.json:
        print(json.dumps(hits, indent=2))
        return 0 if hits else 1

    if not hits:
        print(f'No matches for "{query}". Try fewer/looser terms, or read references/index.md.')
        return 1

    print(f'Top matches for "{query}":\n')
    for r in hits:
        loc = f"references/{r['file']}"
        if r["anchor"]:
            loc += f"#{r['anchor']}"
        line = f"  {loc} — {r['snippet']}"
        if r.get("source_url"):
            line += f"  (source: {r['source_url']})"
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
