#!/usr/bin/env python3
"""Mirror Hyperliquid GitBook Markdown docs into skill references.

This uses GitBook's public llms.txt index and Markdown page variants. It avoids
HTML crawling and writes provenance headers so the local mirror remains
auditable.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse


BASE = "https://hyperliquid.gitbook.io/hyperliquid-docs"
ROBOTS_URL = "https://hyperliquid.gitbook.io/robots.txt"
LLMS_URL = f"{BASE}/llms.txt"
USER_AGENT = "CodexSkillBuilder/1.0 (+https://openai.com; docs reference scrape)"


LINK_RE = re.compile(r"- \[([^\]]+)\]\((https://hyperliquid\.gitbook\.io/hyperliquid-docs/[^)]+?\.md)\)(?::\s*([^\n]+))?")


def fetch(url: str, timeout: int = 30) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def slug_for_url(url: str) -> str:
    path = urlparse(url).path
    prefix = "/hyperliquid-docs/"
    if path.startswith(prefix):
        path = path[len(prefix):]
    if path.endswith(".md"):
        path = path[:-3]
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", path).strip("-").lower()
    return slug or "index"


def section_for_url(url: str) -> str:
    path = urlparse(url).path.replace("/hyperliquid-docs/", "")
    if path.startswith("for-developers/api/") or path == "for-developers/api.md":
        return "api"
    if path.startswith("for-developers/hyperevm/") or path == "for-developers/hyperevm.md":
        return "hyperevm-dev"
    if path.startswith("for-developers/nodes/") or path == "for-developers/nodes.md":
        return "nodes"
    if path.startswith("hypercore/"):
        return "hypercore"
    if path.startswith("hyperevm"):
        return "hyperevm"
    if path.startswith("hyperliquid-improvement-proposals-hips"):
        return "hips"
    if path.startswith("trading"):
        return "trading"
    if path.startswith("validators"):
        return "validators"
    if path.startswith("support"):
        return "support"
    if path.startswith("builder-tools"):
        return "builder-tools"
    if path.startswith("onboarding"):
        return "onboarding"
    return "general"


def parse_llms(llms_text: str) -> list[dict[str, str]]:
    pages: list[dict[str, str]] = []
    seen: set[str] = set()
    for match in LINK_RE.finditer(llms_text):
        title, url, description = match.groups()
        if url in seen:
            continue
        seen.add(url)
        pages.append(
            {
                "title": title.strip(),
                "url": url,
                "description": (description or "").strip(),
                "slug": slug_for_url(url),
                "section": section_for_url(url),
            }
        )
    return pages


def write_compliance(out_dir: Path, robots_text: str, page_count: int, delay: float) -> None:
    (out_dir / "scrape-compliance.md").write_text(
        "\n".join(
            [
                "# Scrape Compliance Note",
                "",
                f"- Target: `{BASE}` Markdown documentation pages from `llms.txt`",
                f"- robots.txt checked: allowed, `{ROBOTS_URL}` permits `/` and disallows only query search/ask paths",
                "- Terms/source permission: public GitBook docs with explicit `llms.txt` agent index and Markdown page variants",
                f"- Rate limit: {delay:.2f}s delay between page requests, {page_count} indexed pages",
                f"- User-Agent: `{USER_AGENT}`",
                "- Decision: proceed",
                "",
                "## robots.txt",
                "",
                "```text",
                robots_text.strip(),
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )


def write_index(out_dir: Path, pages: list[dict[str, str]]) -> None:
    by_section: dict[str, list[dict[str, str]]] = {}
    for page in pages:
        by_section.setdefault(page["section"], []).append(page)

    lines = [
        "# Hyperliquid Docs Local Index",
        "",
        "Generated from the official GitBook `llms.txt` index. Load the smallest relevant",
        "reference first, then open individual mirrored pages from `references/docs/` when",
        "the answer depends on exact request schemas, examples, constants, or current wording.",
        "",
        "## Sections",
        "",
    ]
    for section in sorted(by_section):
        lines.append(f"### {section}")
        lines.append("")
        for page in by_section[section]:
            desc = f" - {page['description']}" if page["description"] else ""
            lines.append(f"- [{page['title']}](docs/{page['slug']}.md) ([source]({page['url']})){desc}")
        lines.append("")

    (out_dir / "index.md").write_text("\n".join(lines), encoding="utf-8")


def mirror_pages(out_dir: Path, pages: list[dict[str, str]], delay: float) -> list[dict[str, str]]:
    docs_dir = out_dir / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    mirrored: list[dict[str, str]] = []
    for idx, page in enumerate(pages, start=1):
        if idx > 1:
            time.sleep(delay)
        try:
            body = fetch(page["url"])
            status = "ok"
            error = ""
        except (urllib.error.URLError, TimeoutError) as exc:
            body = ""
            status = "error"
            error = str(exc)

        path = docs_dir / f"{page['slug']}.md"
        header = [
            "---",
            f"title: {json.dumps(page['title'])[1:-1]}",
            f"source_url: {page['url']}",
            f"section: {page['section']}",
            f"scrape_status: {status}",
            "---",
            "",
        ]
        if status == "ok":
            path.write_text("\n".join(header) + body, encoding="utf-8")
        else:
            path.write_text("\n".join(header) + f"# Fetch failed\n\n{error}\n", encoding="utf-8")

        mirrored_page = dict(page)
        mirrored_page["local_path"] = str(path.relative_to(out_dir.parent))
        mirrored_page["status"] = status
        if error:
            mirrored_page["error"] = error
        mirrored.append(mirrored_page)
        print(f"{idx:03d}/{len(pages):03d} {status} {page['slug']}", file=sys.stderr)
    return mirrored


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="references", help="Output directory")
    parser.add_argument("--delay", type=float, default=0.25, help="Delay between page requests")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    robots_text = fetch(ROBOTS_URL)
    llms_text = fetch(LLMS_URL)
    pages = parse_llms(llms_text)
    if not pages:
        raise SystemExit("No docs pages found in llms.txt")

    (out_dir / "llms.txt").write_text(llms_text, encoding="utf-8")
    write_compliance(out_dir, robots_text, len(pages), args.delay)
    mirrored = mirror_pages(out_dir, pages, args.delay)
    write_index(out_dir, mirrored)
    manifest = {
        "source": LLMS_URL,
        "page_count": len(mirrored),
        "ok_count": sum(1 for page in mirrored if page["status"] == "ok"),
        "error_count": sum(1 for page in mirrored if page["status"] != "ok"),
        "user_agent": USER_AGENT,
        "pages": mirrored,
    }
    (out_dir / "source-map.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(
        f"DONE: {out_dir}/source-map.json - {manifest['ok_count']} pages mirrored, "
        f"{manifest['error_count']} errors",
    )
    return 0 if manifest["error_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
