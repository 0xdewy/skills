# Visual checklist

Judge screenshots and the `tokens` block of `audit.json` against these. Every
finding cites a screenshot path or a token value. Fix by mapping to the app's
existing scale, never by inventing a new one.

## Hard failures (fix first)

- Horizontal scroll at 375px (`overflow` in `audit.json`).
- Text overlapping, clipped, or escaping its container.
- Body text under 14px; any input under 16px on mobile (iOS zooms the page).
- Touch targets under 24×24px (`touchTargets`); 44×44 for primary actions.
- No visible focus ring when tabbing.
- Text contrast under 4.5:1 (3:1 for text 18px+ or bold 14px+).

## Consistency (from `tokens`)

| Dimension | Healthy | Smell |
|---|---|---|
| Font families | 1–2 | 3+ in one view |
| Font sizes | 5–8 forming a scale | 10+, or sizes 1–2px apart |
| Font weights | 3–4 | 300 for body text; odd weights like 450 |
| Background colors | 10 or fewer | Near-duplicate grays such as #f5f5f5 and #f6f6f6 |
| Spacing | 10 or fewer, on a 4px grid | Off-grid values (7, 13, 22); 14+ distinct |
| Border radii | 4 or fewer | Mixed radii on the same component type |

## Layout and hierarchy

- One dominant element per screen; primary actions outweigh secondary ones.
- Left edges of text in a column agree; cards in a grid share a width; page
  padding is symmetric.
- More space above a heading than below it; related items sit closer than
  unrelated ones.
- Buttons, cards, and inputs of one kind share radius, padding, border,
  shadow, and states.
- Hover, focus, active, disabled, loading, empty, and error states are all
  visibly distinct and styled, not browser defaults.
- Mobile rearranges content; it does not shrink the desktop layout.
- Motion: 150–300ms ease-out on state changes, `transform` and `opacity`
  only; nothing animates in on page load.
