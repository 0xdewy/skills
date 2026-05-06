# Adversarial Attack Catalog

Read this file when executing Phase 3 of the testing pipeline. Each attack includes what to do, how to script it with Playwright, and what to look for. Not every attack applies to every app — use judgment, but err on the side of trying more rather than fewer.

Organize generated test files under `tests/adversarial/` (or `e2e/adversarial/` if that convention exists in the project). Name each test file after the attack category.

---

## 1. State Corruption

### 1.1 Double-submit
**What:** Rapidly click any submit button 5+ times.
**Playwright approach:**
```js
const btn = page.locator('button[type="submit"], button:has-text("Save"), button:has-text("Submit")');
await btn.click({ clickCount: 5 });
```
**Look for:** Duplicate records created, spinner stuck forever, multiple success/error toasts, race conditions in network tab.

### 1.2 Mid-action navigation
**What:** Fill a form halfway, press browser back, then browser forward.
**Playwright approach:**
```js
await page.fill('#some-input', 'partial text');
await page.goBack();
await page.goForward();
```
**Look for:** Form state lost (acceptable) vs. corrupted (bad — half-filled state with wrong values), error thrown on forward navigation, stale form data submitted on accident.

### 1.3 Concurrent tabs
**What:** Open the same resource in two contexts. Edit in tab A and save. Edit in tab B and save.
**Playwright approach:**
```js
const ctx = await browser.newContext();
const page2 = await ctx.newPage();
await page2.goto sameUrl;
// edit in page1, save, then edit in page2, save
```
**Look for:** Silent overwrite (no warning), crash, error message, optimistic update conflict. Last-write-wins without warning is a moderate bug.

### 1.4 Session expiry mid-action
**What:** Clear auth cookies/localStorage while the user is mid-flow, then attempt an action.
**Playwright approach:**
```js
await page.context().clearCookies();
await page.evaluate(() => localStorage.clear());
await page.click('#some-action-button');
```
**Look for:** White screen, raw error dump, redirect to login with state preserved, graceful error message. Any unhandled exception is critical.

---

## 2. Input Boundary Attacks

### 2.1 Empty required fields
**What:** Submit every form with all fields blank.
**Playwright approach:**
```js
await page.click('button[type="submit"]');
```
**Look for:** Frontend validation fires (good), request still sent to server (bad), error messages are clear, no crash.

### 2.2 Maximum length overflow
**What:** Paste 10,000+ characters into every text input and textarea.
**Playwright approach:**
```js
const longText = 'A'.repeat(10001);
await page.fill('#text-input', longText);
```
**Look for:** Input accepts it (may be fine if server truncates), UI breaks (text overflow, layout shift), character counter goes negative, form submission fails silently.

### 2.3 Special characters and emoji
**What:** Inject `<>'";{}` and complex emoji (🇺🇳, 👨‍👩‍👧‍👦, ❤️‍🔥) into all inputs.
**Playwright approach:**
```js
const specialChars = `<>'";{}👨‍👩‍👧‍👦🇺🇳❤️‍🔥`;
await page.fill('#input', specialChars);
await page.click('button[type="submit"]');
```
**Look for:** Encoding errors, garbled output on re-render, XSS (raw HTML renders — critical), form submission fails, database errors surfaced to user.

### 2.4 Numeric edge cases
**What:** Enter `-1`, `0`, `9999999999`, `NaN`, `1e309`, `3.14159` in numeric inputs.
**Playwright approach:**
```js
for (const val of ['-1', '0', '9999999999', '1e309', '3.14159']) {
  await page.fill('#number-input', val);
  await page.click('button[type="submit"]');
}
```
**Look for:** Negative values accepted when they shouldn't be, overflow/Infinity handling, decimal precision issues, silent truncation.

### 2.5 SQL/XSS probes
**What:** Submit `<script>alert(1)</script>` and `'; DROP TABLE users;--` in inputs.
**Playwright approach:**
```js
const xss = '<script>alert(1)</script>';
const sql = "'; DROP TABLE users;--";
```
**Look for:** Raw `<script>` content renders as HTML in the response page (critical — XSS), input is sanitized/escaped (good), server error exposed to user.

---

## 3. Timing and Network

### 3.1 Rapid toggle
**What:** Flip any toggle/checkbox as fast as possible for 10 seconds.
**Playwright approach:**
```js
const toggle = page.locator('.toggle, input[type="checkbox"]');
for (let i = 0; i < 50; i++) {
  await toggle.click({ delay: 200 });
}
```
**Look for:** State desync between UI and server, network request queue overflow, final state doesn't match last click, spinner stuck.

### 3.2 Slow network (throttled)
**What:** Simulate Slow 3G and navigate all core flows.
**Playwright approach:**
```js
const client = await page.context().newCDPSession(page);
await client.send('Network.emulateNetworkConditions', {
  offline: false, latency: 2000, downloadThroughput: 50000, uploadThroughput: 25000
});
```
**Look for:** Spinners appear and eventually resolve (good), permanent loading states (bad), timeout errors unhandled, skeleton loaders stuck.

### 3.3 Offline recovery
**What:** Load the page, go offline, attempt actions, go back online.
**Playwright approach:**
```js
await client.send('Network.emulateNetworkConditions', { offline: true, latency: 0, downloadThroughput: -1, uploadThroughput: -1 });
// try actions
await client.send('Network.emulateNetworkConditions', { offline: false, latency: 0, downloadThroughput: -1, uploadThroughput: -1 });
```
**Look for:** App recovers automatically, requires refresh, loses data, shows error boundary, queues actions for retry.

---

## 4. UI Stress

### 4.1 Rapid modal cycling
**What:** Open and close different modals 10+ times quickly.
**Playwright approach:**
```js
for (let i = 0; i < 10; i++) {
  await page.click('#open-modal-1');
  await page.click('#close-modal');
  await page.click('#open-modal-2');
  await page.click('#close-modal');
}
```
**Look for:** Modals stacking on top of each other, broken z-index, scroll lock stuck after closing (body remains `overflow: hidden`), orphaned backdrops.

### 4.2 Scroll position on re-render
**What:** Scroll down a long list, trigger a re-render (delete an item, filter change).
**Playwright approach:**
```js
await page.evaluate(() => window.scrollTo(0, 1000));
await page.click('#delete-item');
```
**Look for:** Scroll jumps to top, position preserved but wrong (stale index), virtual scroll breaks.

### 4.3 Resize thrashing
**What:** Rapidly resize the browser viewport while interacting with a form.
**Playwright approach:**
```js
for (let width of [375, 1280, 768, 500, 1024, 375]) {
  await page.setViewportSize({ width, height: 800 });
}
```
**Look for:** Layout breaks at non-standard widths, form elements overlap, responsive breakpoints leave artifacts, absolute-positioned elements escape containers.

---

## 5. Framework-Specific Attacks

### React
- **Concurrent mode edge cases:** Trigger rapid route switches while data is fetching. Look for stale closures, torn rendering between Suspense boundaries.
- **Effect cleanup races:** Navigate away during a pending fetch. Check for state updates on unmounted components (console warnings).
- **Key prop abuse:** If lists use array index as key, reorder items and check for state leakage between list items.

### Svelte
- **Reactive statement loops:** Bind a reactive `$:` statement that depends on itself. The compiler catches most of these, but derived stores with circular dependencies can still cause infinite loops at runtime.
- **Transition leaks:** Rapidly toggle elements with `transition:` or `animate:` directives. Look for residual CSS classes from interrupted transitions.
- **Destroyed element bindings:** Check if any `bind:` references survive component destruction (rare but possible with stores).

### Vue
- **Watcher loops:** Trigger a `watch` that modifies its own source value. Vue 3 handles this with max iteration limits, but computed chains can still loop.
- **Direct prop mutation:** Check for components that mutate props directly — Vue warns but doesn't prevent, and the behavior in production differs from development.
- **v-if/v-show toggling:** Rapidly toggle between v-if (destroys/creates) and check for event listener leaks, v-show (CSS toggle) and check for stale styles.

### Angular
- **Change detection storms:** Trigger rapid events in a component with `ChangeDetectionStrategy.Default` and heavy template bindings. Look for performance degradation.
- **Subscription leaks:** Check that `Observable` subscriptions are cleaned up in `ngOnDestroy`. Missing teardown causes memory leaks detectable over repeated navigation.

### Solid
- **Signal dependency loops:** Create a reactive derivation that depends on its own output. Solid's fine-grained reactivity can enter infinite update loops in edge cases.
- **Effect cleanup:** Check that `onCleanup` is called in all effects that create resources.

### Astro
- **Island hydration order:** Rapidly interact with multiple interactive islands. Check for hydration race conditions where an island's JS hasn't loaded yet.
- **View transitions:** Navigate between pages with `transition:animate` rapidly. Look for stale DOM nodes from previous pages.
