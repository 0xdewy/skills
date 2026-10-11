---
name: frontend-qa
description: >-
  Drives a local web app in a headless browser to find and fix functional
  failures and visual defects, then proves each fix with a re-run. Only use
  when explicitly requested.
disable-model-invocation: true
---

# Frontend QA

Exercise a running local web app in headless Chromium, find what breaks or
looks wrong, fix it in scope, and prove the fix by re-running. Evidence is a
screenshot path, a recorded event, or a computed value; nothing else counts.

Load `../common/patterns/execution-contract.md` for `WORKSPACE` and the
completion line. Everything runs through `scripts/browse.mjs` with Node. It
uses the project's Playwright when installed, else the global `playwright`
package. If neither exists, ask before running
`npm i -g playwright && playwright install chromium`. Never add Playwright to
the project's own dependencies.

## Scope

- Named routes or flows: test only those. Otherwise the routes linked from the
  start page and the flows visible on them.
- "test", "QA", "bugs", "broken": functional lens. "design", "layout",
  "looks", "polish": visual lens. Unqualified: both.
- State scope, lens, and app URL in one line before starting.

## Workflow

1. **App.** Use a server that is already running. Otherwise start the dev
   script from `package.json` with the lockfile's package manager, in the
   background, and record command, URL, and PID.
2. **Sweep.** `node scripts/browse.mjs audit <url> --out <WORKSPACE>/audit
   [--routes /a /b]`. Per route and viewport it saves a screenshot and records
   console and page errors, failed and 4xx+ requests, horizontal overflow,
   broken images, small touch targets (mobile), and design tokens (desktop).
   Read the printed summary, then `audit.json` for the routes with problems.
3. **Flows** (functional lens). One file per flow under `<WORKSPACE>/flows/`,
   run with `node scripts/browse.mjs run <flow>.mjs --base <url> --out
   <WORKSPACE>/flows [--viewport mobile]`. Use `getByRole` and `getByLabel`
   locators, assert the outcome a user would see, then `t.snap`. Pick attacks
   for each form and action from `references/attacks.md`.

   ```js
   export default async (page, t) => {
     await page.goto(t.base + '/checkout');
     await page.getByLabel('Email').fill('qa@example.com');
     await page.getByRole('button', { name: 'Continue' }).click();
     await page.waitForURL('**/payment');
     await t.snap('payment-step');
   };
   ```

   A thrown error or a page error fails the flow, saves a `-failed`
   screenshot, and exits 1. Console errors and failed requests are recorded
   in the flow's JSON for you to judge.
4. **Judge** (visual lens). Read the screenshots and tokens against
   `references/visual-checklist.md`. A finding names the element, the
   screenshot or value, and the rule it breaks.
5. **Fix.** Smallest change in the app's own conventions and design system.
   No redesign, new dependency, or unrelated cleanup unless asked. Re-run the
   failing flow or re-sweep the route; a fix without a green re-run is not a
   fix. When asked for a report only, edit no source.
6. **Report** `<WORKSPACE>/report.md`: still failing first, each with
   evidence; then fixed and re-verified; then tested and passing; then out of
   reach (external services, auth, missing data). Generated flows stay in
   `WORKSPACE` unless the user wants them in the project.
7. Stop any server you started.

```text
DONE: <WORKSPACE>/report.md — <passed>/<total> flows passing, <N> fixed, <M> open
```
