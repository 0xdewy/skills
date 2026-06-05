#!/usr/bin/env python3
"""Download and extract full text for a targeted subset of corpus papers.

Reads a corpus produced by search_papers.py, selects the requested papers
(by DOI or title), and for each one tries its open-access full-text locators
in priority order (xml -> html -> pdf), extracting clean plain text to a file.
Writes one .txt per paper plus a manifest.json the researcher skill's testing
sub-agents read to know which papers are available in full vs abstract-only.

Usage:
    python3 fetch_fulltext.py --corpus corpus.json \
        --keys "10.1234/abc; some paper title; another title" \
        --out-dir /tmp/researcher-XXX/fulltext [--max-chars 60000] [--max-papers 20]
    python3 fetch_fulltext.py --corpus corpus.json --all --out-dir DIR

Source policy: open access only (arXiv, OpenAlex OA locations, Europe PMC JATS,
plus Unpaywall-resolved OA copies as a DOI fallback). Papers with no OA copy
anywhere are marked status="abstract_only" — the inquiry stays honest about what
was actually read in full.

Unpaywall is only used when RESEARCHER_MAILTO is set to a real email (its API
requires it); otherwise it is skipped cleanly.

Manifest entry schema:
    {key, title, doi, status: full_text|abstract_only|failed,
     path, chars, truncated, locator_used, error}
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
import time

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    sys.exit("requests and beautifulsoup4 are required")

DEFAULT_MAILTO = "researcher-skill@example.com"
# Unpaywall (and the OpenAlex/Crossref polite pools) want a real contact email.
# Override with RESEARCHER_MAILTO; the example.com default disables Unpaywall.
MAILTO = os.environ.get("RESEARCHER_MAILTO", DEFAULT_MAILTO)
HEADERS = {"User-Agent": f"researcher-skill (mailto:{MAILTO})"}
TIMEOUT = 45
# Below this, an extraction is almost certainly a landing-page abstract or stub
# rather than a real full document (methods/results run to many thousands of
# chars). Such papers stay abstract_only rather than masquerading as full text.
MIN_FULLTEXT_CHARS = 2500
# Retry transient failures so a single rate-limit/blip doesn't drop a paper that
# does have an open-access copy. (Self-contained copy of search_papers.py's
# helper — the two scripts are meant to be independently runnable.)
MAX_RETRIES = 3
BACKOFF_BASE = 1.0  # seconds; exponential: BACKOFF_BASE * 2**attempt
MAX_BACKOFF = 20.0
RETRY_STATUSES = {429, 500, 502, 503, 504}


def _get(url: str, **kwargs) -> "requests.Response":
    """GET with retry/backoff on rate limits and transient network errors.

    Defaults headers/timeout to the module's polite values; honors Retry-After
    when sent, else exponential backoff. Raises the last error after MAX_RETRIES
    so callers' own except-clauses still fall through to the next locator.
    """
    kwargs.setdefault("headers", HEADERS)
    kwargs.setdefault("timeout", TIMEOUT)
    last_err: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            r = requests.get(url, **kwargs)
            if r.status_code in RETRY_STATUSES and attempt < MAX_RETRIES - 1:
                retry_after = r.headers.get("Retry-After")
                try:
                    wait = float(retry_after) if retry_after else 0.0
                except ValueError:
                    wait = 0.0
                time.sleep(min(wait or BACKOFF_BASE * (2 ** attempt), MAX_BACKOFF))
                last_err = requests.HTTPError(f"{r.status_code} from {url}")
                continue
            r.raise_for_status()
            return r
        except (requests.Timeout, requests.ConnectionError) as e:
            last_err = e
            if attempt < MAX_RETRIES - 1:
                time.sleep(min(BACKOFF_BASE * (2 ** attempt), MAX_BACKOFF))
    raise last_err or RuntimeError(f"GET failed: {url}")


def _norm(t: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (t or "").lower())


def _slug(title: str, n: int = 60) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (title or "untitled").lower()).strip("-")
    return (s[:n] or "untitled").strip("-")


def select_papers(corpus: list[dict], keys: list[str], take_all: bool) -> list[dict]:
    """Match requested keys (DOI or title substring) to corpus papers.

    A key matches if it equals a paper's DOI (case-insensitive) or its
    normalized form is a substring of the paper's normalized title (so the
    PI can pass motivating-paper titles verbatim). De-duplicates matches.
    """
    if take_all:
        return [p for p in corpus if p.get("fulltext_locators")]
    chosen: list[dict] = []
    seen: set[int] = set()
    for key in keys:
        key = key.strip()
        if not key:
            continue
        kdoi = key.lower().replace("https://doi.org/", "")
        knorm = _norm(key)
        for i, p in enumerate(corpus):
            if i in seen:
                continue
            doi = (p.get("doi") or "").lower()
            if (doi and doi == kdoi) or (knorm and knorm in _norm(p.get("title", ""))):
                chosen.append(p)
                seen.add(i)
                break  # first best match for this key
    return chosen


def extract_xml(content: bytes) -> str:
    """Extract body text from a JATS full-text XML document (Europe PMC)."""
    soup = BeautifulSoup(content, "lxml-xml")
    body = soup.find("body")
    if body is None:
        return ""
    # Drop apparatus that adds noise rather than scientific content.
    for tag in body.find_all(["ref-list", "table-wrap", "fig", "table"]):
        tag.decompose()
    parts = [el.get_text(" ", strip=True) for el in body.find_all(["title", "p"])]
    return "\n\n".join(p for p in parts if p)


def extract_html(content: bytes) -> str:
    """Extract main readable text from an HTML page (arXiv HTML, OA landing)."""
    soup = BeautifulSoup(content, "lxml")
    for tag in soup(["script", "style", "nav", "header", "footer", "aside",
                     "noscript", "form"]):
        tag.decompose()
    main = soup.find("article") or soup.find("main") or soup.body or soup
    parts = [el.get_text(" ", strip=True)
             for el in main.find_all(["h1", "h2", "h3", "p", "li"])]
    text = "\n\n".join(p for p in parts if p)
    # Fallback for pages without semantic tags.
    return text or main.get_text("\n", strip=True)


def extract_pdf(content: bytes) -> str:
    """Extract text from a PDF with pypdf (lossy but dependency-free)."""
    try:
        from pypdf import PdfReader
    except ImportError:
        return ""
    reader = PdfReader(io.BytesIO(content))
    pages = []
    for page in reader.pages:
        try:
            pages.append(page.extract_text() or "")
        except Exception:  # noqa: BLE001 — skip an unparseable page, keep the rest
            continue
    return "\n\n".join(p for p in pages if p.strip())


EXTRACTORS = {"xml": extract_xml, "html": extract_html, "pdf": extract_pdf}


def unpaywall_enabled() -> bool:
    """Unpaywall's API requires a real contact email and 422s on example.com.

    Enabled only when the operator set RESEARCHER_MAILTO; warns once otherwise so
    a missing email is visible without spraying rejected requests.
    """
    if MAILTO != DEFAULT_MAILTO:
        return True
    if not getattr(unpaywall_enabled, "_warned", False):
        print("[unpaywall] skipped — set RESEARCHER_MAILTO=you@domain to enable "
              "DOI->OA fallback", file=sys.stderr)
        unpaywall_enabled._warned = True  # type: ignore[attr-defined]
    return False


def unpaywall_locators(doi: str) -> list[dict]:
    """Resolve a DOI to open-access full-text locators via Unpaywall.

    Returns pdf/html locators drawn from best_oa_location + oa_locations,
    repository copies first (publisher OA URLs are more often bot-blocked).
    Any error yields [] so a failure never sinks the fetch.
    """
    try:
        r = _get(
            f"https://api.unpaywall.org/v2/{doi}",
            params={"email": MAILTO},
        )
        data = r.json()
    except Exception:  # noqa: BLE001 — Unpaywall is a best-effort fallback
        return []
    oas = []
    best = data.get("best_oa_location")
    for oa in (data.get("oa_locations") or []) + ([best] if best else []):
        if oa:
            oas.append(oa)
    # Repository copies before publisher copies; preserve order within each group.
    oas.sort(key=lambda oa: 0 if oa.get("host_type") == "repository" else 1)
    locators: list[dict] = []
    seen: set[str] = set()
    for oa in oas:
        for kind, url in (("pdf", oa.get("url_for_pdf")), ("html", oa.get("url"))):
            if url and url not in seen:
                seen.add(url)
                locators.append({"kind": kind, "url": url, "via": "unpaywall"})
    return locators


def fetch_one(paper: dict, out_dir: str, max_chars: int) -> dict:
    """Try each locator in order; write the first successful extraction."""
    title = paper.get("title", "")
    entry = {
        "key": paper.get("doi") or title,
        "title": title,
        "doi": paper.get("doi"),
        "status": "abstract_only",
        "path": None,
        "chars": 0,
        "truncated": False,
        "locator_used": None,
        "error": None,
    }
    # Try the paper's own OA locators first; if they run out without yielding a
    # full document, fall back once to Unpaywall-resolved OA copies for the DOI
    # (which rescues many paywalled-per-Crossref papers and publisher-bot-blocked
    # ones via repository mirrors). The list is extended in place mid-loop.
    locators = list(paper.get("fulltext_locators") or [])
    tried: set[str] = set()
    queried_unpaywall = False
    last_err = None
    had_error = False  # a real fetch/parse failure, vs merely thin content
    i = 0
    while True:
        if i >= len(locators):
            doi = paper.get("doi")
            if not queried_unpaywall and doi and unpaywall_enabled():
                queried_unpaywall = True
                locators.extend(unpaywall_locators(doi))
                continue
            break
        loc = locators[i]
        i += 1
        if loc["url"] in tried:
            continue
        tried.add(loc["url"])
        try:
            r = _get(loc["url"])
            text = EXTRACTORS[loc["kind"]](r.content)
            # Require enough text to be a real document, not a stub/landing page.
            if len(text.strip()) < MIN_FULLTEXT_CHARS:
                last_err = f"{loc['kind']} yielded only {len(text.strip())} chars"
                continue
            truncated = len(text) > max_chars
            text = text[:max_chars]
            path = os.path.join(out_dir, f"{_slug(title)}.txt")
            used = loc["kind"] + (" (unpaywall)" if loc.get("via") == "unpaywall" else "")
            header = (
                f"# {title}\n"
                f"DOI: {paper.get('doi')}\n"
                f"Source: {loc['url']} ({used})\n"
                f"{'[TRUNCATED to %d chars]' % max_chars if truncated else ''}\n"
                f"{'=' * 70}\n\n"
            )
            with open(path, "w") as f:
                f.write(header + text)
            entry.update(
                status="full_text",
                path=path,
                chars=len(text),
                truncated=truncated,
                locator_used=used,
            )
            return entry
        except Exception as e:  # noqa: BLE001 — try the next locator
            last_err = str(e)
            had_error = True
            continue

    # No full document anywhere (own locators + Unpaywall). A real error
    # (network/HTTP/parse) is "failed"; merely thin/abstract-sized content — or no
    # OA copy known at all — is honestly "abstract_only".
    entry["status"] = "failed" if had_error else "abstract_only"
    entry["error"] = last_err
    return entry


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--keys", default="",
                    help="semicolon-separated DOIs or title substrings")
    ap.add_argument("--all", action="store_true",
                    help="fetch every paper that has a full-text locator")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--max-chars", type=int, default=60000)
    ap.add_argument("--max-papers", type=int, default=20)
    args = ap.parse_args()

    with open(args.corpus) as f:
        corpus = json.load(f)

    keys = [k for k in args.keys.split(";")] if args.keys else []
    targets = select_papers(corpus, keys, args.all)[: args.max_papers]
    os.makedirs(args.out_dir, exist_ok=True)

    manifest = []
    for p in targets:
        entry = fetch_one(p, args.out_dir, args.max_chars)
        manifest.append(entry)
        print(f"[{entry['status']:13}] {(entry['title'] or '')[:60]}"
              f" ({entry['locator_used'] or entry.get('error') or '-'})",
              file=sys.stderr)
        time.sleep(0.4)  # polite pacing on shared OA endpoints

    with open(os.path.join(args.out_dir, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    full = sum(1 for m in manifest if m["status"] == "full_text")
    abst = sum(1 for m in manifest if m["status"] == "abstract_only")
    fail = sum(1 for m in manifest if m["status"] == "failed")
    print(
        f"\nDONE: {full} full / {abst} abstract-only / {fail} failed "
        f"-> {args.out_dir}/manifest.json",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
