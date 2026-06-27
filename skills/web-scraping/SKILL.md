---
name: web-scraping
description: >-
  Builds compliant website scrapers with Playwright for JS-rendered pages or
  httpx/BeautifulSoup for static HTML, including pagination, login with permission,
  infinite scroll, rate limits, robots/TOS checks, screenshots, monitoring, and
  CSV/JSON/JSONL output. TRIGGER on: "scrape", "crawl", "extract data from",
  "get data from website", "download all pages", "web scraper", "collect data
  from", "parse HTML", "get all links", "harvest data", browser automation, or
  programmatic form submission. SKIP on: one-off browsing, factual lookups,
  official API/SDK tasks, and requests to bypass CAPTCHA, bot defenses, paywalls,
  geoblocks, access controls, robots.txt, or ToS restrictions.
license: MIT
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

# Web Scraping Skill

A comprehensive guide to scraping websites reliably using Python. Covers both static and dynamic content, with robust patterns for handling the common challenges.

Load `skills/common/patterns/knowledge.md` for source hierarchy, freshness, and
compliance-before-collection rules. Load
`skills/common/patterns/execution-contract.md` when writing a scraper or durable
dataset.

## Quick Reference

| Scenario | Tool | When to use |
|---|---|---|
| Static HTML page | `httpx` + `BeautifulSoup` | No JS rendering needed |
| JS-rendered page | `Playwright` | React/Vue/Angular SPAs |
| API-backed site | Direct API calls | Check Network tab first |
| Multi-page results | `Playwright` pagination loop | Tables, search results |
| Authentication-gated | `Playwright` session | Login flows, cookies |
| Access-controlled or bot-challenged site | Stop and seek permission/API/export | Do not bypass defenses |

## Prerequisites (always verify before starting)

The skill assumes these are available. If not, the user can install them:

```bash
pip install playwright httpx beautifulsoup4 lxml
playwright install chromium
```

## Golden Rule: Check Before You Scrape

Before scraping any site, verify:
1. **robots.txt** — Check `https://example.com/robots.txt` for disallowed paths
2. **Terms of Service** — Are they OK with automated access?
3. **Rate limits** — Add delays between requests (`time.sleep(1)` minimum)
4. **Identify yourself** — Always set a descriptive `User-Agent` header

Write the result of this check before collecting data:

```markdown
## Scrape Compliance Note
- Target: <domain and paths>
- robots.txt checked: <allowed|disallowed|unavailable, with URL>
- Terms/source permission: <allowed|unclear|disallowed, with URL or note>
- Rate limit: <delay and max pages>
- User-Agent: <string>
- Decision: <proceed|stop and use alternative>
```

If the decision is `stop`, do not write scraper code for that target. Offer a
compliant alternative instead.

If the site presents CAPTCHA, Cloudflare/browser integrity checks, paywalls,
explicit bot blocks, geoblocks, or other access controls, stop. Recommend an
official API, data export, written permission, or user-provided data instead of
trying to bypass the control.

## Approach: Prefer Static, Fall Back to Dynamic

Most data on the web can be extracted from the initial HTML response without running JavaScript. Static extraction is faster, more reliable, and uses fewer resources. Only reach for Playwright when you need JS execution.

### Step 1: Check if the page loads data statically

```python
import httpx
from bs4 import BeautifulSoup

response = httpx.get("https://example.com", headers={
    "User-Agent": "Mozilla/5.0 (compatible; ResearchScraper/1.0; +https://example.com/bot)"
})
soup = BeautifulSoup(response.text, "lxml")
```

If the site blocks automated access, do not switch to impersonation libraries.
Use an official API/export or ask the site owner for permission.

If the data you need is in `soup`, you're done. No browser needed.

### Step 2: If the data isn't in the HTML, check the Network API

When data renders via JS, the site almost always fetches it from an internal API. Open DevTools → Network tab → Fetch/XHR, reload the page, and look for JSON responses. These APIs are often simpler to call than rendering the full page.

```python
# If you find an API endpoint in the Network tab, call it directly
import httpx
api_data = httpx.get("https://example.com/api/data", headers={
    "Accept": "application/json"
}).json()
```

### Step 3: Use Playwright for JS-rendered pages only when needed

```python
from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://example.com", wait_until="networkidle")
    
    # Wait for specific content to appear
    page.wait_for_selector("div.content")
    
    html = page.content()
    soup = BeautifulSoup(html, "lxml")
    # ... extract data from soup ...
    
    browser.close()
```

## Reliable Extraction Patterns

### Extracting structured data from HTML

```python
import httpx
from bs4 import BeautifulSoup
import csv, json

response = httpx.get("https://example.com/items")
soup = BeautifulSoup(response.text, "lxml")

results = []
for item in soup.select("div.item"):
    results.append({
        "title": item.select_one("h2.title").get_text(strip=True) if item.select_one("h2.title") else None,
        "price": item.select_one("span.price").get_text(strip=True) if item.select_one("span.price") else None,
        "link": item.select_one("a")["href"] if item.select_one("a") else None,
    })

# Save as JSON
with open("output.json", "w") as f:
    json.dump(results, f, indent=2)

# Save as CSV
with open("output.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=results[0].keys())
    writer.writeheader()
    writer.writerows(results)
```

### Handling pagination

```python
from playwright.sync_api import sync_playwright
import time

all_results = []
base_url = "https://example.com/items?page="

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    page_num = 1
    while True:
        page.goto(f"{base_url}{page_num}", wait_until="networkidle")
        page.wait_for_selector("div.item")
        
        items = page.query_selector_all("div.item")
        if not items:
            break
        
        for item in items:
            all_results.append({
                "title": item.inner_text(),
            })
        
        # Check for "next" button
        next_btn = page.query_selector("a.next")
        if not next_btn:
            break
        
        page_num += 1
        time.sleep(1)  # Be polite
    
    browser.close()
```

### Handling infinite scroll

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://example.com/infinite-scroll")
    
    # Scroll to bottom repeatedly until no new content loads
    prev_height = 0
    for _ in range(50):  # safety limit
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2000)  # wait for content to load
        new_height = page.evaluate("document.body.scrollHeight")
        if new_height == prev_height:
            break
        prev_height = new_height
    
    html = page.content()
    # ... parse with BeautifulSoup ...
```

### Handling login flows

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://example.com/login")
    
    page.fill("input[name='email']", "user@example.com")
    page.fill("input[name='password']", "password123")
    page.click("button[type='submit']")
    page.wait_for_url("https://example.com/dashboard")
    
    # Save cookies for reuse
    cookies = page.context.cookies()
    
    # Now scrape authenticated pages
    page.goto("https://example.com/protected-data")
    # ... extract ...
```

### Saving cookies for reuse across sessions

```python
import json

# After login
cookies = page.context.cookies()
with open("session_cookies.json", "w") as f:
    json.dump(cookies, f)

# Next session: restore cookies
with open("session_cookies.json") as f:
    cookies = json.load(f)
page.context.add_cookies(cookies)
page.goto("https://example.com/protected-data")
```

## Access Blocks and Bot Defenses

If a site actively blocks automation, presents a CAPTCHA/challenge page, requires
paywalled access, or says automated collection is disallowed, stop the scraping
workflow. Do not provide bypass code, stealth patches, TLS/browser impersonation,
challenge solvers, proxy rotation, or residential proxy advice.

Use one of these compliant alternatives:

1. Official API, export, sitemap, RSS feed, bulk download, or dataset.
2. Written permission from the site owner with an agreed rate limit and user agent.
3. User-provided files, screenshots, or manually exported data.
4. A reduced workflow that only captures pages the user owns or is authorized to
   automate.

If the user explicitly asks to bypass a block, refuse that part and offer the
alternatives above.

### Throttling & politeness

```python
import time
import random

# Random delay between requests (1-3 seconds)
time.sleep(random.uniform(1, 3))
```

## Common Pitfalls

| Problem | Solution |
|---|---|
| Page loads but data is empty | Wait for a specific selector: `page.wait_for_selector("div.result")` |
| "We detect you are a bot" | Stop and use an official API/export or request permission |
| Data appears after user action (click, scroll) | Simulate the action with Playwright before extracting |
| Table has many pages | Loop through pagination, checking for "next" button each time |
| Rate limited (429 status) | Slow down, reduce scope, or stop and request permission |
| Dynamic class names | Use partial attribute matches: `[class*="price"]` or structural selectors |
| Data is behind a login | Save cookies after login and reuse them |
| Infinite scroll never stops loading | Set a max scroll counter |
| Page uses shadow DOM | Use `page.evaluate()` to pierce shadow roots |
| 403/503 with WAF/challenge page | Stop and use an official API/export or request permission |

## When to write a script vs. extract inline

For simple one-off scrapes, extract data inline using the patterns above. For scrapes that:
- Run on a schedule
- Process many pages (100+)
- Need to be resumed after interruption
- Will be reused by others

Write a standalone Python script with command-line arguments, error handling, and progress logging. Bundle it in the `scripts/` directory of this skill if it's a common task.

Standalone scripts must include:
- CLI arguments for target URL/path, output path, max pages, and delay.
- Resume behavior: skip already-written records by stable ID or URL.
- Structured output: JSONL for streaming/resumable scrapes, CSV only when the
  schema is flat and stable.
- A final validation step that prints record count, required fields present, and
  duplicate count.
- A dry-run mode that fetches one page and prints the inferred schema without
  writing the full dataset.

For reusable scripts, write a companion README or top-of-file usage block with
the compliance note, run command, expected output schema, and known limitations.

## Debugging Tips

1. **Take a screenshot** to see what the browser actually rendered:
   ```python
   page.screenshot(path="debug.png")
   ```
2. **Save the HTML** to inspect the DOM:
   ```python
   with open("page.html", "w") as f:
       f.write(page.content())
   ```
3. **Check console errors**:
   ```python
   page.on("console", lambda msg: print(f"CONSOLE: {msg.text}"))
   ```
4. **Check network requests** to find API calls:
   ```python
   page.on("response", lambda resp: print(f"RESP: {resp.url}") if resp.status == 200 else None)
   ```

## Completion

End your final message with a parseable completion line:

```
DONE: <output-path> — <N> records scraped to <format>, <D> duplicates, compliance <proceed|stopped>
```
