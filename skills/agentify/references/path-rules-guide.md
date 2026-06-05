# .claude/rules/ Path-Scoped Rules Guide

Loaded by agentify during Phase 4.2 when generating rules files.

---

## What .claude/rules/ Files Are

Claude Code loads files from `.claude/rules/` into context selectively:
each file is only included when the agent is editing files matching the
`paths:` glob patterns in the file's YAML frontmatter. Files without a
`paths:` field are **always loaded** at session start (same priority as
`.claude/CLAUDE.md`).

There are two locations for rules:
- **`.claude/rules/`** (project-level, committed to git, shared with team)
- **`~/.claude/rules/`** (user-level, applies to ALL your projects on this machine)

User-level rules load first, then project-level rules — so project rules take
priority when both exist for the same domain.

---

## Frontmatter Syntax

```yaml
---
paths:
  - "src/api/**"
  - "src/routes/**"
  - "**/handlers/**"
# No paths: field → always loaded (use sparingly!)
---
```

- `paths:` is the key field for path scoping
- Globs follow `.gitignore`-style syntax
- Multiple patterns are OR'd (any match → file is loaded)
- The file loads when the agent is *working on* a matching file

### Brace Expansion (Claude Code 2026+)

```yaml
---
paths:
  - "src/**/*.{ts,tsx}"   # Matches .ts and .tsx files under src/
  - "test/**/*.{test,spec}.{ts,js}"  # Matches .test.ts, .spec.ts, .test.js, .spec.js
---
```

This is more concise than listing every extension separately.

### Always-Loaded Rules

A rules file without `paths:` field loads for every session — same as
CLAUDE.md. Only use this for genuinely repo-wide conventions. If a rule
only applies to certain file types, use paths: scoping to save context.

```yaml
---
# No paths: field — this loads for all files
---

# Repo-Wide Rules

- All commits must reference a ticket number
...  ← Keep it under 60 lines or reconsider whether it should be in CLAUDE.md
```

---

## Glob Pattern Reference

| Pattern | What it matches | Common mistake |
|---------|----------------|---------------|
| `src/api/**` | Everything under src/api/ recursively | `src/api/*` only matches one level |
| `**/*.test.ts` | All TypeScript test files anywhere | `*.test.ts` only matches root |
| `migrations/**` | Everything under migrations/ | `migrations/` is not a valid glob |
| `src/**/*.py` | All Python files under src/ | `src/*.py` only matches root of src/ |
| `cmd/**` | Everything under cmd/ recursively | — |
| `**/*.spec.*` | All spec files in any language | — |
| `*.go` | Go files in the root directory only | `**/*.go` for all Go files |
| `src/**/*.{ts,tsx}` | TypeScript and TSX files under src/ | `src/**/*.{ts}` (trailing comma) |
| `**/*.{test,spec}.ts` | .test.ts and .spec.ts files | Requires Claude Code 2026+ |

**Key rule:** Use `**` for recursive matching. A single `*` only matches
within one directory level. Use brace expansion `{a,b}` for multiple extensions.

---

## Rules File Structure

Four sections — use only the ones that have real content:

```markdown
---
paths:
  - "src/api/**"
  - "**/handlers/**"
---

## Conventions

- Route handlers must validate input before calling the service layer
- All handlers return typed Response objects, not raw JSON
- Error responses follow the ErrorResponse interface in src/types/errors.ts

## Patterns

### Input Validation
Always use the `validate(schema, data)` helper:
```typescript
const body = validate(CreateUserSchema, req.body);
// validate() throws BadRequestError on invalid input — no try/catch needed
```

### Error Handling
Handlers should not catch errors — the error middleware handles all exceptions.
Throw typed errors: `throw new NotFoundError('User not found')`.

## Pitfalls

- Do not access `req.body` before validation — it may contain unsanitized data
- Do not import from src/services directly — use dependency injection via req.services

## See Also

- Service layer conventions → docs/services.md
- Error type definitions → src/types/errors.ts
```

**Sizing:** If a domain's conventions need more than 100 lines, split the
domain into two files:
- `api-validation.md` (paths: `src/api/**`) — validation patterns only
- `api-errors.md` (paths: `src/api/**`) — error handling only

---

## Domain Taxonomy

Standard domains for most repo types. Only create files for domains that
have actual files in this repo:

| Domain | Typical path globs | Key conventions to capture |
|--------|-------------------|---------------------------|
| `api` | `src/api/**`, `api/**`, `**/routes/**`, `**/handlers/**` | Input validation, auth checks, response shape, error throwing |
| `testing` | `tests/**`, `**/*.test.*`, `**/*.spec.*`, `test/**` | Test structure, mock patterns, fixture conventions, assertion style |
| `frontend` | `src/components/**`, `src/pages/**`, `frontend/**`, `ui/**` | Component patterns, state management, prop conventions, styling |
| `database` | `src/db/**`, `migrations/**`, `**/models/**`, `**/repository/**` | Query patterns, migration style, ORM idioms, transaction patterns |
| `cli` | `cmd/**`, `src/cli/**`, `**/commands/**` | Argument parsing, exit codes, output format, error messages |
| `config` | `config/**`, `**/config.*`, `settings/**`, `.env*` | Env var patterns, validation, defaults, secret handling |
| `scripts` | `scripts/**`, `*.sh`, `Makefile` | Shell conventions, error handling, idempotency, logging |

---

## Extracting Conventions from Existing Code

Before writing a rules file, read 2-3 representative files in the domain:

```bash
# Find the most-changed files in this domain (highest convention density)
git log --name-only --since=180.days -- src/api/ | grep '\.ts$' | sort | uniq -c | sort -rn | head -5
```

Look for:
- Repeated import patterns (what utilities are always used?)
- Function signature patterns (what do handlers/services always accept/return?)
- Error handling patterns (try/catch? throw? result types?)
- Naming patterns (camelCase? snake_case? specific suffixes?)
- Validation patterns (where does validation happen?)

Only document patterns you actually observe. Do not invent conventions.

---

## Verifying Globs Match Actual Files

After writing each rules file, verify its globs are correct:

```bash
# For paths: ["src/api/**"]
find . -not -path './.git/*' -not -path './node_modules/*' \
  -path './src/api/*' | head -5
```

If a glob matches zero files:
1. Check if the directory structure matches the glob
2. Try a simpler pattern (e.g., `src/api/**` → `**/api/**`)
3. If the domain simply doesn't exist in this repo, remove the rules file

A rules file with globs that match nothing is worse than no rules file —
it may confuse the agent about the repo structure.
