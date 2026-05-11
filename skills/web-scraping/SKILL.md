---
name: web-scraping
description: >-
  Scrape websites using Playwright for JavaScript-rendered content or
  requests+BeautifulSoup for static HTML. Provides reliable scraping patterns:
  handling pagination, login flows, infinite scroll, rate limiting, anti-bot
  evasion, and data extraction to structured formats (CSV, JSON). Use this skill
  whenever the user says "scrape", "crawl", "extract data from", "get data from
  website", "download all pages", "web scraper", "collect data from", "parse
  HTML", "get all links from", "harvest data", or wants to programmatically
  collect information from any website — including SPAs, paginated tables,
  search results, product catalogs, or API-backed sites. Also trigger when the
  user needs to monitor a page for changes, take screenshots of pages,
  automate browser interactions, or fill/submit forms programmatically.
---

# Web Scraping Skill

A comprehensive guide to scraping websites reliably using Python. Covers both static and dynamic content, with robust patterns for handling the common challenges.

## Quick Reference

| Scenario | Tool | When to use |
|---|---|---|
| Static HTML page | `httpx` + `BeautifulSoup` | No JS rendering needed |
| JS-rendered page | `Playwright` | React/Vue/Angular SPAs |
| API-backed site | Direct API calls | Check Network tab first |
| Multi-page results | `Playwright` pagination loop | Tables, search results |
| Authentication-gated | `Playwright` session | Login flows, cookies |
| CF-protected site | `curl_cffi` + `FlareSolverr` | Cloudflare/bot detection |

## Prerequisites (always verify before starting)

The skill assumes these are available. If not, the user can install them:

```bash
pip install playwright httpx beautifulsoup4 lxml
pip install curl-cffi playwright-stealth
playwright install chromium
```

For Cloudflare challenge pages, also run FlareSolverr (Docker):

```bash
docker run -d --name=flaresolverr -p 8191:8191 ghcr.io/flaresolverr/flaresolverr:latest
```

## Golden Rule: Check Before You Scrape

Before scraping any site, verify:
1. **robots.txt** — Check `https://example.com/robots.txt` for disallowed paths
2. **Terms of Service** — Are they OK with automated access?
3. **Rate limits** — Add delays between requests (`time.sleep(1)` minimum)
4. **Identify yourself** — Always set a descriptive `User-Agent` header

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

If the site has any bot detection, prefer `curl_cffi` instead of `httpx` — it impersonates real browser TLS fingerprints:

```python
from curl_cffi import requests
from bs4 import BeautifulSoup

response = requests.get("https://example.com", impersonate="chrome")
soup = BeautifulSoup(response.text, "lxml")
```

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

## Anti-Bot Evasion

Some sites actively block scrapers. Here are techniques to reduce detection.

> **For sites with Cloudflare challenge pages or advanced bot protection, see the [Handling Cloudflare & Bot Protection](#handling-cloudflare--bot-protection) section below.**

### Manual approach: custom browser context

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=[
            "--disable-blink-features=AutomationControlled",
        ]
    )
    
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        viewport={"width": 1920, "height": 1080},
        locale="en-US",
        timezone_id="America/New_York",
    )
    
    page = context.new_page()
    page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """)
    
    page.goto("https://example.com")
```

### Recommended approach: playwright-stealth library

The `playwright-stealth` package applies a comprehensive set of stealth patches automatically — hiding `navigator.webdriver`, patching `navigator.plugins`, fixing `chrome.runtime`, and more. Prefer this over manual patches.

```python
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

with Stealth().use_sync(sync_playwright()) as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://example.com")
    html = page.content()
    browser.close()
```

Async version:

```python
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def scrape():
    async with Stealth().use_async(async_playwright()) as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://example.com")
        html = await page.content()
        await browser.close()
        return html
```

### Throttling & politeness

```python
import time
import random

# Random delay between requests (1-3 seconds)
time.sleep(random.uniform(1, 3))
```

## Handling Cloudflare & Bot Protection

Sites behind Cloudflare or similar WAF services require specialized handling. Use this decision tree to pick the right approach:

1. **If the site returns 403/503 with a Cloudflare challenge page** → Use the cookie-refresh pattern (recommended)
2. **If `curl_cffi` with impersonation alone works** → Just use `curl_cffi` (simplest)
3. **If basic bot detection but no CF challenge page** → `playwright-stealth` may suffice

### Layer 1 — TLS fingerprint impersonation with curl_cffi

`curl_cffi` is a drop-in replacement for `httpx`/`requests` that impersonates real browser TLS fingerprints. Use it for ALL static requests when bot detection is a concern.

Available impersonation targets: `chrome99`, `chrome100`, `chrome101`, ..., `chrome120`, `chrome131`, `safari15_3`, `safari15_5`, `safari17_0`, `firefox`, `edge99`, and more.

Sync usage:

```python
from curl_cffi import requests

response = requests.get("https://example.com", impersonate="chrome")
print(response.status_code)
print(response.text[:500])
```

Async usage:

```python
import asyncio
from curl_cffi import requests

async def scrape():
    response = await requests.get("https://example.com", impersonate="chrome")
    return response.text

html = asyncio.run(scrape())
```

### Layer 2 — Browser stealth with playwright-stealth

For sites with basic bot detection (but no CF challenge page), `playwright-stealth` patches Playwright to hide automation markers.

```python
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

with Stealth().use_sync(sync_playwright()) as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://example.com")
    html = page.content()
    browser.close()
```

> **Note:** This only handles basic detection. It won't solve Cloudflare challenge pages on its own.

### Layer 3 — FlareSolverr for CF challenge pages

FlareSolverr is a Docker sidecar that solves Cloudflare challenges in a real browser and returns the HTML plus `cf_clearance` cookies.

Start FlareSolverr:

```bash
docker run -d --name=flaresolverr -p 8191:8191 ghcr.io/flaresolverr/flaresolverr:latest
```

Call FlareSolverr from Python:

```python
import httpx

def solve_cf_challenge(url, flaresolverr_url="http://localhost:8191/v1"):
    response = httpx.post(flaresolverr_url, json={
        "cmd": "request.get",
        "url": url,
        "maxTimeout": 60000,
    })
    data = response.json()
    html = data["solution"]["response"]
    cookies = data["solution"]["cookies"]
    return html, cookies
```

> **Limitations:** Slow (~5-10 seconds per request), resource-heavy. Captcha solving may be broken on some CF versions.

### The Cookie-Refresh Pattern (RECOMMENDED)

This is the most effective DIY approach for CF-protected sites:

1. Use FlareSolverr to solve the CF challenge once → get `cf_clearance` cookie
2. Pass that cookie to `curl_cffi` (with matching impersonation) for all subsequent requests
3. When requests start failing again (cookie expired), repeat step 1

```python
from curl_cffi import requests as cffi_requests
import httpx

CF_PROTECTED_URL = "https://example.com"
FLARESOLVERR_URL = "http://localhost:8191/v1"

def get_cf_cookies(url):
    resp = httpx.post(FLARESOLVERR_URL, json={
        "cmd": "request.get",
        "url": url,
        "maxTimeout": 60000,
    })
    return resp.json()["solution"]["cookies"]

def scrape_cf_protected(url):
    cookies = get_cf_cookies(url)
    cookie_dict = {c["name"]: c["value"] for c in cookies}
    
    response = cffi_requests.get(url, 
        impersonate="chrome",
        cookies=cookie_dict
    )
    
    if response.status_code == 403:
        cookies = get_cf_cookies(url)
        cookie_dict = {c["name"]: c["value"] for c in cookies}
        response = cffi_requests.get(url,
            impersonate="chrome",
            cookies=cookie_dict
        )
    
    return response.text
```

### Alternative: DrissionPage

For advanced cases where even the above approaches fail, [DrissionPage](https://github.com/g1879/DrissionPage) uses Chrome DevTools Protocol directly (no WebDriver artifacts = harder to detect).

```bash
pip install DrissionPage
```

> **Note:** DrissionPage documentation is primarily in Chinese.

## Common Pitfalls

| Problem | Solution |
|---|---|
| Page loads but data is empty | Wait for a specific selector: `page.wait_for_selector("div.result")` |
| "We detect you are a bot" | Add anti-bot evasion script + realistic user agent + human-like delays |
| Data appears after user action (click, scroll) | Simulate the action with Playwright before extracting |
| Table has many pages | Loop through pagination, checking for "next" button each time |
| Rate limited (429 status) | Add longer delays, rotate user agents, or use proxies |
| Dynamic class names | Use partial attribute matches: `[class*="price"]` or structural selectors |
| Data is behind a login | Save cookies after login and reuse them |
| Infinite scroll never stops loading | Set a max scroll counter |
| Page uses shadow DOM | Use `page.evaluate()` to pierce shadow roots |
| 403/503 with Cloudflare ray id | Use curl_cffi with `impersonate="chrome"` + FlareSolverr for challenge pages |
| Stuck in CF Turnstile loop | FlareSolverr can solve Turnstile; if not, use a residential proxy |
| CF challenge page in browser | Use playwright-stealth + headful mode (`headless=False`) — CF detects headless |
| cf_clearance cookie expired | Re-solve via FlareSolverr and refresh the cookie |

## When to write a script vs. extract inline

For simple one-off scrapes, extract data inline using the patterns above. For scrapes that:
- Run on a schedule
- Process many pages (100+)
- Need to be resumed after interruption
- Will be reused by others

Write a standalone Python script with command-line arguments, error handling, and progress logging. Bundle it in the `scripts/` directory of this skill if it's a common task.

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
DONE: <output-path> — <N> records scraped to <format>
```
