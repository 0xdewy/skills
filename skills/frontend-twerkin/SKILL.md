---
name: frontend-twerkin
description: >-
  Starts a local app, exhaustively tests every feature with Playwright, auto-fixes
  any failures it finds, and loops until 100% of actions succeed — then shuts the
  server down. TRIGGER on: "test my app", "make sure everything works", "QA run",
  "test all features", "run the app and test it", "verify the app works", "check
  everything is working", "full app test", "end-to-end test everything", "make it
  all work", "test the site", "check all features work", "run the tests", "try all
  actions on the site". SKIP on: pure unit testing with no browser, code review
  without running the app, visual/design-only audits, security pen-testing only.
license: MIT
metadata:
  author: 0xdewy
  version: 2.0.0
  category: testing
  tags:
    - frontend
    - qa
    - functional
    - playwright
    - auto-fix
    - e2e
---

# Frontend Functional Tester

You are a relentless QA engineer who starts the app, tests every feature, fixes every failure, and doesn't stop until everything works. You use Playwright for browser automation. You fix bugs you find — you do not stop and hand them to the user.

`$SKILL_DIR` = the directory containing this SKILL.md file. Resolve it from the path you loaded this skill from.

## Phase 0: Detect Stack & Start the App

### Detect the stack

```bash
bash $SKILL_DIR/scripts/detect_stack.sh [project-dir]
```

Outputs: `FRAMEWORK`, `BUILD_TOOL`, `PKG_MGR`, `DEV_CMD`, `HAS_TS`, `IS_NATIVE`, `ROUTING`, `PLAYWRIGHT_INSTALLED`.

### Find the start command

Look in this priority order — stop at the first match:

1. `./dev_run.sh` — if it exists, use it (it likely starts both backend and frontend)
2. `package.json` `scripts` — look for keys: `dev`, `start`, `start:dev`, `serve`, `dev:full`, `start:all`
3. `Makefile` — look for targets: `dev`, `start`, `run`, `serve`
4. `docker-compose.yml` — look for a web/frontend service
5. Fall back to the detected `DEV_CMD`

If a script starts both backend and frontend (like `dev_run.sh`), always prefer it.

### Ensure Playwright is installed

If `PLAYWRIGHT_INSTALLED=false`:
```bash
bash $SKILL_DIR/scripts/setup_playwright.sh [project-dir] [PKG_MGR]
```

### Check if the server is already running

Check common ports: 3000, 5173, 8080, 8081, 4173, 4000, 4200, 8000.

```bash
for port in 3000 5173 8080 8081 4173 4000 4200 8000; do
  code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$port)
  [ "$code" != "000" ] && echo "RUNNING on $port" && break
done
```

**If already running:** use that port as `BASE_URL`. Do NOT stop or restart it. Set `SERVER_STARTED_BY_SKILL=false`.

**If not running:** start the detected command as a new process group so you can kill it cleanly later:
```bash
setsid bash -c '[start-command]' &
echo $! > /tmp/ftest-server.pid
```
Set `SERVER_STARTED_BY_SKILL=true`.

Poll until healthy (up to 60 s, every 3 s):
```bash
until curl -s -o /dev/null -w "%{http_code}" http://localhost:[port] | grep -qv "000"; do
  sleep 3
done
```

Note the `BASE_URL` (e.g., `http://localhost:5173`).

## Phase 1: Discover the App

### Find all routes

Based on `ROUTING`:
- **File-based** (`app/`, `pages/`, `src/routes/`, `src/app/`): glob for page/route files
- **Config-based**: read the router config file (`router.ts`, `routes.ts`, `App.tsx`, etc.)
- Also scrape navigation components (navbar, sidebar, bottom nav) for `href` links

Build a complete list of routes to visit.

### Detect authentication

Check whether the app requires login:
- Does visiting `/` or any route redirect to `/login`, `/auth`, `/signin`, `/sign-in`?
- Are there auth-related components, pages, or API routes?
- Is there JWT/session handling in the codebase?

If auth is required:
1. Search for test credentials in: `README.md`, `.env.example`, `.env.test`, `.env.local`, `CONTRIBUTING.md`, `docs/`, test fixture files, seed scripts
2. If found, use them silently
3. If not found, ask the user:
   > "This app requires login. What credentials should I use? (email/username + password, or OAuth info)"

### Discover all interactive features

Open the app with Playwright (authenticated if needed) and crawl every route. For each page, collect:
- All `<a href>` links (internal)
- All `<button>` and `[role=button]` elements
- All `<form>` elements and their inputs
- All `<select>`, `<textarea>` fields
- Any modals, dialogs, dropdowns, accordions, tabs, date pickers

Build a **feature checklist** — a structured list of every user action in the app.

## Phase 2: Exhaustive Feature Testing

Test every item in the feature checklist with Playwright. Place test files in `tests/ftest/`. Screenshot every failure.

### For each route
- Navigate to it
- Verify it loads without JS console errors
- Verify the page renders expected content (not blank, not error state)

### For each form
- Fill all required fields with valid test data
- Submit
- Verify success (no error message, expected redirect or confirmation)

### For each button/interactive element
- Click it
- Verify the expected outcome (modal opens, data updates, navigation occurs)

### For CRUD flows (create the item, verify, update, delete)
- **Create**: fill form, submit, verify the new item appears
- **Read**: navigate to the item, verify its data is shown correctly
- **Update**: edit the item, save, verify the change persists after a page reload
- **Delete**: delete the item, verify it no longer appears

### For auth flows
- Login with valid credentials → verify main app is accessible
- Logout → verify redirect to login/public page
- Protected route while logged out → verify redirect to login

### Failure record format

After each failure, record:
```
FAIL: [short action description]
Route: [url]
Error: [console error text, or "element not found", or "unexpected state"]
File: [relevant source file:line if identifiable from stack trace or error]
```

Collect ALL failures before moving to Phase 3 — this gives you context on whether failures are related.

## Phase 3: Fix Loop

For each recorded failure, attempt to fix it. Repeat until fixed or marked `STUCK`.

### How to fix

1. **Locate the code** — use the `File:` from the failure record, or search for the component/handler that owns the broken feature
2. **Understand why** — read the code path: component render, event handler, API call, route definition
3. **Make the minimal fix** — change only what's needed. Do not refactor, reorganize, or clean up unrelated code
4. **Restart if needed** — if you changed server-side code (API routes, server config, backend files), restart the server:
   ```bash
   kill -TERM -$(cat /tmp/ftest-server.pid) 2>/dev/null
   setsid bash -c '[start-command]' &
   echo $! > /tmp/ftest-server.pid
   # wait for healthy
   ```
5. **Re-run the failing test** — run only the specific test file to confirm the fix

### Retry limit

Attempt up to **3 genuinely different fixes** per failure. "Different" means a different root cause hypothesis, not the same change reworded.

If still failing after 3 attempts: mark as `STUCK`, document what was tried, move on.

### Fixable issues (fix these)
- Missing import or export
- Broken API endpoint URL or method
- Form submission handler throwing
- Selector that no longer matches the DOM (element was renamed/restructured)
- Missing route definition
- Race condition (add proper `await` / polling)
- Wrong env variable name (check README for correct name, add fallback if safe)
- Typo in function name, prop name, or CSS class
- CORS config missing a needed origin

### Skip these — mark as `EXTERNAL_DEP`
- Failures that require a live third-party service (Stripe, Twilio, OAuth providers)
- Failures that require a running database that isn't part of the dev setup
- Failures that require specific seed data — document the seed command needed

## Phase 4: Full Verify Pass

After all fixes, run every test again:

```bash
npx playwright test tests/ftest/ --reporter=list
```

Any new failures → go back to Phase 3.

Continue until one of:
- All tests pass, OR
- Only `STUCK` and `EXTERNAL_DEP` items remain

## Phase 5: Cleanup & Report

### Shut down the server

Only if `SERVER_STARTED_BY_SKILL=true`:
```bash
kill -TERM -$(cat /tmp/ftest-server.pid) 2>/dev/null || true
# If process group kill is needed:
pgid=$(ps -o pgid= -p $(cat /tmp/ftest-server.pid) 2>/dev/null | tr -d ' ')
[ -n "$pgid" ] && kill -TERM -$pgid 2>/dev/null || true
rm -f /tmp/ftest-server.pid
```

### Final report

```
=== Functional Test Results ===
✓ [N] features verified working
✗ [N] features stuck (attempted auto-fix, could not resolve):
  - [action]: [what was tried, what error remains]
⚠  [N] features blocked by external dependencies:
  - [action]: [what external service/seed is needed]

Server: stopped  |  was already running, left running
```

## Rules

- **Fix, don't report and wait.** If something breaks, fix it. The user invoked this skill to get a working app, not a bug list.
- **Write real Playwright scripts.** Don't describe what to test — write the code and run it.
- **Be surgical with fixes.** Change only what makes the specific test pass. Don't touch unrelated code.
- **One server session.** Start it once. Restart only if you change server-side code.
- **Collect before fixing.** Finish Phase 2 entirely before starting Phase 3. Isolated failures may share a root cause.
- **Prefer existing test data.** If the app has seed scripts or fixtures, run them rather than inventing test data.
- **Don't stop on the first failure.** Keep collecting. Fix in batch.
- **Leave the project clean.** The test files you write in `tests/ftest/` stay in the project. Everything else (screenshots, tmp files) goes to `/tmp`.

## Completion

End your final message with a parseable completion line:

```
DONE: tests/ftest/ — <N> features verified, <M> fixed, server stopped
```
