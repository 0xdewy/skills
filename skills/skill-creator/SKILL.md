---
name: skill-creator
description: >-
  Create, refine, test, and publish Claude skills (reusable SKILL.md behavior
  packs). TRIGGER on: "make a skill for X", "create a SKILL.md", "write a skill
  that does Y", "improve my skill", "publish my skill", "set up a skills repo",
  "make this into a skill", "how do I share a skill". SKIP on: casual uses of
  the word "skill" unrelated to Claude behavior packs ("that's a useful skill",
  "he's skilled at X"), general workflow questions that don't involve SKILL.md
  authoring, or when the user is just asking what skills are without intent to
  build one.
license: MIT
metadata:
  author: iamky1e
  version: 2.0.0
  category: meta
  tags:
    - skills
    - development
    - workflow
    - publishing
---

# Skill Creator

A meta-skill for creating, testing, and publishing other skills.

Skills are reusable behavior packs — a `SKILL.md` file (plus optional scripts,
references, and assets) that Claude loads into context to perform specialized
tasks consistently. Once published to a GitHub repo, anyone can install a skill
with a single command.

---

## Phase 0: Is a Skill the Right Tool?

Before building, confirm this problem actually warrants a skill. A skill is the
right tool when the task is:

- **Recurring** — the user or others will invoke it repeatedly across sessions
- **Transferable** — another Claude instance (or another user) should do this
  the same way, with the same guidance loaded
- **Nontrivial** — it requires enough domain knowledge or workflow guidance that
  the behavior wouldn't emerge correctly without the skill loaded

If the task is a one-off, answer directly or write a quick script. If it's a
personal preference that applies only to this user's workspace, a `CLAUDE.md`
entry fits better. If it involves automated recurring behavior (run X every
night), a cron + `schedule` skill is the right layer.

Before starting fresh, check whether a skill already exists by invoking the
`find-skills` skill. If you have hermes installed with a tap configured:

```bash
hermes skills search <keywords>
```

If a close match exists, consider improving it rather than duplicating it.

If a skill is the right tool, continue to Phase 1.

---

## Phase 1: Capture Intent

Gather (or infer from context) these four things:

1. **What task does it automate?** Specific is better than vague.
2. **When should it trigger?** What phrases or contexts signal "use this skill"?
3. **What does good output look like?** Files created? Text format? Actions taken?
4. **Any edge cases, constraints, or dependencies** worth knowing upfront?

Don't start writing until you have a clear mental model of the skill's purpose.
One well-understood use case beats three vague ones.

---

## Phase 2: Write the SKILL.md

Every skill lives in a directory named after it. The only required file is
`SKILL.md` with YAML frontmatter:

```
skill-name/
├── SKILL.md          ← required
├── references/       ← docs loaded when needed
├── scripts/          ← executable helpers (Python, bash)
├── evals/            ← evals.json test cases
├── templates/        ← boilerplate files the agent copies/modifies
└── assets/           ← binary or non-text resources (images, fonts, etc.)
```

### Frontmatter template

```yaml
---
name: skill-name
description: >-
  One or two sentences. Start with what it does. Then add explicit trigger and
  skip conditions — Claude has a slight tendency to undertrigger, so name the
  phrases and contexts that activate this skill. TRIGGER on: X, Y, Z.
  SKIP on: A, B, C (casual mentions, unrelated uses of keywords).
license: MIT
metadata:
  author: your-github-username
  version: 1.0.0
  category: <see Quick Reference for definitions>
  tags:
    - relevant-tag
    - another-tag
---
```

The description lives in Claude's context at all times and is the primary
mechanism that controls when the skill fires. TRIGGER/SKIP structure prevents
both undertriggering (vague descriptions) and overtriggering (broad keywords
that appear in unrelated contexts).

For a complete annotated example applying all these patterns, see
`references/example-skill.md`.

### Writing the skill body

**Explain the why, not just the what.** Claude is smart. When it understands
*why* a step matters, it adapts when things go sideways rather than failing
mechanically. "Extract dates in ISO format (tools downstream expect this)"
works better than "ALWAYS use ISO format."

**Use progressive disclosure.** Keep `SKILL.md` focused on decisions and
workflow steps. Move content to `references/` when it is:
- Long enough to disrupt reading flow (tables > 20 rows, code blocks > 40 lines)
- Domain-specific detail that only applies to certain execution paths
- Reference material consulted occasionally, not on every run

Always tell the skill when to load a reference: "For AWS-specific steps, read
`references/aws.md`." Never load references unconditionally at the top.

**Bundle scripts for repetitive work.** If the skill always needs the same
multi-step computation, write it once as `scripts/do-thing.py` and call it.
This is cheaper and more reliable than asking Claude to reinvent it every time.

**Prefer imperative instructions.** "Read the file, extract the date column,
output as ISO 8601" beats "The skill will read the file and attempt to
extract..."

**Design for composition and subagent use.** Skills are often invoked inside
larger workflows — by other skills, by loop/schedule agents, or by Claude acting
as an orchestrator. Write your skill so it works in both interactive and
non-interactive contexts:

- **Accept context from the caller.** If the skill needs a target URL, file
  path, or option, accept it as a parameter in the invocation prompt rather than
  always asking the user interactively. "Scrape {{url}} and return JSON" is more
  composable than always prompting for the URL.
- **Emit structured output when possible.** JSON or clearly delimited output
  lets a calling agent parse results without brittle text parsing. Document the
  output format explicitly in the skill body.
- **Scope side effects.** Write outputs to a predictable path (e.g.,
  `./outputs/result.json`) so callers know where to find them. Avoid prompting
  for confirmation mid-execution when the context is non-interactive.
- **Signal completion clearly.** End with a summary line a caller can detect:
  `DONE: <count> items written to outputs/result.json`. This gives orchestrators
  a reliable completion signal without parsing prose.
- **Name natural chains.** If this skill feeds another, say so: "Output is a
  JSON array at `./outputs/data.json`, compatible with the data-analysis skill."
- **Subagent behavior.** When invoked as a subagent (Claude in a loop or
  pipeline), complete the task fully and report results — don't wait for further
  interaction. Design phases to be resumable: if a step produces intermediate
  files, later steps should detect and skip completed work rather than re-running
  from scratch.

**Set up evals for measurable quality.** Once the skill has a testable
behavior, encode it as `evals/evals.json` — an array of test cases. Write a
`scripts/grade.py` that checks outputs against those assertions and emits a
`grading.json` summary. This lets you run before/after comparisons when
iterating.

Minimum viable `evals/evals.json` entry:

```json
[{
  "id": 1,
  "prompt": "A realistic user prompt that should trigger the skill",
  "expected_output": "What good output looks like, described in prose",
  "expectations": [
    "Specific assertion grade.py can check programmatically",
    "Another assertion"
  ]
}]
```

See `web-scraping/evals/evals.json` and `web-scraping/scripts/grade.py` for a
complete implementation of this pattern.

---

## Phase 3: Test It

Before publishing, test the skill on 2–3 realistic prompts — the kind of thing
a real user would actually say.

**Simple test protocol:**

1. Write the test prompts down. Would a real user say this?
2. Open a new Claude Code session with the skill loaded:
   ```bash
   claude --skill /path/to/your-skill/
   ```
   Before sending any test prompts, confirm the skill actually loaded:
   ```
   What skills are currently loaded? List their names and descriptions.
   ```
   Your skill's `name` should appear in the list. If it doesn't, check
   frontmatter syntax — `name` and `description` fields must be present and
   correctly indented. Fix and reload before testing.
3. Send each test prompt. Does Claude invoke the skill? Does the output match
   what you expected?
4. Note what went wrong and revise the SKILL.md.

Repeat until outputs look right. Two or three iterations on concrete examples
is usually enough to find the obvious gaps.

**What to look for:**
- Does Claude trigger the skill at all? (If not, strengthen the TRIGGER clause)
- Does it overtrigger on prompts that should be handled without the skill? (Add
  SKIP examples to the description)
- Does it follow the instructions, or invent its own approach?
- Are the outputs complete, or are important parts missing?
- Does it handle edge cases reasonably?

---

## Phase 4: Iterate

Focus improvements on the concrete failures you observed. A few heuristics:

- If Claude ignores an instruction, explain *why* it matters instead of just
  making it louder. Adding ALL CAPS rarely helps; context usually does.
- If outputs are inconsistent, look for ambiguity in the instructions and
  tighten the language.
- If the skill is too slow (too many tokens), remove instructions that aren't
  pulling their weight. Read the transcript to find where time is wasted.
- If a pattern repeats across test cases, bundle it in `scripts/` instead.

**When to write a script vs. refine prose.** If a step fails because Claude
made a reasoning error, fix the instructions — add the *why*, tighten ambiguous
language. If a step fails because it's a mechanical multi-step computation that
Claude reinvents differently each time (parsing a specific format, calling an
API with a fixed schema), write a `scripts/` helper and call it from the skill.
Scripts are deterministic; prose is not.

**Sizing and splitting.** Consider splitting a skill into sub-skills when:
- It covers two distinct trigger conditions that rarely overlap in practice
- Phases 2–3 have grown past 150 lines spanning two different domains
- Users frequently invoke only one half of the skill

Split by creating `skill-name-part-a/` and `skill-name-part-b/` directories.
Reference siblings from a parent skill's "See also" section, or let them stand
alone if the trigger conditions are genuinely distinct.

---

## Phase 5: Publish

Read `references/publishing.md` for the full workflow. The short version:

1. Put your skill in a GitHub repo under `skills/<skill-name>/`
2. Push to GitHub
3. Others install it:
   ```bash
   hermes skills tap add your-username/your-repo
   hermes skills install your-username/your-repo/skills/skill-name
   ```

See `references/publishing.md` for repo structure, `skills.sh` listing, README
templates, and versioning guidance.

---

## Quick Reference

**Skill directory structure:**
```
skill-name/
├── SKILL.md
├── references/
│   └── something.md
├── scripts/
│   └── helper.py
├── evals/
│   └── evals.json
└── assets/
    └── template.docx
```

**Required frontmatter fields:** `name`, `description`

**Recommended frontmatter fields:** `license`, `metadata.author`,
`metadata.version`, `metadata.category`, `metadata.tags`

**Category definitions:**

| Category | Use for |
|---|---|
| `devops` | CI/CD, infrastructure, deployment, cloud tooling |
| `data` | ETL, analysis, scraping, databases, data pipelines |
| `writing` | Content generation, editing, documentation |
| `security` | Audits, vulnerability research, pen testing |
| `meta` | Skills about skills, agent tooling, Claude config |
| `productivity` | Personal workflow, task management, automation |
| `testing` | QA, end-to-end testing, eval frameworks, test generation |
| `education` | Teaching, visualization, Socratic/interactive learning |
| `finance` | Market data, financial reports, investment analysis |
| `other` | Doesn't fit the above categories |

**Skill discovery:** Claude reads `name` + `description` to decide when to use
a skill. Everything else (body + resources) only loads when the skill is
invoked. Keep descriptions specific, with explicit TRIGGER and SKIP clauses.

**references/ directory:** Create a `references/` directory if your skill needs
lookup tables, checklists, or prompt templates that would clutter the main
SKILL.md. Always tell the skill when to load a reference file — never load
references unconditionally at the top.

**Composition checklist:**
- [ ] Accepts inputs as parameters (not just interactive prompts)
- [ ] Outputs to a documented, predictable path
- [ ] Ends with a parseable completion signal
- [ ] Names any skills it chains with
- [ ] Phases are resumable (detects and skips completed work)

---

## Completion

End your final message with a parseable completion line:

```
DONE: <skill-name>/SKILL.md — <brief summary of what was created or improved>
```
