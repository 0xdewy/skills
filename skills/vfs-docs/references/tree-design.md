# Tree Design: The Filesystem Is the Documentation

Loaded by vfs-docs before designing or restructuring a tree. Contains the
design rules, sizing guidance, worked examples, and migration procedure.

---

## The Reader

Design for one reader: an agent (or human) whose first and often only command
is `tree docs/`. That output must answer three questions without opening a
single file:

1. What is this system made of? (top-level directory names)
2. What does the author think I need to know? (filenames as claims)
3. Where do I zoom in for my task? (the branch whose names match the task)

Every rule below exists to make that one command sufficient.

---

## Rule 1 — Names carry the meaning

A filename is a complete, specific statement of what the file contains,
readable in tree output. Directory names are nouns (topics); filenames are
claims or questions about that topic.

| Bad | Why | Good |
|---|---|---|
| `notes.md` | says nothing | `why-we-chose-postgres.md` |
| `misc.md` | a junk drawer | split into named topics |
| `api.md` at depth 3 | too broad for its depth | `rate-limits-are-per-token.md` |
| `2024-meeting.md` | names the occasion, not the content | `sharding-decision.md` |
| `IMPORTANT.md` | shouts, doesn't inform | name the important fact itself |

Conventions:

- kebab-case, lowercase, `.md` for prose. Non-prose artifacts (diagrams,
  schemas, fixtures) live in the tree under the same naming rules.
- A question filename (`how-do-retries-work.md`) promises an answer; a claim
  filename (`retries-are-idempotent.md`) promises evidence. Both are good.
  Prefer the claim when one sentence can carry the conclusion.
- Numeric prefixes (`10-`, `20-`) only when reading order genuinely matters
  (tutorials, runbooks). Everywhere else, alphabetical is the order.

## Rule 2 — Depth is zoom

Each directory level narrows scope and increases detail. Nothing at depth N
repeats what depth N-1 already said; it elaborates it.

| Depth | Role |
|---|---|
| `docs/*.md` | orientation — what the system is, in one screen each |
| `docs/topic/*.md` | how each area works |
| deeper | specifics: edge cases, decisions, invariants, runbooks |

Depth beyond 4 usually means a level in the middle is contributing a name but
no meaning — collapse it.

## Rule 3 — Summary file pairs with detail dir

Growth path for any topic:

1. `docs/deploys.md` — one screen, complete at its zoom level.
2. It outgrows one screen → promote: keep `docs/deploys.md` as a one-screen
   summary, move the detail into a new sibling dir `docs/deploys/` split into
   named children.
3. Reading `deploys.md` tells the reader whether `deploys/` is worth entering.

Invariants:

- Every directory has a same-named sibling summary file (`deploys.md` beside
  `deploys/`). The summary states what the directory covers and the one or two
  facts everyone needs even without descending.
- The summary never duplicates a child; it compresses them.
- Demotion is legal too: a directory whose children shrank back to one screen
  total collapses into its summary file.

## Rule 4 — The tree is the index

Forbidden inside `docs/`: `README.md`, `index.md`, `NAVIGATION.md`, `TOC.md`,
context maps, link farms, "start here" files. Each of these is an admission
that the names have failed. When tempted, rename and restructure until the
tree output itself reads as the table of contents.

Outside `docs/` a single pointer is fine and encouraged — one line in the repo
README or agent guidance: "Docs are self-describing: run `tree docs/`."

## Directory rules

- A directory needs ≥ 2 entries besides its own summary pair. One child means
  the split was premature — fold it back.
- No empty directories; the tree contains only meaning, never scaffolding for
  future meaning.
- Siblings should be mutually exclusive: if a fact could live in either of two
  siblings, their names overlap — sharpen one or merge them.

---

## Worked example — small service

```text
docs
├── what-this-service-does.md
├── how-a-request-flows.md
├── operations.md
├── operations
│   ├── deploy-and-rollback.md
│   ├── alerts-and-what-they-mean.md
│   └── secrets-come-from-vault.md
├── decisions.md
└── decisions
    ├── why-postgres-not-dynamo.md
    └── why-we-queue-writes.md
```

Read the tree top to bottom: it already tells you the service's story — what
it does, how requests flow, how it is operated, and which choices were
deliberate. Opening files is zooming, not searching.

## Worked example — monorepo

```text
docs
├── how-the-packages-fit-together.md
├── api.md
├── api
│   ├── auth-is-jwt-with-refresh.md
│   ├── rate-limits.md
│   └── rate-limits
│       ├── limits-are-per-token-not-per-ip.md
│       └── what-happens-at-the-limit.md
├── web.md
├── web
│   └── ... (per-area detail)
└── shared.md
```

Top level mirrors the package layout, so the docs tree and the code tree teach
the same shape. `rate-limits.md` summarizes; its directory holds the two facts
that needed their own files.

---

## Migration of an existing docs/ folder

1. Inventory every existing doc and the headings inside each; content is
   preserved and relocated, never discarded. Big multi-topic files are split
   along their headings into named files.
2. Draft the target tree as plain text first. Review it with the three reader
   questions from the top of this file.
3. `git mv` where a file maps 1:1 so history follows; split/merge with new
   files where it doesn't.
4. Delete index/navigation files last, after confirming every link they held
   is either represented by a name in the tree or moved into a summary file.
5. Grep the whole repo for links to moved paths and update them.
6. Run `scripts/lint_tree.py docs/`; fix every violation before reporting.
