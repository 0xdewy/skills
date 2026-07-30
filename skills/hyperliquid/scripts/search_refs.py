#!/usr/bin/env python3
"""Rank Hyperliquid reference files/headings for a query; stdlib and local only."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


REFS = Path(__file__).resolve().parent.parent / "references"
SOURCE_MAP = REFS / "source-map.json"
WORD = re.compile(r"[a-z0-9_./@+-]+")
ALIASES = [
    ("asset id spot builder deployed perp outcome token", "docs/for-developers-api-asset-ids.md"),
    ("place cancel order exchange signing tif", "docs/for-developers-api-exchange-endpoint.md"),
    ("info meta market data positions orderbook", "docs/for-developers-api-info-endpoint.md"),
    ("websocket subscription stream reconnect", "docs/for-developers-api-websocket-subscriptions.md"),
    ("rate limit user limit", "docs/for-developers-api-rate-limits-and-user-limits.md"),
    ("error response error code", "docs/for-developers-api-error-responses.md"),
    ("corewriter precompile hyperevm hypercore", "docs/for-developers-hyperevm-interacting-with-hypercore.md"),
]


def tokens(text: str) -> set[str]:
    return set(WORD.findall(text.lower()))


def slug(text: str) -> str:
    text = re.sub(r"[`*]", "", text.lower())
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def score(query: set[str], text: str) -> float:
    words = tokens(text)
    if not query or not words:
        return 0.0
    exact = len(query & words) * 2.0
    partial = sum(1.0 for q in query if any(q in word or word in q for word in words))
    return exact + partial


def source_pages() -> list[dict]:
    if not SOURCE_MAP.exists():
        return []
    return json.loads(SOURCE_MAP.read_text()).get("pages", [])


def first_body_line(lines: list[str], start: int) -> str:
    for line in lines[start + 1 :]:
        line = re.sub(r"\s+", " ", line.strip())
        if line and not line.startswith("#"):
            return line[:160]
    return ""


def search(query: str, limit: int) -> list[dict]:
    query_tokens = tokens(query)
    ranked: dict[tuple[str, str], dict] = {}

    for terms, path in ALIASES:
        overlap = len(query_tokens & tokens(terms))
        if overlap:
            ranked[(path, "")] = {
                "file": path,
                "heading": "curated route",
                "anchor": "",
                "snippet": f"matched {overlap} routing terms",
                "source_url": "",
                "score": 20.0 + overlap * 8.0,
            }

    for page in source_pages():
        identity = " ".join(
            str(page.get(key, "")) for key in ("title", "slug", "local_path")
        )
        context = " ".join(str(page.get(key, "")) for key in ("description", "section"))
        value = 3 * score(query_tokens, identity) + score(query_tokens, context)
        if value:
            path = page.get("local_path", "").removeprefix("references/")
            key = (path, "")
            hit = {
                "file": path,
                "heading": page.get("title", ""),
                "anchor": "",
                "snippet": page.get("description", "") or page.get("section", ""),
                "source_url": page.get("url", ""),
                "score": value,
            }
            if key not in ranked or value > ranked[key]["score"]:
                ranked[key] = hit

    for path in sorted(REFS.rglob("*.md")):
        try:
            lines = path.read_text(errors="replace").splitlines()
        except OSError:
            continue
        for index, line in enumerate(lines):
            match = re.match(r"^(#{1,6})\s+(.*)$", line)
            if not match:
                continue
            heading = match.group(2).strip()
            snippet = first_body_line(lines, index)
            value = 3 * score(query_tokens, f"{path} {heading}") + score(query_tokens, snippet)
            if not value:
                continue
            rel = str(path.relative_to(REFS))
            anchor = slug(heading)
            key = (rel, anchor)
            hit = {
                "file": rel,
                "heading": heading,
                "anchor": anchor,
                "snippet": snippet,
                "source_url": "",
                "score": value,
            }
            if key not in ranked or value > ranked[key]["score"]:
                ranked[key] = hit

    return sorted(
        ranked.values(), key=lambda item: (-item["score"], item["file"], item["anchor"])
    )[:limit]


def main() -> int:
    parser = argparse.ArgumentParser(description="Search local Hyperliquid references.")
    parser.add_argument("query", nargs="+")
    parser.add_argument("--limit", type=int, default=6)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    query = " ".join(args.query)
    hits = search(query, args.limit)
    if args.json:
        print(json.dumps(hits, indent=2))
    elif hits:
        for hit in hits:
            location = f"references/{hit['file']}"
            if hit["anchor"]:
                location += f"#{hit['anchor']}"
            print(f"{location} — {hit['heading']}: {hit['snippet']}")
    else:
        print(f'No matches for "{query}".')
    return 0 if hits else 1


if __name__ == "__main__":
    raise SystemExit(main())
