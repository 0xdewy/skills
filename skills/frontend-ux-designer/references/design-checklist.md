# Design Evaluation Checklist

Reference for Phase 3 of the frontend-ux-designer skill. Load this when doing
the design critique pass. Each section maps to a dimension in the audit.

---

## 1. Spacing Rhythm

A well-designed app uses a **spacing scale** — a small set of values derived
from a base unit (usually 4px or 8px). Common healthy scales:

| Scale | Values |
|---|---|
| 4px base | 4, 8, 12, 16, 20, 24, 32, 40, 48, 64 |
| 8px base | 8, 16, 24, 32, 40, 48, 64, 80, 96 |
| Tailwind default | 4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 44, 48, 56, 64, 80, 96 |

**What to look for:**
- Values not on a 4px grid (7, 13, 19, 22px) = magic numbers, fix to nearest grid value
- More than 12 distinct spacing values = scale sprawl, needs consolidation
- Adjacent sections with wildly different spacing = no rhythm
- Inner component padding that doesn't match the global scale

**Fix pattern:** Identify the most common spacing values (these are the de facto
scale). Map all other values to the nearest scale value.

---

## 2. Typography

### Type scale

A healthy type scale has 5–8 sizes forming a clear hierarchy:

| Role | Typical sizes |
|---|---|
| Display / Hero | 48–72px |
| H1 | 32–40px |
| H2 | 24–28px |
| H3 | 18–22px |
| Body | 14–16px |
| Caption / label | 11–13px |

**What to look for:**
- Headings all the same size → no hierarchy
- 3+ different body text sizes → inconsistency
- Font sizes that don't follow a ratio (e.g. jumps from 14 to 17 to 21) → not a scale

### Font weight

Use 3–4 weights maximum:
- Regular (400): body text
- Medium (500): subtitles, secondary labels
- Semibold (600): UI labels, buttons, headings
- Bold (700): strong emphasis, main headings

**What to look for:**
- Weight 300 used for body text → too light for readability
- Only weight 400 used everywhere → no hierarchy
- Weights like 450 or 550 → likely a mistake or CSS variable drift

### Line height

- Body text: 1.4–1.6
- Headings: 1.1–1.3
- Labels/UI text: 1.0–1.2

Line height set in px (e.g. `line-height: 20px`) is fragile — prefer unitless.

---

## 3. Color System

### Palette structure

A well-structured palette has:
- **Brand colors**: 1–2 primary colors with 3–5 shades each
- **Neutral colors**: 6–8 gray shades from near-white to near-black
- **Semantic colors**: success (green), warning (amber), error (red), info (blue)
- **Total**: 20–30 tokens is healthy; 50+ is sprawl

**What to look for in the audit data:**
- Background colors: more than 10 distinct values = palette sprawl
- Grays: if you see 5 very similar grays (e.g. #f5f5f5, #f6f6f6, #f7f7f7) → consolidate to 2
- Accent colors that appear only once = one-off, should use the nearest brand color

### Contrast

Minimum WCAG AA requirements:
- Normal text: 4.5:1 contrast ratio
- Large text (18px+ or 14px+ bold): 3:1
- UI components and graphics: 3:1

Use the formula: `(L1 + 0.05) / (L2 + 0.05)` where L is relative luminance.

Quick rule: white text needs background darker than ~#767676 for AA. Black text
needs background lighter than ~#959595 for AA.

---

## 4. Visual Hierarchy

The **Gutenberg principle**: the eye moves top-left to bottom-right. Most
important content should be top-left or top-center.

**F-pattern**: users scan in an F shape — first line fully, second line
partially, then vertical down the left edge. Navigation and CTAs placed on the
left or at the top of sections get more attention.

**Visual weight signals** (in order of strength):
1. Size (largest = most important)
2. Color (saturated/contrasting = important)
3. Weight (bold = important)
4. Position (higher up = more important)
5. Spacing (more whitespace around = more important)

**What to look for:**
- Multiple large bold elements on the same page competing for attention
- CTA buttons that are the same visual weight as secondary actions
- Important information pushed below the fold
- Empty space that's randomly distributed (not intentionally framing content)

---

## 5. Layout & Alignment

### Grid alignment

All content should sit on an invisible grid. Common patterns:
- **Single-column**: content max-width of 640–800px, centered
- **Two-column**: sidebar + main, or 50/50 split
- **CSS grid**: explicit tracks, content snapping to grid lines
- **Flexbox rows**: items with consistent gaps

**What to look for:**
- Text that starts at different left positions on the same page (misaligned columns)
- Cards in a grid that are different widths
- Section headers that don't align with the content below them
- Page content that's accidentally shifted right or left of center

### Symmetry

Symmetry is a strong signal of quality. Check:
- Left padding == Right padding on page containers
- Form labels all left-aligned (or all right-aligned)
- Button groups centered or right-aligned, not randomly placed
- Icon and text in buttons vertically centered

### Whitespace

Whitespace isn't empty — it's structure. Rules of thumb:
- More whitespace above a section header than below it (keeps header close to its content)
- Related items: less space between them. Unrelated items: more space.
- Hero sections: generous padding (80–120px vertical) signals importance
- Dense data tables: tight spacing is OK if it's consistent

---

## 6. Component Consistency

### Buttons

All primary buttons should have:
- Same background color
- Same border radius
- Same font size and weight
- Same padding (e.g. 8px 16px or 12px 24px)
- Same hover/active state

If there are multiple button "levels" (primary, secondary, ghost, danger), each
level should be internally consistent.

### Cards

All cards at the same level of hierarchy should have:
- Same border (or none)
- Same box shadow (or none)
- Same border radius
- Same padding
- Same hover state (if interactive)

Mixing some cards with shadows and some without, or some with borders and some
without, creates visual confusion.

### Form inputs

All inputs (text, select, textarea) should have:
- Same height (single-line inputs)
- Same border color and radius
- Same focus ring style
- Same padding

### Icons

Icon sizes should be chosen from 2–3 values (e.g. 16, 20, 24px). Mixing 14,
16, 18, 20, 22px icons in the same UI creates visual noise.

---

## 7. Interactive States

Every interactive element needs visual feedback for:
- **Hover**: color shift, shadow change, slight scale (1.02x max)
- **Focus**: visible focus ring — non-negotiable for keyboard access
- **Active/pressed**: slight darken or inset shadow
- **Disabled**: reduced opacity (0.4–0.6), `cursor: not-allowed`
- **Loading**: spinner or skeleton, element not interactive during load

Missing hover states = the app feels unresponsive.
Missing focus rings = the app is inaccessible to keyboard users.

---

## 8. Responsive Quality

### Breakpoints to check

| Breakpoint | Width | Device |
|---|---|---|
| Mobile | 375px | iPhone SE / small Android |
| Tablet | 768px | iPad portrait |
| Desktop | 1280px | Laptop |
| Wide | 1440px+ | Large monitor (optional) |

### Mobile checklist

- No horizontal scroll (immediate Critical fix)
- Touch targets ≥ 44x44px
- Text readable without zooming (body ≥ 14px)
- Navigation accessible (hamburger menu, bottom nav, or similar)
- Forms don't cause zoom on iOS (input font-size ≥ 16px)
- Images don't overflow their containers

### Responsive patterns (from good to bad)

**Good**: Designed for mobile, enhanced for desktop. Content rearranges meaningfully.
**OK**: Desktop layout adapts to mobile with a few breakpoints. Minor layout shifts.
**Bad**: Desktop layout squished into mobile. Tiny text, horizontal scroll.

---

## 9. Animation & Motion

### When to animate

- State transitions (open/close, show/hide): 150–300ms, ease-out
- Navigation transitions: 200–400ms
- Loaders/spinners: continuous, not distracting
- Micro-interactions (button press, hover): 50–150ms

### When NOT to animate

- Page load (don't animate content in — just show it)
- Long data tables (animating rows is distracting)
- Error messages (show immediately, not after a delay)

### Animation properties

Prefer animating `transform` and `opacity` — they're GPU-accelerated and don't
cause layout reflow. Avoid animating `width`, `height`, `margin`, `padding`.

---

## 10. Polish Checklist

The details that separate "pretty good" from "beautiful":

- [ ] No orphan words (single word on its own line in headings)
- [ ] Icon and text baselines aligned (use `align-items: center`)
- [ ] Buttons have consistent internal padding (not just min-width)
- [ ] No stray underlines on text that isn't a link
- [ ] No stray `border: 1px solid transparent` that becomes visible on resize
- [ ] Images have consistent aspect ratios in lists/grids
- [ ] Loading states look intentional (skeleton screens, not blank flashes)
- [ ] Empty states designed (not just "No data found" in default body text)
- [ ] Error messages styled consistently (not raw browser alerts mixed with custom ones)
- [ ] Scroll behavior: main page scrolls, modals scroll internally, nothing double-scrolls
