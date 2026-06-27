# Scrape Compliance Note

- Target: `https://hyperliquid.gitbook.io/hyperliquid-docs` Markdown documentation pages from `llms.txt`
- robots.txt checked: allowed, `https://hyperliquid.gitbook.io/robots.txt` permits `/` and disallows only query search/ask paths
- Terms/source permission: public GitBook docs with explicit `llms.txt` agent index and Markdown page variants
- Rate limit: 0.10s delay between page requests, 145 indexed pages
- User-Agent: `CodexSkillBuilder/1.0 (+https://openai.com; docs reference scrape)`
- Decision: proceed

## robots.txt

```text
User-agent: *
Content-Signal: ai-train=yes, search=yes, ai-input=yes
Disallow: /*?*q=*
Disallow: /*?*ask=*
Allow: /~gitbook/image?*
Allow: /~gitbook/icon?*
Allow: /favicon.ico
Allow: /
Sitemap: https://hyperliquid.gitbook.io/hyperliquid-docs/sitemap.xml
```
