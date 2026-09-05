---
name: web-scraping
description: >-
  Builds compliant scrapers and datasets with HTTP parsing or Playwright.
  Only use when explicitly requested.
license: MIT
disable-model-invocation: true
metadata:
  author: 0xdewy
  version: 1.1.0
  category: data
  tags:
    - scraping
    - playwright
    - beautifulsoup
    - data-extraction
    - compliance
---

# Web Scraping

Build compliant scrapers and data extractors. Use official APIs when available.

Load `../common/patterns/knowledge.md` for source/compliance rules and `../common/patterns/execution-contract.md` when
writing durable scripts or datasets.

## Safety Gate

Before scraping, check robots/TOS where relevant, rate limits, authentication
permission, data sensitivity, and whether an API is the better route. Refuse
bypass of CAPTCHA, bot defenses, paywalls, geoblocks, access controls, or
robots/TOS restrictions.

## Workflow

1. Define target pages, fields, output format, freshness needs, and allowed
   crawl scope.
2. Choose `httpx`/BeautifulSoup for static HTML; Playwright for JS-rendered or
   interaction-heavy pages.
3. Implement pagination/infinite scroll, retries, rate limits, dedupe, and
   structured output (`csv`, `json`, or `jsonl`).
4. Add screenshots/logging for brittle browser flows.
5. Test on a small sample before full collection.
6. Document run command, limits, and assumptions.

Final line:

```text
DONE: web-scraping — scraper/output ready, sample=<N> records
```
