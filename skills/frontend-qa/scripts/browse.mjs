#!/usr/bin/env node
// Headless-browser helper for the frontend-qa skill. No project dependencies:
// it uses the project's Playwright when installed, else the global `playwright`
// CLI's package.
//
//   node browse.mjs audit <baseUrl> [--out DIR] [--routes /a /b] [--viewports mobile,desktop]
//   node browse.mjs run <flow.mjs> --base <baseUrl> [--out DIR] [--viewport desktop]
//
// audit: loads each route at each viewport; saves a full-page screenshot and
//   records console errors, page errors, failed and 4xx+ requests, horizontal
//   overflow, broken images, small touch targets (mobile) and computed design
//   tokens (desktop). Writes <out>/audit.json and prints a summary.
// run: imports flow.mjs and awaits its default export `(page, t)`, where
//   t = { base, out, snap(name) }. Records the same events, screenshots on
//   failure, writes <out>/<flow>.json, exits 1 when the flow throws or a page
//   error occurred.

import { createRequire } from 'node:module';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const VIEWPORTS = {
  mobile: { width: 375, height: 812 },
  tablet: { width: 768, height: 1024 },
  desktop: { width: 1280, height: 800 },
};
const ASSET_RE = /\.(png|jpe?g|gif|svg|ico|css|js|mjs|json|pdf|woff2?|ttf|mp4|webm|zip)$/i;

function loadPlaywright() {
  const candidates = [createRequire(path.join(process.cwd(), 'x.js'))];
  try {
    const bin = fs.realpathSync(execFileSync('which', ['playwright']).toString().trim());
    candidates.push(createRequire(bin));
  } catch {}
  for (const req of candidates) {
    for (const name of ['playwright', '@playwright/test', 'playwright-core']) {
      try { return req(name); } catch {}
    }
  }
  throw new Error(
    'Playwright not found. Run `npm i -g playwright && playwright install chromium` ' +
    '(or install it in the project), then retry.',
  );
}

function parseArgs(argv) {
  const args = { _: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (!a.startsWith('--')) { args._.push(a); continue; }
    const key = a.slice(2);
    const vals = [];
    while (i + 1 < argv.length && !argv[i + 1].startsWith('--')) vals.push(argv[++i]);
    args[key] = vals.length === 0 ? true : vals.length === 1 ? vals[0] : vals;
  }
  return args;
}

function record(page, events) {
  page.on('console', (m) => {
    if (m.type() === 'error' || m.type() === 'warning') {
      events.push({ kind: 'console', level: m.type(), text: m.text(), page: page.url() });
    }
  });
  page.on('pageerror', (e) => events.push({ kind: 'pageerror', text: String(e), page: page.url() }));
  page.on('requestfailed', (r) => events.push({
    kind: 'requestfailed', method: r.method(), url: r.url(), error: r.failure()?.errorText,
  }));
  page.on('response', (r) => {
    if (r.status() >= 400) {
      events.push({ kind: 'http', status: r.status(), method: r.request().method(), url: r.url() });
    }
  });
}

async function withBrowser(fn) {
  const pw = loadPlaywright();
  const browser = await pw.chromium.launch({ headless: true });
  try { return await fn(browser); } finally { await browser.close(); }
}

const slug = (s) => (s.replace(/^\/+|\/+$/g, '').replace(/[^a-z0-9]+/gi, '-') || 'home').toLowerCase();

// ---- audit -----------------------------------------------------------------

async function discoverRoutes(page, base) {
  await page.goto(base, { waitUntil: 'networkidle', timeout: 20000 });
  const origin = new URL(base).origin;
  const hrefs = await page.$$eval('a[href]', (as) => as.map((a) => a.href));
  const routes = new Set(['/']);
  for (const h of hrefs) {
    let u; try { u = new URL(h); } catch { continue; }
    if (u.origin !== origin || ASSET_RE.test(u.pathname)) continue;
    routes.add(u.pathname || '/');
    if (routes.size >= 30) break;
  }
  return [...routes].sort();
}

const CHECKS = {
  overflow: () => {
    const vw = document.documentElement.clientWidth;
    if (document.documentElement.scrollWidth <= vw + 1) return [];
    return [...document.querySelectorAll('body *')]
      .map((el) => ({ el, r: el.getBoundingClientRect() }))
      .filter(({ r }) => r.width > 0 && r.right > vw + 2 && r.width < vw * 3)
      .slice(0, 8)
      .map(({ el, r }) => ({
        tag: el.tagName.toLowerCase(), class: String(el.className).slice(0, 60),
        overflowPx: Math.round(r.right - vw),
      }));
  },
  brokenImages: () => [...document.images]
    .filter((img) => img.complete && img.naturalWidth === 0 && img.getAttribute('src'))
    .slice(0, 10).map((img) => img.getAttribute('src')),
  touchTargets: () => [...document.querySelectorAll('a[href],button,input,select,textarea,[role=button]')]
    .map((el) => ({ el, r: el.getBoundingClientRect() }))
    .filter(({ el, r }) => r.width > 0 && r.height > 0 && (r.width < 24 || r.height < 24)
      && !(el.tagName === 'A' && getComputedStyle(el).display === 'inline'))
    .slice(0, 10)
    .map(({ el, r }) => ({
      tag: el.tagName.toLowerCase(),
      label: (el.textContent || el.getAttribute('aria-label') || '').trim().slice(0, 30),
      w: Math.round(r.width), h: Math.round(r.height),
    })),
  tokens: () => {
    const sets = { fontFamilies: new Set(), fontSizes: new Set(), fontWeights: new Set(),
      textColors: new Set(), backgroundColors: new Set(), spacing: new Set(), radii: new Set() };
    const props = ['marginTop', 'marginBottom', 'marginLeft', 'marginRight', 'paddingTop',
      'paddingBottom', 'paddingLeft', 'paddingRight', 'gap', 'rowGap', 'columnGap'];
    for (const el of document.querySelectorAll('body *')) {
      const r = el.getBoundingClientRect();
      if (r.width === 0 || r.height === 0) continue;
      const s = getComputedStyle(el);
      sets.fontFamilies.add(s.fontFamily.split(',')[0].trim().replace(/['"]/g, ''));
      sets.fontSizes.add(parseFloat(s.fontSize));
      sets.fontWeights.add(s.fontWeight);
      if (s.color !== 'rgba(0, 0, 0, 0)') sets.textColors.add(s.color);
      if (s.backgroundColor !== 'rgba(0, 0, 0, 0)') sets.backgroundColors.add(s.backgroundColor);
      for (const p of props) { const v = parseFloat(s[p]); if (v > 0 && v < 300) sets.spacing.add(v); }
      const br = parseFloat(s.borderRadius); if (br > 0) sets.radii.add(br);
    }
    const num = (set) => [...set].sort((a, b) => a - b);
    return {
      fontFamilies: [...sets.fontFamilies], fontSizes: num(sets.fontSizes),
      fontWeights: [...sets.fontWeights].sort(), textColors: [...sets.textColors],
      backgroundColors: [...sets.backgroundColors], spacing: num(sets.spacing), radii: num(sets.radii),
    };
  },
};

async function audit(args) {
  const base = args._[1]?.replace(/\/+$/, '');
  if (!base) throw new Error('usage: browse.mjs audit <baseUrl> [--out DIR] [--routes ...] [--viewports a,b]');
  const out = path.resolve(args.out || 'audit');
  fs.mkdirSync(path.join(out, 'screenshots'), { recursive: true });
  const viewports = String(args.viewports || 'mobile,desktop').split(',').map((v) => v.trim());
  for (const v of viewports) if (!VIEWPORTS[v]) throw new Error(`unknown viewport ${v}`);

  const report = { base, generatedAt: new Date().toISOString(), routes: [] };
  await withBrowser(async (browser) => {
    const page = await (await browser.newContext()).newPage();
    const routes = args.routes ? [].concat(args.routes) : await discoverRoutes(page, base);
    for (const route of routes) {
      const entry = { route, viewports: {}, events: [] };
      record(page, entry.events);
      for (const vp of viewports) {
        await page.setViewportSize(VIEWPORTS[vp]);
        const result = {};
        try {
          await page.goto(base + route, { waitUntil: 'networkidle', timeout: 20000 });
          await page.waitForTimeout(300);
          const shot = path.join('screenshots', `${slug(route)}-${vp}.png`);
          await page.screenshot({ path: path.join(out, shot), fullPage: true });
          result.screenshot = shot;
          result.overflow = await page.evaluate(CHECKS.overflow);
          result.brokenImages = await page.evaluate(CHECKS.brokenImages);
          if (vp === 'mobile') result.touchTargets = await page.evaluate(CHECKS.touchTargets);
          if (vp === 'desktop') result.tokens = await page.evaluate(CHECKS.tokens);
        } catch (e) {
          result.error = String(e.message || e).split('\n')[0];
        }
        entry.viewports[vp] = result;
      }
      page.removeAllListeners();
      report.routes.push(entry);
      const problems = [
        entry.events.length && `${entry.events.length} event(s)`,
        ...viewports.filter((v) => entry.viewports[v].overflow?.length).map((v) => `overflow@${v}`),
        ...viewports.filter((v) => entry.viewports[v].brokenImages?.length).map((v) => `broken-img@${v}`),
        ...viewports.filter((v) => entry.viewports[v].error).map((v) => `load-error@${v}`),
      ].filter(Boolean);
      console.log(`${route.padEnd(32)} ${problems.length ? problems.join(', ') : 'ok'}`);
    }
  });
  fs.writeFileSync(path.join(out, 'audit.json'), JSON.stringify(report, null, 2));
  console.log(`\naudit.json and screenshots written to ${out}`);
}

// ---- run -------------------------------------------------------------------

async function run(args) {
  const flow = args._[1];
  if (!flow || !args.base) throw new Error('usage: browse.mjs run <flow.mjs> --base <url> [--out DIR] [--viewport name]');
  const base = String(args.base).replace(/\/+$/, '');
  const name = path.basename(flow).replace(/\.m?js$/, '');
  const out = path.resolve(args.out || 'flows-out');
  fs.mkdirSync(out, { recursive: true });
  const viewport = VIEWPORTS[args.viewport || 'desktop'];
  if (!viewport) throw new Error(`unknown viewport ${args.viewport}`);

  const result = { flow: name, base, viewport: args.viewport || 'desktop', events: [], screenshots: [], status: 'passed' };
  await withBrowser(async (browser) => {
    const page = await (await browser.newContext({ viewport })).newPage();
    record(page, result.events);
    const t = {
      base, out,
      snap: async (label) => {
        const file = `${name}-${slug(label)}.png`;
        await page.screenshot({ path: path.join(out, file), fullPage: true });
        result.screenshots.push(file);
        return file;
      },
    };
    try {
      const mod = await import(pathToFileURL(path.resolve(flow)).href);
      await mod.default(page, t);
    } catch (e) {
      result.status = 'failed';
      result.error = String(e.message || e).split('\n')[0];
      result.failedAt = page.url();
      try { await t.snap('failed'); } catch {}
    }
  });
  if (result.status === 'passed' && result.events.some((e) => e.kind === 'pageerror')) result.status = 'failed';
  fs.writeFileSync(path.join(out, `${name}.json`), JSON.stringify(result, null, 2));
  console.log(`${name}: ${result.status}${result.error ? ` (${result.error})` : ''}; ` +
    `${result.events.length} event(s); details in ${path.join(out, `${name}.json`)}`);
  if (result.status !== 'passed') process.exitCode = 1;
}

const args = parseArgs(process.argv.slice(2));
const cmd = { audit, run }[args._[0]];
if (!cmd) {
  console.error('usage: browse.mjs audit <baseUrl> | run <flow.mjs> --base <url>');
  process.exit(2);
}
cmd(args).catch((e) => { console.error(e.message); process.exit(2); });
