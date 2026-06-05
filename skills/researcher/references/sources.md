# Scientific Literature Sources

`scripts/search_papers.py` queries these publicly available, key-less APIs and
normalizes the results into one schema. Read this when a search underperforms,
when you need to choose a source subset (`--sources`), or when adding a source.

| Source | Coverage | Strengths | Notes |
|---|---|---|---|
| **OpenAlex** | ~250M works, all fields | Best general default; citation counts, abstracts (inverted index), open metadata | "Polite pool" via `mailto`. Most reliable. |
| **arXiv** | Physics, math, CS, quant-bio, econ preprints | Cutting-edge preprints before peer review | Atom XML API. No citation counts. No DOIs for many entries. |
| **Crossref** | ~150M DOIs, all publishers | Authoritative DOI/metadata of record | Abstracts often missing or JATS-XML; citation counts are referenced-by. |
| **Europe PMC** | Biomedical & life sciences | Full abstracts, PubMed + preprints, MeSH | Use for medicine/biology. Supports `PUB_YEAR` filters. |
| **Semantic Scholar** | ~200M papers, all fields | Strong abstracts, citation graph, influential-citation data | Aggressively rate-limited without an API key (429s common). Set `SEMANTIC_SCHOLAR_API_KEY` to use it reliably; the script also retries with backoff and degrades gracefully when a source still fails. |

## Choosing sources

- **General / interdisciplinary** → default (all five). OpenAlex + Crossref form
  the backbone; the others fill gaps.
- **Biomedical / clinical** → prioritize `europepmc,openalex,crossref`.
- **CS / physics / math** → prioritize `arxiv,semanticscholar,openalex`.
- **Need citation impact** → OpenAlex and Semantic Scholar carry the best counts;
  results are sorted by citations descending so high-impact work surfaces first.

## Query craft

The corpus quality caps the entire inquiry, so spend effort here:

- Run **multiple queries** with synonyms and competing terms, not one. Pass them
  as several arguments in a single `search_papers.py` call — it runs each against
  every source and merges/dedupes them into one corpus for you.
- Include mechanism terms, not just the phenomenon ("intermittent fasting"
  *and* "time-restricted eating" *and* "insulin sensitivity").
- **Always include at least one adversarial query** — the terms a contrarian
  would use, or ones targeting null/negative/no-effect results — so the corpus
  isn't one-sided. This is required, not optional: a citation-sorted corpus skews
  toward popular positive findings, and the Falsifier in Phase 3 needs real
  disconfirming material to work with.
- Use `--since` to control recency by field clock-speed; omit for settled areas.

## Full-text retrieval

The search step records, per paper, an `oa_status` and an ordered list of
`fulltext_locators`. `scripts/fetch_fulltext.py` consumes these to download and
extract full documents for a targeted subset (the papers under test):

- **Open access only.** Locators come from arXiv (`/html/`, `/pdf/`), OpenAlex
  `best_oa_location`, Europe PMC's advertised OA full-text URLs, and Semantic
  Scholar `openAccessPdf`. When those run out, the fetcher falls back to
  **Unpaywall** (`api.unpaywall.org`), which resolves a DOI to any legal OA copy
  known anywhere — frequently rescuing papers Crossref reported with no locator,
  or whose publisher OA PDF is bot-blocked, by pointing at a repository mirror
  (PMC, institutional, DOAJ). Repository copies are tried before publisher copies
  for exactly that reason — some publishers (e.g. MDPI) return `403` on their own
  OA PDFs to non-browser clients. A paper with no OA copy *anywhere* stays
  `abstract_only` — the inquiry never pretends to have read what it couldn't.
- **Unpaywall needs a real contact email.** Its API rejects placeholder addresses
  (`example.com` → HTTP 422), so the fallback is **only used when
  `RESEARCHER_MAILTO` is set** to a real email; otherwise it is skipped with a
  one-line stderr note and the run proceeds on the built-in locators. The same env
  var feeds the OpenAlex/Crossref polite pool in `search_papers.py`. Export it
  before a run: `export RESEARCHER_MAILTO=you@domain`.
- **Priority xml → pdf → html.** Clean JATS XML is best; PDF (via `pypdf`) is a
  reliable full document; HTML is last because it is excellent for arXiv but
  often only a thin abstract on publisher landing pages. The fetcher falls
  through to the next locator when one yields too little text
  (`< MIN_FULLTEXT_CHARS`), so a thin landing page doesn't masquerade as full text.
- **Manifest.** Each run writes `manifest.json` mapping every requested paper to
  `full_text` / `abstract_only` / `failed` plus the local path. Testing agents
  read it to decide whether to open the full text or fall back to the abstract.
- **No new dependencies / lossy PDF.** Extraction uses installed `pypdf`, `bs4`,
  and `lxml`. PDF text extraction is lossy (columns, equations, tables garble) —
  prefer XML/HTML when both exist, and don't quote tables/figures from a PDF.

## Retraction flag

Each paper carries an `is_retracted` boolean. It is populated from **OpenAlex**'s
`is_retracted` field (the authoritative signal) **and** a title heuristic that
catches the standard retraction markers publishers prepend (`RETRACTED:`,
`RETRACTED ARTICLE:`, `Retraction—…`, `(Retracted)`). The heuristic matters because
a retracted paper can reach the corpus via a source with no retraction field
(e.g. Crossref) — the famous Wakefield MMR paper is exactly this case. Both signals
are unioned across sources in `dedupe()`; if any flags a work retracted, it stays
flagged, and the build summary reports the retracted count. Retracted papers are **kept** in the corpus
(they may legitimately appear as withdrawn/refuted claims) but must never be cited
as *support* — see the agent prompts and the SKILL.md rule. Honest limitation:
coverage is only as complete as OpenAlex's retraction metadata, so absence of the
flag is not proof a paper is sound.

## Limits & honesty

- Full text is **open-access only**; behind paywalls the inquiry reasons from
  abstracts + citation signals. Weight abstract-only evidence lower and say so
  when the question hinges on methodological detail buried in a paper's body.
- Coverage skews English-language and toward indexed journals; grey literature
  and non-indexed work are under-represented. Note this if relevant to the topic.
- Rate limits and transient network errors are expected; the script reports
  per-source success/failure to stderr and continues. If a key source failed,
  re-run that source alone before drawing conclusions.
