#!/usr/bin/env python3
"""Search publicly available scientific literature across multiple open APIs.

Queries OpenAlex, arXiv, Crossref, Europe PMC, and Semantic Scholar — all
key-less, publicly available sources — normalizes results into one schema,
deduplicates by DOI/title, and writes a JSON corpus the researcher skill's
sub-agents read.

Usage:
    python3 search_papers.py "query one" ["query two" ...] [--out PATH]
            [--limit N] [--since YEAR] [--sources a,b,c]

Multiple queries are each run against every chosen source and merged/deduped into
one corpus, so callers pass all their query strings in a single invocation.

Output schema (one object per paper):
    {title, authors[], year, venue, doi, url, abstract, citations, source,
     is_retracted, fulltext_locators[], bias_flags[]}

After corpus build, a bias scan runs automatically and outputs:
    data/bias-funding.json      — papers with funding/conflict signals
    data/bias-institutions.json — institutional concentration
    data/bias-publication-bias.json — null-result ratio and publication bias flag
    data/bias-summary.md        — human-readable bias summary
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.parse
import xml.etree.ElementTree as ET
from collections import Counter

try:
    import requests
except ImportError:
    sys.exit("requests is required: pip install requests")

# A contact in the User-Agent puts OpenAlex/Crossref in their faster "polite"
# pool and is just good citizenship for shared public APIs. Override the contact
# with RESEARCHER_MAILTO (the same env var fetch_fulltext.py uses for Unpaywall).
import os
MAILTO = os.environ.get("RESEARCHER_MAILTO", "researcher-skill@example.com")
HEADERS = {"User-Agent": f"researcher-skill (mailto:{MAILTO})"}
TIMEOUT = 30

# Semantic Scholar is aggressively rate-limited without a key; set this to use it
# reliably. Other sources are key-less.
S2_API_KEY = os.environ.get("SEMANTIC_SCHOLAR_API_KEY")
# Retry transient failures (rate limits, 5xx, dropped connections) so one blip
# doesn't drop a whole source's results.
MAX_RETRIES = 3
BACKOFF_BASE = 1.0  # seconds; exponential: BACKOFF_BASE * 2**attempt
MAX_BACKOFF = 20.0
RETRY_STATUSES = {429, 500, 502, 503, 504}


def _get(url: str, **kwargs) -> "requests.Response":
    """GET with retry/backoff on rate limits and transient network errors.

    Defaults headers/timeout to the module's polite values. Retries on the
    statuses in RETRY_STATUSES and on Timeout/ConnectionError, honoring a
    Retry-After header when the server sends one. Raises the last error after
    MAX_RETRIES so each source's own try/except still records it as failed.
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
                wait = wait or BACKOFF_BASE * (2 ** attempt)
                time.sleep(min(wait, MAX_BACKOFF))
                last_err = requests.HTTPError(f"{r.status_code} from {url}")
                continue
            r.raise_for_status()
            return r
        except (requests.Timeout, requests.ConnectionError) as e:
            last_err = e
            if attempt < MAX_RETRIES - 1:
                time.sleep(min(BACKOFF_BASE * (2 ** attempt), MAX_BACKOFF))
    raise last_err or RuntimeError(f"GET failed: {url}")


def _norm_title(t: str) -> str:
    """Lowercase, strip punctuation/whitespace — for dedup matching only."""
    return re.sub(r"[^a-z0-9]+", "", (t or "").lower())


# Publishers/indexers mark retracted work by prefixing the title ("RETRACTED:",
# "RETRACTED ARTICLE:", "Retraction—…") or tagging it "(Retracted)". This catches
# retractions a source's metadata flag misses — e.g. when only Crossref (which has
# no is_retracted field) returned the paper. Anchored + colon/bracket-gated to
# avoid false positives like a review titled "Retracted articles in oncology".
_RETRACTED_TITLE = re.compile(
    r"^\s*retract(?:ed(?:\s+article)?|ion)\s*[:\—\-–]"
    r"|[\(\[]\s*retracted\s*[\)\]]",
    re.IGNORECASE,
)


def _looks_retracted(title: str) -> bool:
    return bool(_RETRACTED_TITLE.search(title or ""))


def _add_locator(locators: list[dict], kind: str, url: str | None) -> None:
    """Append a full-text locator if the url is present and not already listed.

    Locators are kept best-first (xml > html > pdf); fetch_fulltext.py tries them
    in list order. kind is one of: xml, html, pdf.
    """
    if not url:
        return
    if any(loc["url"] == url for loc in locators):
        return
    locators.append({"kind": kind, "url": url})


def _reconstruct_abstract(inverted: dict | None) -> str:
    """OpenAlex ships abstracts as an inverted index {word: [positions]}."""
    if not inverted:
        return ""
    positions: list[tuple[int, str]] = []
    for word, idxs in inverted.items():
        for i in idxs:
            positions.append((i, word))
    positions.sort()
    return " ".join(w for _, w in positions)


def search_openalex(query: str, limit: int, since: int | None) -> list[dict]:
    params = {
        "search": query,
        "per-page": min(limit, 50),
        "mailto": MAILTO,
        "sort": "relevance_score:desc",
    }
    if since:
        params["filter"] = f"from_publication_date:{since}-01-01"
    r = _get("https://api.openalex.org/works", params=params)
    out = []
    for w in r.json().get("results", []):
        doi = (w.get("doi") or "").replace("https://doi.org/", "")
        authors = [
            a.get("author", {}).get("display_name", "")
            for a in w.get("authorships", [])
        ]
        oa = w.get("open_access") or {}
        best = w.get("best_oa_location") or {}
        locators: list[dict] = []
        _add_locator(locators, "pdf", best.get("pdf_url"))
        _add_locator(locators, "html", best.get("landing_page_url"))
        _add_locator(locators, "html", oa.get("oa_url"))
        out.append(
            {
                "title": w.get("title") or "",
                "authors": [a for a in authors if a][:12],
                "year": w.get("publication_year"),
                "venue": (
                    (w.get("primary_location") or {}).get("source") or {}
                ).get("display_name"),
                "doi": doi or None,
                "url": w.get("id"),
                "abstract": _reconstruct_abstract(
                    w.get("abstract_inverted_index")
                ),
                "citations": w.get("cited_by_count", 0),
                "source": "openalex",
                "oa_status": "oa" if oa.get("is_oa") else "closed",
                "is_retracted": bool(w.get("is_retracted")),
                "fulltext_locators": locators,
            }
        )
    return out


def search_arxiv(query: str, limit: int, since: int | None) -> list[dict]:
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": limit,
        "sortBy": "relevance",
    }
    r = _get("http://export.arxiv.org/api/query", params=params)
    ns = {"a": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(r.text)
    out = []
    for e in root.findall("a:entry", ns):
        published = (e.findtext("a:published", "", ns) or "")[:4]
        year = int(published) if published.isdigit() else None
        if since and year and year < since:
            continue
        authors = [
            a.findtext("a:name", "", ns)
            for a in e.findall("a:author", ns)
        ]
        entry_id = e.findtext("a:id", "", ns)
        # entry_id looks like http://arxiv.org/abs/1706.03762v5 -> strip to bare id
        m = re.search(r"arxiv\.org/abs/(.+?)(v\d+)?$", entry_id or "")
        arxiv_id = m.group(1) if m else None
        locators: list[dict] = []
        if arxiv_id:
            _add_locator(locators, "html", f"https://arxiv.org/html/{arxiv_id}")
            _add_locator(locators, "pdf", f"https://arxiv.org/pdf/{arxiv_id}")
        out.append(
            {
                "title": " ".join(
                    (e.findtext("a:title", "", ns) or "").split()
                ),
                "authors": [a for a in authors if a][:12],
                "year": year,
                "venue": "arXiv",
                "doi": None,
                "url": entry_id,
                "abstract": " ".join(
                    (e.findtext("a:summary", "", ns) or "").split()
                ),
                "citations": None,
                "source": "arxiv",
                "oa_status": "oa",
                "is_retracted": False,
                "fulltext_locators": locators,
            }
        )
    return out


def search_crossref(query: str, limit: int, since: int | None) -> list[dict]:
    params = {"query": query, "rows": limit, "select":
              "title,author,issued,container-title,DOI,URL,abstract,is-referenced-by-count"}
    if since:
        params["filter"] = f"from-pub-date:{since}-01-01"
    r = _get("https://api.crossref.org/works", params=params)
    out = []
    for w in r.json().get("message", {}).get("items", []):
        title = (w.get("title") or [""])[0]
        if not title:
            continue
        authors = [
            " ".join(filter(None, [a.get("given"), a.get("family")]))
            for a in w.get("author", [])
        ]
        parts = (w.get("issued", {}).get("date-parts") or [[None]])[0]
        year = parts[0] if parts else None
        abstract = re.sub(r"<[^>]+>", "", w.get("abstract", "") or "")
        out.append(
            {
                "title": title,
                "authors": [a for a in authors if a][:12],
                "year": year,
                "venue": (w.get("container-title") or [None])[0],
                "doi": w.get("DOI"),
                "url": w.get("URL"),
                "abstract": abstract.strip(),
                "citations": w.get("is-referenced-by-count", 0),
                "source": "crossref",
                "oa_status": "unknown",
                "is_retracted": False,
                "fulltext_locators": [],
            }
        )
    return out


def search_europepmc(query: str, limit: int, since: int | None) -> list[dict]:
    q = query
    if since:
        q = f"{query} AND PUB_YEAR:[{since} TO 3000]"
    params = {
        "query": q,
        "format": "json",
        "pageSize": limit,
        "resultType": "core",
    }
    r = _get(
        "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
        params=params,
    )
    out = []
    for w in r.json().get("resultList", {}).get("result", []):
        year = w.get("pubYear")
        locators: list[dict] = []
        # Use EPMC's own advertised full-text URLs (resultType=core supplies
        # these); only the entries marked open/free are fetchable without a
        # subscription. documentStyle maps to our locator kind.
        style_to_kind = {"xml": "xml", "pdf": "pdf", "html": "html"}
        for ft in (w.get("fullTextUrlList") or {}).get("fullTextUrl", []):
            if ft.get("availability") not in ("Open access", "Free"):
                continue
            kind = style_to_kind.get(ft.get("documentStyle"))
            if kind:
                _add_locator(locators, kind, ft.get("url"))
        out.append(
            {
                "title": w.get("title", ""),
                "authors": [
                    a.strip()
                    for a in (w.get("authorString", "") or "").split(",")
                    if a.strip()
                ][:12],
                "year": int(year) if str(year).isdigit() else None,
                "venue": w.get("journalTitle"),
                "doi": w.get("doi"),
                "url": f"https://doi.org/{w['doi']}" if w.get("doi") else None,
                "abstract": w.get("abstractText", "") or "",
                "citations": w.get("citedByCount", 0),
                "source": "europepmc",
                "oa_status": "oa" if w.get("isOpenAccess") == "Y" else "unknown",
                "is_retracted": False,
                "fulltext_locators": locators,
            }
        )
    return out


def search_semanticscholar(query: str, limit: int, since: int | None) -> list[dict]:
    params = {
        "query": query,
        "limit": min(limit, 100),
        "fields": "title,authors,year,venue,externalIds,url,abstract,"
        "citationCount,openAccessPdf,isOpenAccess",
    }
    if since:
        params["year"] = f"{since}-"
    headers = {**HEADERS, **({"x-api-key": S2_API_KEY} if S2_API_KEY else {})}
    r = _get(
        "https://api.semanticscholar.org/graph/v1/paper/search",
        params=params,
        headers=headers,
    )
    out = []
    for w in r.json().get("data", []) or []:
        ext = w.get("externalIds") or {}
        locators: list[dict] = []
        _add_locator(locators, "pdf", (w.get("openAccessPdf") or {}).get("url"))
        out.append(
            {
                "title": w.get("title") or "",
                "authors": [a.get("name", "") for a in w.get("authors", [])][:12],
                "year": w.get("year"),
                "venue": w.get("venue"),
                "doi": ext.get("DOI"),
                "url": w.get("url"),
                "abstract": w.get("abstract") or "",
                "citations": w.get("citationCount", 0),
                "source": "semanticscholar",
                "oa_status": "oa" if w.get("isOpenAccess") else "unknown",
                "is_retracted": False,
                "fulltext_locators": locators,
            }
        )
    return out


SOURCES = {
    "openalex": search_openalex,
    "arxiv": search_arxiv,
    "crossref": search_crossref,
    "europepmc": search_europepmc,
    "semanticscholar": search_semanticscholar,
}

# ----------------------------------------------------------------------
# Bias scanning — runs automatically after every corpus build
# ----------------------------------------------------------------------

FUNDING_SIGNALS = [
    "funded by", "received funding", "grant from", "honoraria",
    "advisory board", "employee of", "consultant to", "stock holder",
    "founder of", "owns shares", "conflict of interest", "industry funded",
    "pharmaceutical", "supplement company", "nutrition research",
    "biotech", "funded by the author",
]

INSTITUTIONAL_TERMS = [
    "university", "hospital", "medical center", "institute", "college",
    "school of", "pharmaceutical", "nutra", "herb", "biotech", "supplement",
]

NULL_RESULT_SIGNALS = [
    "no benefit", "failed to improve", "not significant", "null result",
    "no difference", "did not reduce", "placebo controlled", "placebo-controlled",
    "negative trial", "no effect",
]

PREDATORY_JOURNALS = [
    "scientific research", "journal of",  # too generic — skip
]


def scan_corpus_for_bias(corpus: list[dict], out_dir: str) -> dict:
    """Run bias scan against a corpus and write bias JSON + markdown reports.

    Returns a dict of summary stats for printing.
    """
    os.makedirs(out_dir, exist_ok=True)

    # --- A. Funding / conflict scan ---
    funded_papers = []
    no_funding_found = []
    no_abstract = 0

    for p in corpus:
        ab = p.get("abstract", "") or ""
        if not ab:
            no_abstract += 1
            continue
        ab_lower = ab.lower()
        matches = [kw for kw in FUNDING_SIGNALS if kw in ab_lower]
        if matches:
            funded_papers.append({
                "title": p.get("title", "")[:100],
                "year": p.get("year"),
                "doi": p.get("doi"),
                "signals": matches,
                "source": p.get("source"),
                "citations": p.get("citations"),
            })
        else:
            no_funding_found.append(p.get("title", "")[:80])

    funding_report = {
        "total_papers": len(corpus),
        "with_funding_signals": len(funded_papers),
        "without_funding_signals": len(no_funding_found),
        "no_abstract": no_abstract,
        "papers": funded_papers,
    }
    with open(os.path.join(out_dir, "bias-funding.json"), "w") as f:
        json.dump(funding_report, f, indent=2, ensure_ascii=False)

    # --- B. Institutional concentration ---
    institution_counts = Counter()
    no_author = 0
    for p in corpus:
        authors = p.get("authors", [])
        if not authors:
            no_author += 1
            continue
        authors_str = " ".join(authors) if isinstance(authors, list) else str(authors)
        found = re.findall(
            r"(University|Hospital|Medical Center|Institute|College|"
            r"School|Pharmaceutical|Nutra|Herb|Biotech|Supplement|Corp|Ltd)",
            authors_str, re.IGNORECASE
        )
        for inst in found:
            institution_counts[inst.lower()] += 1

    total_with_authors = len(corpus) - no_author
    institutional_flags = []
    for inst, count in institution_counts.most_common(20):
        pct = (count / total_with_authors * 100) if total_with_authors else 0
        if pct > 50:
            institutional_flags.append({
                "institution_pattern": inst,
                "count": count,
                "pct": round(pct, 1),
                "flag": "CONCENTRATION >50%",
            })

    institution_report = {
        "total_with_author_data": total_with_authors,
        "top_institutions": [
            {"pattern": inst, "count": cnt, "pct": round(cnt/total_with_authors*100,1) if total_with_authors else 0}
            for inst, cnt in institution_counts.most_common(20)
        ],
        "concentration_flags": institutional_flags,
        "corpus_balanced": len(institutional_flags) == 0,
    }
    with open(os.path.join(out_dir, "bias-institutions.json"), "w") as f:
        json.dump(institution_report, f, indent=2, ensure_ascii=False)

    # --- C. Publication bias (null-result ratio) ---
    total_with_abstract = sum(1 for p in corpus if p.get("abstract"))
    null_papers = []
    for p in corpus:
        ab = (p.get("abstract") or "").lower()
        if not ab:
            continue
        if any(sig in ab for sig in NULL_RESULT_SIGNALS):
            null_papers.append({
                "title": p.get("title", "")[:100],
                "year": p.get("year"),
                "doi": p.get("doi"),
                "source": p.get("source"),
            })

    null_ratio = (len(null_papers) / total_with_abstract * 100) if total_with_abstract else 0
    publication_bias_flag = null_ratio < 5.0

    pub_report = {
        "total_with_abstract": total_with_abstract,
        "null_result_papers": len(null_papers),
        "null_ratio_pct": round(null_ratio, 1),
        "publication_bias_suspected": publication_bias_flag,
        "papers": null_papers[:50],  # cap at 50 for file size
    }
    with open(os.path.join(out_dir, "bias-publication-bias.json"), "w") as f:
        json.dump(pub_report, f, indent=2, ensure_ascii=False)

    # --- D. Bias summary markdown ---
    bias_md = f"""# Bias Scan Summary — {os.path.basename(out_dir)}

Generated automatically by search_papers.py bias scan.

## Funding / Conflict of Interest
- Papers with funding/conflict signals: **{len(funded_papers)}** / {len(corpus)}
- Papers without signals: **{len(no_funding_found)}**
- No abstract available: **{no_abstract}**

## Institutional Concentration
"""
    if institutional_flags:
        bias_md += "**⚠️ FLAGGED** — concentration >50%:\n\n"
        for f2 in institutional_flags:
            bias_md += f"- `{f2['institution_pattern']}`: {f2['count']} papers ({f2['pct']}%)\n"
    else:
        bias_md += "✅ Corpus appears balanced — no single institution >50%\n"

    bias_md += f"""
## Publication Bias
- Null-result papers found: **{len(null_papers)}** / {total_with_abstract} = **{null_ratio:.1f}%**
"""
    if publication_bias_flag:
        bias_md += "**⚠️ FLAGGED** — null-result ratio <5%, publication bias suspected.\n"
    else:
        bias_md += "✅ Null-result papers present — publication bias not strongly suspected.\n"

    bias_md += f"""
## Bias Flags Applied
| Type | Action |
|---|---|
| Industry-funded (for-profit) | Downgrade 1 evidence level |
| Government/academic funding | No penalty |
| Funding not declared | Flag, no penalty |
| Predatory journal / fraud | **Exclude** |
| Institution >50% of corpus | Flag, note imbalance |
| Null ratio <5% | Flag publication bias |

---
*Run bias scan again with: python3 scripts/search_papers.py [queries] --out data/corpus.json*
"""
    with open(os.path.join(out_dir, "bias-summary.md"), "w") as f:
        f.write(bias_md)

    return {
        "funded": len(funded_papers),
        "null_ratio": round(null_ratio, 1),
        "pub_bias_flag": publication_bias_flag,
        "institutional_flags": len(institutional_flags),
    }


def dedupe(papers: list[dict]) -> list[dict]:
    """Merge duplicates across sources, keyed by DOI then normalized title.

    Keeps the record with the richest abstract; unions the source labels and
    keeps the highest citation count seen for the work.
    """
    seen: dict[str, dict] = {}
    for p in papers:
        key = (p.get("doi") or "").lower() or _norm_title(p["title"])
        if not key:
            continue
        if key not in seen:
            p["sources"] = [p["source"]]
            seen[key] = p
            continue
        cur = seen[key]
        if cur["source"] not in cur["sources"]:
            cur["sources"].append(p["source"])
        if len(p.get("abstract") or "") > len(cur.get("abstract") or ""):
            cur["abstract"] = p["abstract"]
        cites = [c for c in (cur.get("citations"), p.get("citations")) if c]
        if cites:
            cur["citations"] = max(cites)
        # Union full-text locators — one source may know a PDF another doesn't.
        for loc in p.get("fulltext_locators", []):
            _add_locator(cur["fulltext_locators"], loc["kind"], loc["url"])
        # Any source calling it open access wins over "closed"/"unknown".
        if p.get("oa_status") == "oa":
            cur["oa_status"] = "oa"
        # Any source flagging a retraction wins — never silently un-retract.
        if p.get("is_retracted"):
            cur["is_retracted"] = True
    # Order each paper's locators best-first: clean structured XML, then PDF
    # (reliably a full document), then HTML last (great for arXiv but often only
    # a thin abstract on publisher landing pages).
    kind_rank = {"xml": 0, "pdf": 1, "html": 2}
    for p in seen.values():
        p["fulltext_locators"].sort(key=lambda loc: kind_rank.get(loc["kind"], 9))
        # Belt-and-suspenders: trust a metadata flag OR a retraction-marked title,
        # so a paper only Crossref returned (no is_retracted field) is still caught.
        p["is_retracted"] = bool(p.get("is_retracted")) or _looks_retracted(p["title"])
    return list(seen.values())


def _add_null_queries(queries: list[str]) -> list[str]:
    """Augment every query with null-result variants to combat publication bias.

    For each original query, adds a variant ANDed with a null-result term so
    the corpus explicitly includes negative-trial results.  The adversarial
    null-result terms are injected into every query string so the bias
    is baked in automatically — the PI doesn't have to remember to do it.
    """
    null_terms = [
        "failed to improve", "no benefit", "not significant",
        "null result", "no difference", "did not reduce",
    ]
    augmented = []
    for q in queries:
        augmented.append(q)
        for nt in null_terms[:3]:  # keep it to 3 to avoid flooding
            augmented.append(f'"{q}" AND "{nt}"')
    return augmented


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("queries", nargs="+",
                    help="one or more search queries; results are merged & deduped")
    ap.add_argument("--out", default="outputs/corpus.json")
    ap.add_argument("--limit", type=int, default=25,
                    help="max results per source")
    ap.add_argument("--since", type=int, default=None,
                    help="earliest publication year")
    ap.add_argument("--sources", default=",".join(SOURCES),
                    help="comma-separated subset of: " + ",".join(SOURCES))
    ap.add_argument("--no-bias-scan", action="store_true",
                    help="skip the post-build bias scan (rare; use for quick checks)")
    args = ap.parse_args()

    # Always add null-result queries to combat publication bias
    all_queries = _add_null_queries(args.queries)

    chosen = [s.strip() for s in args.sources.split(",") if s.strip() in SOURCES]
    all_papers: list[dict] = []
    # Each query hits every chosen source; dedupe() merges the union below, so the
    # PI no longer hand-merges per-query corpus files.
    for qi, query in enumerate(all_queries, 1):
        tag = f"q{qi}" if len(all_queries) > 1 else None
        for name in chosen:
            label = f"{tag}/{name}" if tag else name
            try:
                got = SOURCES[name](query, args.limit, args.since)
                all_papers.extend(got)
                print(f"[{label}] {len(got)} results", file=sys.stderr)
            except Exception as e:  # noqa: BLE001 — one source must not sink the run
                print(f"[{label}] FAILED: {e}", file=sys.stderr)
            time.sleep(0.3)  # be gentle on shared public endpoints

    merged = dedupe(all_papers)
    # Sort by citations desc (None last), then year desc — most-cited recent first.
    merged.sort(
        key=lambda p: (p.get("citations") or -1, p.get("year") or 0),
        reverse=True,
    )

    out_dir = os.path.dirname(args.out) or "."
    os.makedirs(out_dir, exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)

    retracted = sum(1 for p in merged if p.get("is_retracted"))
    print(
        f"\nDONE: {len(merged)} unique papers ({retracted} retracted) from "
        f"{len(chosen)} sources × {len(all_queries)} quer"
        f"{'y' if len(all_queries) == 1 else 'ies'} -> {args.out}",
        file=sys.stderr,
    )

    # --- Automatic bias scan ---
    if not args.no_bias_scan:
        bias_stats = scan_corpus_for_bias(merged, out_dir)
        print(
            f"\nBIAS SCAN: {bias_stats['funded']} funded/conflict papers, "
            f"null-ratio {bias_stats['null_ratio']}% "
            f"{'(⚠️ pub bias suspected)' if bias_stats['pub_bias_flag'] else '(ok)'}, "
            f"{bias_stats['institutional_flags']} concentration flags",
            file=sys.stderr,
        )
        print(f"BIAS REPORT: {os.path.join(out_dir, 'bias-summary.md')}", file=sys.stderr)


if __name__ == "__main__":
    main()
