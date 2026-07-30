# Web Scraping Code Patterns

Load this file when writing scraper code. The parent `SKILL.md` holds the
compliance rules, decision tables, and completion contract — read those first.

## Approach: Prefer Static, Fall Back to Dynamic

Most data on the web can be extracted from the initial HTML response without
running JavaScript. Static extraction is faster, more reliable, and uses fewer
resources. Only reach for Playwright when you need JS execution.

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

When data renders via JS, the site almost always fetches it from an internal API.
Open DevTools → Network tab → Fetch/XHR, reload the page, and look for JSON
responses. These APIs are often simpler to call than rendering the full page.

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

### Throttling & politeness

```python
import time
import random

# Random delay between requests (1-3 seconds)
time.sleep(random.uniform(1, 3))
```

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
