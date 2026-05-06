# CSS & Visual Audit Checklist

Read this file during Phase 2 of the testing pipeline. These checks are meant to be automated with Playwright scripts that take screenshots at each viewport and flag issues. Not every check requires a screenshot — many can be asserted programmatically.

---

## 1. Viewport Testing

Test at three breakpoints minimum:
- **375px** — Mobile (iPhone-sized)
- **768px** — Tablet
- **1280px** — Desktop

For each viewport, capture a full-page screenshot of every route. Compare against the desktop layout to spot broken responsive behavior.

```js
const viewports = [
  { name: 'mobile', width: 375, height: 812 },
  { name: 'tablet', width: 768, height: 1024 },
  { name: 'desktop', width: 1280, height: 800 },
];
for (const vp of viewports) {
  await page.setViewportSize(vp);
  await page.screenshot({ path: `screenshots/${vp.name}-${route}.png`, fullPage: true });
}
```

---

## 2. Spacing & Alignment

**Check programmatically:**
- Get bounding boxes of sibling elements and verify consistent gaps
- Check that content doesn't overflow its container
- Verify grid/flex items align correctly at all viewports

```js
const boxes = await page.locator('.card').evaluateAll(els =>
  els.map(el => ({ left: el.offsetLeft, top: el.offsetTop, width: el.offsetWidth, height: el.offsetHeight }))
);
// Check for consistent gaps, misalignment
```

**What to flag:**
- Content overflowing viewport horizontally (especially on mobile)
- Inconsistent padding between sections
- Text or buttons clipped by container edges
- Elements that should be centered but aren't

---

## 3. Typography

**Check programmatically:**
- Scan for font-size, font-weight, font-family computed styles
- Verify line-height on body text (should be 1.4–1.7 for readability)

```js
const typo = await page.locator('h1, h2, h3, p, span').evaluateAll(els =>
  els.slice(0, 20).map(el => ({
    tag: el.tagName,
    fontSize: getComputedStyle(el).fontSize,
    fontWeight: getComputedStyle(el).fontWeight,
    fontFamily: getComputedStyle(el).fontFamily,
    lineHeight: getComputedStyle(el).lineHeight,
  }))
);
```

**What to flag:**
- Mixed font families within the same hierarchy level
- Font sizes that don't follow a scale (e.g., h2 larger than h1)
- Body text with line-height below 1.4 (hard to read)
- Text too small to read on mobile (below 14px body)

---

## 4. Color & States

**Interactive element states to test:**
- Default (resting)
- Hover
- Focus (keyboard navigation)
- Active (pressed)
- Disabled
- Loading

```js
const button = page.locator('button').first();
// Default
await button.screenshot({ path: 'btn-default.png' });
// Hover
await button.hover();
await button.screenshot({ path: 'btn-hover.png' });
// Focus
await button.focus();
await button.screenshot({ path: 'btn-focus.png' });
// Disabled — find a disabled button or set disabled
await page.evaluate(() => {
  const btn = document.querySelector('button');
  if (btn) btn.disabled = true;
});
await button.screenshot({ path: 'btn-disabled.png' });
```

**Contrast checks:**
- Use Playwright's accessibility assertions to check text contrast
- Flag text-over-image sections where contrast may be insufficient

```js
// Accessibility scan catches contrast issues
const accessibilityScanResults = await page.accessibility.snapshot();
```

**Dark/light mode:**
- If the app has a theme toggle, run all checks in both modes
- Look for hardcoded colors that don't switch with theme

---

## 5. Responsive & Touch

**Touch target sizes:**
- All interactive elements should be at least 44x44px
- Check spacing between adjacent targets (minimum 8px gap)

```js
const targets = await page.locator('a, button, input, select, textarea, [role="button"]').evaluateAll(els =>
  els.map(el => ({
    tag: el.tagName,
    width: el.offsetWidth,
    height: el.offsetHeight,
    text: el.textContent?.trim().slice(0, 30),
  })).filter(el => el.width < 44 || el.height < 44)
);
```

**Horizontal scroll:**
- Flag any page that scrolls horizontally on mobile viewport

```js
const hasHorizontalScroll = await page.evaluate(() => {
  return document.documentElement.scrollWidth > document.documentElement.clientWidth;
});
```

**Modal/dropdown visibility:**
- Open modals and dropdowns at all viewport widths
- Check that they don't render off-screen
- Check that backdrop covers full viewport

---

## 6. Framework-Specific Visual Checks

### React / Next.js
- **Flash of unstyled content (FOUC):** Navigate between routes and screenshot immediately. Check for raw HTML flash before hydration.
- **Suspense boundaries:** Check that loading fallbacks render correctly (not just spinners — proper spacing and layout).

### Svelte / SvelteKit
- **Transition artifacts:** After route transitions, check for residual CSS classes from `transition:` directives that linger on removed elements.
- **Store-driven styles:** If stores control theme or layout, toggle them and check for visual glitches.

### Vue / Nuxt
- **v-cloak:** Check that `v-cloak` CSS is present and working — without it, raw template syntax flashes before mount.
- **Async component loading:** If using `defineAsyncComponent`, check for layout shift when components load.

### Tailwind CSS
- **Conflicting utilities:** Look for elements where opposing utilities are applied (e.g., `flex` + `grid`, `block` + `hidden`). Tailwind doesn't warn about these.
- **Arbitrary values:** Check that `[]` arbitrary values render correctly and don't break at different viewports.

### CSS-in-JS (Styled Components, Emotion, etc.)
- **Style injection order:** Navigate rapidly and check for styles applied in wrong order (later components override earlier ones incorrectly).
- **Unmount cleanup:** Navigate away from a component and check if its injected `<style>` tags are cleaned up (memory leak if not).
