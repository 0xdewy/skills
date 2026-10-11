---
name: pr-describe
description: >-
  Writes or rewrites a pull request's title and description so a reader with
  no context understands why, what changed, and how to verify it. TRIGGER on:
  "describe this PR", "write the PR description", "rewrite the PR body",
  "PR description for #123", "draft a description before I open the PR".
  SKIP on: reviewing a PR for defects (pr-smellz), commit messages, release
  notes, and summarizing a diff with no PR involved.
---

# PR Describe

Write the description a stranger needs: a title that says what happens, an
opening paragraph anyone can follow, and nothing after it that a reviewer
would not miss. The diff already says what changed; only the description can
say why and how to check it. Every sentence traces to evidence: the diff, the
commits, linked issues, the repo's own template.

Load `../common/patterns/execution-contract.md`. Read `references/anatomy.md`
before writing. Gather evidence with `scripts/pr_context.sh`.

## Inputs

- One or more PR numbers, URLs, or branches; nothing means the current
  branch's PR. Each PR is handled on its own.
- No PR yet: `--base <ref>` describes the local diff and writes a body file
  for `gh pr create --body-file`.
- `--dry-run` prints without applying. Applying is the default for your own
  PRs; a PR by someone else is dry-run unless `--apply` is given.

## Workflow

1. Gather. `scripts/pr_context.sh <pr> --out <WORKSPACE>/<pr>` writes
   `meta.json`, `body.md`, `commits.txt`, `stat.txt`, `diff.patch`,
   `issues.md`, `template.md`. Read everything but the diff whole; for a
   large diff read `stat.txt` first, then the hunks of the substantive files.
   Open surrounding source only where a hunk is unintelligible alone.
2. Understand before writing. Answer each in one line: What problem? What
   changes for a user, operator, or developer? What is deliberately not done?
   How was it verified? What could break? Write `unknown` rather than invent.
   Ask the user only when the why is recoverable from no source.
3. Separate the substantive change from mechanical bulk: renames, generated
   files, lockfiles, formatting. Decide where a reviewer should look first.
4. Keep what deserves keeping from the existing body: required template
   checklists, closing keywords (`Fixes #N`), screenshots and benchmarks,
   human notes that are still true. Drop anything the diff contradicts and
   say so in the report.
5. Write per `references/anatomy.md`, in this order. The opening paragraph:
   two or three plain sentences a reader with no context follows on first
   read. Then only the sections a reviewer would miss. Then the title, last
   and from scratch: three drafts, keep the shortest that still names the
   outcome.
6. Cut. Delete every line that repeats another or that a reviewer would not
   miss, then run the checklist in `references/anatomy.md`.
7. Apply. Save the current title and body to
   `<WORKSPACE>/<pr>/previous-title.txt` and `previous-body.md`, then
   `gh pr edit <pr> --title <title> --body-file <file>`. Keep the existing
   title only when yours is no better. Report old and new title and print the
   one-line restore command. Under `--dry-run` or on another author's PR,
   print the proposal and stop.

## Rules

- Title and opening come first in effort: most readers stop there.
- Behavior over files. "Uploads over 10 MB now return 413 instead of
  hanging," not "changed the upload handler."
- Never invent intent. If no source records the motivation, write
  `Motivation: not recorded` and flag it.
- Shorter is better until meaning is lost. Delete before rewording.
- Never merge, approve, review, comment, push, or edit code. For defects, use
  `pr-smellz`.

Final line:

```text
DONE: <WORKSPACE> — <N> PR(s) described, applied=<A>, dry-run=<D>
```
