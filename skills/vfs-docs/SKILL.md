---
name: vfs-docs
description: >-
  Builds self-describing docs/ trees where directory shape and filenames
  carry the meaning, so an agent orients from `tree docs/` alone. Only use
  when explicitly requested.
license: MIT
disable-model-invocation: true
metadata:
  author: iamky1e
  version: 3.0.0
  category: meta
  activation: explicit
  tags:
    - documentation
    - unix-philosophy
    - progressive-disclosure
    - onboarding
    - docs-tree
---

# VFS Docs

Build or restructure a `docs/` tree that works like a filesystem is supposed
to: every path is a statement, every directory is a zoom level, and
`tree docs/` alone conveys the mental model. The tree is the only index — no
README, NAVIGATION, or context-map files inside `docs/`.

Load `../common/patterns/execution-contract.md`, `../common/patterns/workspace.md`, and `../common/patterns/scaling.md`. Load
`references/tree-design.md` before designing or editing a tree. Prefer the
skill's scripts over handwritten equivalents: `scripts/analyze_repo.py` for
repo shape, `scripts/lint_tree.py` for convention checks.

## The four rules

1. **Names carry the meaning.** Filenames are kebab-case claims or questions
   readable in `tree` output; directory names are topics.
2. **Depth is zoom.** Root files orient in one screen; each level down narrows
   scope and adds detail.
3. **Summary file pairs with detail dir.** When `topic.md` outgrows one
   screen, it keeps a one-screen summary and grows a sibling `topic/` with the
   detail. The summary tells the reader whether to descend.
4. **The tree is the index.** If an index file feels necessary, the names are
   failing — fix the names instead.

## Modes

- `--quick`: lint the existing tree and fix naming/structure violations only.
- `--standard`: scaffold or restructure `docs/` around the repo's main topics.
- `--thorough`: full tree with leaf-level detail and migration of all existing
  doc content.

## Workflow

1. Confirm repo root and git status. Preserve unrelated changes.
2. Run `scripts/analyze_repo.py` for repo shape; inventory existing docs.
   Existing content is preserved and relocated, never discarded.
3. Design on paper first: write the intended `tree docs/` output and check it
   reads as an outline of the system before creating anything.
4. Write files: one topic per file, one screen per file. `git mv` existing
   docs into place, then update inbound links repo-wide.
5. Run `scripts/lint_tree.py docs/` and fix every violation (naming,
   structure, and date-prefixed names). After a migration, run
   `scripts/lint_tree.py docs/ --links` to confirm no cross-reference dangles;
   treat runtime-path mentions as expected noise, not docs links.
6. Print the final `tree docs/` and report created/moved/deleted files.

Final line:

```text
DONE: vfs-docs — <N> files, depth=<D>, lint=<clean|N issues>
```
