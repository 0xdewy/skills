---
name: pr-describe
description: >-
  Writes or rewrites a pull request's title and description so a reader with
  no context understands why, what changed, and how to verify it. TRIGGER on:
  "describe this PR", "write the PR description", "rewrite the PR body",
  "PR description for #123", "draft a description before I open the PR".
  SKIP on: reviewing a PR for defects (pr-smellz), commit messages, release
  notes, and summarizing a diff with no PR involved.
license: MIT
metadata:
  author: 0xdewy
  version: 1.0.0
  category: quality
  tags:
    - pull-request
    - documentation
    - writing
    - github
---

# PR Describe

Write the description a stranger needs. The diff already says what changed;
only the description can say why, what it means for the reader, and how
anyone can check it. Every sentence traces to evidence: the diff, the commits,
linked issues, the repo's own template. Never describe intent the diff does
not carry.

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
5. Write the title and body per `references/anatomy.md`. Proportion: a
   one-line fix gets three lines; a migration gets every section. No empty
   or `N/A` sections.
6. Check before applying: every claim traceable; first sentence stands alone;
   behavior named, not files; no unexplained acronym or codename; the
   verification section says what was not run; nothing in the diff is left
   undescribed at the behavior level.
7. Apply. Save the current body to `<WORKSPACE>/<pr>/previous-body.md`, then
   `gh pr edit <pr> --body-file <file>`. Change the title only when it is
   vague, non-imperative, or inaccurate. Print the one-line restore command.
   Under `--dry-run` or on another author's PR, print the proposal and stop.

## Rules

- Why before what. If no source records the motivation, write
  `Motivation: not recorded` and flag it; do not fabricate one.
- Behavior over files. "Uploads over 10 MB now return 413 instead of
  hanging," not "changed the upload handler."
- Say what is not in the PR whenever a reader would otherwise expect it.
- No marketing and no hedging. Limitations and hacks are stated plainly.
- Never merge, approve, review, comment, push, or edit code. For defects, use
  `pr-smellz`.

Final line:

```text
DONE: <WORKSPACE> — <N> PR(s) described, applied=<A>, dry-run=<D>
```
