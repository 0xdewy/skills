#!/usr/bin/env python3
"""
Frontend UX Audit Script
Crawls all routes, takes screenshots at 3 viewports, extracts design tokens.

Usage:
  python audit.py <base_url> [--output-dir ./ux-audit] [--routes /a /b /c]
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
except ImportError:
    print("Playwright not installed. Run: pip install playwright && playwright install chromium")
    sys.exit(1)

VIEWPORTS = [
    {"name": "mobile", "width": 375, "height": 812},
    {"name": "tablet", "width": 768, "height": 1024},
    {"name": "desktop", "width": 1280, "height": 800},
]


def discover_routes(page, base_url: str) -> list[str]:
    """Crawl navigation links to discover all routes."""
    routes = set(["/"])
    try:
        page.goto(base_url, wait_until="networkidle", timeout=15000)
        links = page.evaluate("""() => {
            return [...document.querySelectorAll('a[href]')]
                .map(a => a.getAttribute('href'))
                .filter(h => h && h.startsWith('/') && !h.startsWith('//'))
                .filter(h => !h.match(/\\.(png|jpg|svg|ico|css|js|json|pdf|woff)$/i));
        }""")
        for link in links:
            # Strip query strings and hashes from discovered links
            clean = link.split("?")[0].split("#")[0]
            if clean:
                routes.add(clean)
    except PWTimeout:
        print(f"Timeout loading {base_url} during route discovery")
    return sorted(routes)


def extract_design_tokens(page) -> dict:
    """Extract computed CSS design tokens from the live DOM."""
    return page.evaluate("""() => {
        const seen = {
            fontFamilies: new Set(),
            fontSizes: new Set(),
            fontWeights: new Set(),
            colors: new Set(),
            backgroundColors: new Set(),
            borderColors: new Set(),
            spacingValues: new Set(),
            borderRadii: new Set(),
            boxShadows: new Set(),
        };

        const elements = document.querySelectorAll('*');
        elements.forEach(el => {
            const rect = el.getBoundingClientRect();
            if (rect.width === 0 || rect.height === 0) return;

            const s = window.getComputedStyle(el);

            const ff = s.fontFamily.split(',')[0].trim().replace(/['"]/g, '');
            if (ff) seen.fontFamilies.add(ff);

            const fs = parseFloat(s.fontSize);
            if (fs > 0) seen.fontSizes.add(fs);

            seen.fontWeights.add(s.fontWeight);

            const color = s.color;
            if (color && color !== 'rgba(0, 0, 0, 0)') seen.colors.add(color);

            const bg = s.backgroundColor;
            if (bg && bg !== 'rgba(0, 0, 0, 0)') seen.backgroundColors.add(bg);

            const bc = s.borderColor;
            if (bc && bc !== 'rgba(0, 0, 0, 0)') seen.borderColors.add(bc);

            ['marginTop','marginBottom','marginLeft','marginRight',
             'paddingTop','paddingBottom','paddingLeft','paddingRight',
             'gap','rowGap','columnGap'].forEach(p => {
                const v = parseFloat(s[p]);
                if (v > 0 && v < 300) seen.spacingValues.add(v);
            });

            const br = parseFloat(s.borderRadius);
            if (br > 0) seen.borderRadii.add(br);

            const bs = s.boxShadow;
            if (bs && bs !== 'none') seen.boxShadows.add(bs);
        });

        const sortNum = arr => [...arr].sort((a, b) => a - b);

        return {
            fontFamilies: [...seen.fontFamilies],
            fontSizes: sortNum(seen.fontSizes),
            fontWeights: [...seen.fontWeights].sort(),
            colors: [...seen.colors],
            backgroundColors: [...seen.backgroundColors],
            borderColors: [...seen.borderColors],
            spacingValues: sortNum(seen.spacingValues),
            borderRadii: sortNum(seen.borderRadii),
            boxShadows: [...seen.boxShadows],
        };
    }""")


def check_overflow(page, viewport_width: int) -> list[dict]:
    """Find elements that overflow horizontally outside the viewport."""
    return page.evaluate(f"""() => {{
        const vw = {viewport_width};
        const issues = [];
        document.querySelectorAll('*').forEach(el => {{
            const rect = el.getBoundingClientRect();
            if (rect.right > vw + 2 && rect.width < vw * 2) {{
                const s = window.getComputedStyle(el);
                issues.push({{
                    tag: el.tagName,
                    class: el.className.toString().slice(0, 60),
                    right: Math.round(rect.right),
                    overflow: Math.round(rect.right - vw),
                }});
            }}
        }});
        return issues.slice(0, 8);
    }}""")


def check_alignment(page) -> list[dict]:
    """Find inline elements in the same visual row with inconsistent top alignment."""
    return page.evaluate("""() => {
        const els = [...document.querySelectorAll(
            'h1,h2,h3,h4,h5,h6,p,button,a,li,label,input,span,td,th'
        )].filter(el => {
            const r = el.getBoundingClientRect();
            return r.width > 20 && r.height > 4 && r.top > 0;
        });

        // Group by approximate row (bucket top to nearest 8px)
        const rows = {};
        els.forEach(el => {
            const r = el.getBoundingClientRect();
            const bucket = Math.round(r.top / 8) * 8;
            if (!rows[bucket]) rows[bucket] = [];
            rows[bucket].push({ tag: el.tagName, top: r.top, height: r.height,
                text: el.textContent.trim().slice(0, 25) });
        });

        const issues = [];
        Object.entries(rows).forEach(([bucket, items]) => {
            if (items.length < 2) return;
            const tops = items.map(i => i.top);
            const spread = Math.max(...tops) - Math.min(...tops);
            if (spread > 5) {
                issues.push({ rowY: parseInt(bucket), spread: Math.round(spread),
                    items: items.slice(0, 3) });
            }
        });
        return issues.slice(0, 6);
    }""")


def check_touch_targets(page) -> list[dict]:
    """Find interactive elements below 44x44px (WCAG 2.5.5)."""
    return page.evaluate("""() => {
        const issues = [];
        document.querySelectorAll(
            'button, a, input, select, textarea, [role="button"], [role="link"]'
        ).forEach(el => {
            const r = el.getBoundingClientRect();
            if (r.width === 0 || r.height === 0) return;
            if (r.width < 44 || r.height < 44) {
                issues.push({
                    tag: el.tagName,
                    label: (el.textContent || el.getAttribute('aria-label') || '').trim().slice(0, 30),
                    width: Math.round(r.width),
                    height: Math.round(r.height),
                });
            }
        });
        return issues.slice(0, 10);
    }""")


def check_z_index_soup(page) -> list[dict]:
    """Find z-index values that suggest layering chaos."""
    return page.evaluate("""() => {
        const zValues = new Set();
        document.querySelectorAll('*').forEach(el => {
            const z = window.getComputedStyle(el).zIndex;
            if (z !== 'auto' && !isNaN(parseInt(z))) {
                zValues.add(parseInt(z));
            }
        });
        const sorted = [...zValues].sort((a, b) => a - b);
        return { values: sorted, count: sorted.length };
    }""")


def audit_route(page, base_url: str, route: str, output_dir: Path) -> dict:
    """Audit a single route across all viewports."""
    url = urljoin(base_url, route)
    route_slug = route.strip("/").replace("/", "_") or "home"
    findings = {"route": route, "url": url, "viewports": {}}

    for vp in VIEWPORTS:
        page.set_viewport_size({"width": vp["width"], "height": vp["height"]})
        try:
            page.goto(url, wait_until="networkidle", timeout=15000)
            page.wait_for_timeout(500)
        except PWTimeout:
            findings["viewports"][vp["name"]] = {"error": "timeout"}
            continue

        shot_name = f"{route_slug}_{vp['name']}.png"
        shot_path = output_dir / "screenshots" / shot_name
        page.screenshot(path=str(shot_path), full_page=True)

        vp_data = {
            "screenshot": str(shot_path.relative_to(output_dir.parent)),
            "overflowIssues": check_overflow(page, vp["width"]),
            "touchTargetIssues": check_touch_targets(page) if vp["name"] == "mobile" else [],
        }

        if vp["name"] == "desktop":
            vp_data["alignmentIssues"] = check_alignment(page)
            vp_data["zIndexAnalysis"] = check_z_index_soup(page)
            vp_data["designTokens"] = extract_design_tokens(page)

        findings["viewports"][vp["name"]] = vp_data

    return findings


def merge_tokens(all_findings: list[dict]) -> dict:
    """Aggregate design tokens across all routes into a single picture."""
    merged = {
        "fontFamilies": set(),
        "fontSizes": set(),
        "fontWeights": set(),
        "colors": set(),
        "backgroundColors": set(),
        "spacingValues": set(),
        "borderRadii": set(),
    }

    for f in all_findings:
        tokens = f.get("viewports", {}).get("desktop", {}).get("designTokens", {})
        for key in merged:
            merged[key].update(tokens.get(key, []))

    def sortnum(s):
        try:
            return sorted(s, key=float)
        except (ValueError, TypeError):
            return sorted(s)

    return {k: sortnum(v) for k, v in merged.items()}


def analyze_tokens(tokens: dict) -> dict:
    """Produce a simple health verdict for each token dimension."""
    spacing = [v for v in tokens["spacingValues"] if isinstance(v, (int, float))]

    def on_grid(vals, step=4):
        return all(v % step < 1.5 for v in vals if v > 0)

    return {
        "fontFamilies": {
            "count": len(tokens["fontFamilies"]),
            "health": "good" if len(tokens["fontFamilies"]) <= 2 else "warning" if len(tokens["fontFamilies"]) <= 3 else "bad",
        },
        "fontSizes": {
            "count": len(tokens["fontSizes"]),
            "health": "good" if len(tokens["fontSizes"]) <= 8 else "warning" if len(tokens["fontSizes"]) <= 12 else "bad",
        },
        "colors": {
            "textCount": len(tokens["colors"]),
            "bgCount": len(tokens["backgroundColors"]),
            "health": "good" if len(tokens["backgroundColors"]) <= 8 else "warning" if len(tokens["backgroundColors"]) <= 14 else "bad",
        },
        "spacing": {
            "count": len(spacing),
            "onGrid": on_grid(spacing),
            "health": "good" if (len(spacing) <= 10 and on_grid(spacing)) else "warning" if len(spacing) <= 14 else "bad",
        },
        "borderRadii": {
            "count": len(tokens["borderRadii"]),
            "health": "good" if len(tokens["borderRadii"]) <= 4 else "warning" if len(tokens["borderRadii"]) <= 6 else "bad",
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("base_url", help="Base URL of the running app (e.g. http://localhost:3000)")
    parser.add_argument("--output-dir", default="./ux-audit", help="Where to write screenshots and report")
    parser.add_argument("--routes", nargs="*", help="Specific routes to audit (default: auto-discover)")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    output_dir = Path(args.output_dir)
    (output_dir / "screenshots").mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="en-US",
        )
        page = context.new_page()
        page.on("console", lambda msg: None)  # suppress noise

        print("Discovering routes...")
        if args.routes:
            routes = args.routes
        else:
            routes = discover_routes(page, base_url)
        print(f"Found {len(routes)} route(s): {routes}")

        all_findings = []
        for route in routes:
            print(f"  Auditing {route}...")
            findings = audit_route(page, base_url, route, output_dir)
            all_findings.append(findings)

        browser.close()

    tokens = merge_tokens(all_findings)
    analysis = analyze_tokens(tokens)

    report = {
        "baseUrl": base_url,
        "routesAudited": routes,
        "aggregatedTokens": tokens,
        "tokenHealth": analysis,
        "routes": all_findings,
    }

    report_path = output_dir / "report.json"
    report_path.write_text(json.dumps(report, indent=2))
    print(f"\nAudit complete.")
    print(f"  Report: {report_path}")
    print(f"  Screenshots: {output_dir / 'screenshots'}/")
    print(f"  Token health: {json.dumps(analysis, indent=2)}")
    print(f"DONE: audit written to {report_path}")


if __name__ == "__main__":
    main()
