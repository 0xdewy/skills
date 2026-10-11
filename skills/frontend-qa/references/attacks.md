# Attacks per form and action

Pick what the surface allows; name the attack in the flow file so the report
can cite it. Each row: what to do, what a failure looks like.

## Forms

| Attack | Do | Failure looks like |
|---|---|---|
| Empty submit | Submit with every field blank | Request sent anyway, vague error, crash |
| Overflow | 10,000 characters in each text field | Layout breaks, counter negative, silent failure |
| Special characters | `<>'";{}` plus joined emoji (👨‍👩‍👧‍👦) | Garbled re-render, raw HTML rendered (critical), 500 |
| Script probe | `<script>alert(1)</script>` | Markup rendered unescaped (critical) |
| Numeric edges | `-1`, `0`, `1e309`, `3.14159`, `9999999999` | Negative accepted, Infinity shown, silent truncation |
| Double submit | `click({ clickCount: 5 })` on submit | Duplicate records, stuck spinner, stacked toasts |
| Back mid-form | Fill half, `page.goBack()`, `page.goForward()` | Corrupted half state, error on forward, stale submit |

## Session and network

| Attack | Do | Failure looks like |
|---|---|---|
| Expired session | `context.clearCookies()` and clear localStorage mid-flow, then act | White screen, raw error, lost state with no login redirect |
| Two tabs | Edit the same record in two contexts, save both | Silent last-write-wins |
| Slow network | CDP `Network.emulateNetworkConditions` with 2 s latency | Spinner never resolves, unhandled timeout, stuck skeleton |
| Offline | `context.setOffline(true)`, act, `setOffline(false)` | Data lost, no retry, error boundary with no way back |

## UI state

| Attack | Do | Failure looks like |
|---|---|---|
| Rapid toggle | Click a toggle 20 times with 100 ms delay | Final state differs from last click, request storm |
| Modal cycling | Open and close two modals 10 times | Stacked backdrops, body scroll locked after close |
| Scroll on re-render | Scroll down a list, then delete or filter | Jump to top, wrong item at the kept position |
| Resize | Loop viewport widths 375, 1024, 500, 1280 | Overlapping controls, elements escaping containers |
| Keyboard only | Tab through the flow; Enter and Space to act | No visible focus, unreachable control, focus trap |
