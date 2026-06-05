---
name: agentify
description: >-
  Creates and maintains a hierarchical, context-efficient documentation system for
  any git repo — generating CLAUDE.md (≤200 lines), .claude/rules/ path-scoped
  files, .claude/context-map.md (navigation index), docs/OVERVIEW.md (architecture),
  and docs/{component}.md deep-dives. Analyzes codebase, audits existing docs and
  auto memory (MEMORY.md), then generates or improves the hierarchy so an LLM agent
  can cold-start with minimal context and navigate to detail on demand. Idempotent:
  files scoring >80/100 are kept; only gaps are filled. Supports @import syntax,
  AGENTS.md interoperability, CLAUDE.local.md, and user-level rules.
  TRIGGER on: "map this repo", "prep this repo for agents", "make this repo agent-ready",
  "set up context for agents", "document this repo",
  "set up docs for LLMs", "create CLAUDE.md",
  "generate documentation hierarchy", "run agentify", "agentify this repo",
  "make this repo LLM-navigable", "set up docs",
  "create context map", "set up .claude/rules", "/agentify", "run /agentify",
  "set up docs for agents", "set up AGENTS.md",
  "update the docs", "refresh documentation",
  "create context memory", "set up CLAUDE.local.md",
  "set up coordination docs", "create docs/plans", "agent coordination hub",
  "create plans/specs/reviews", "set up agent coordination",
  "agentify --yes", "agentify --non-interactive".
  SKIP on: editing a single existing doc without wanting the full system, asking what
  CLAUDE.md should contain (answer directly without running scripts), repos already
  with excellent docs and no request to improve them, simple README edits.
license: MIT
metadata:
  author: iamky1e
  version: 1.4.0
  category: meta
  tags:
    - documentation
    - context-management
    - llm-navigation
    - claude-md
    - claude-rules
    - progressive-disclosure
    - agent-coordination
    - plans
    - specs
    - reviews
---

# agentify

Builds a layered documentation system that lets an LLM cold-start a repo with
≤200 lines of context, then navigate to exactly the depth it needs on demand.
For multi-agent repos, also scaffolds `docs/plans/`, `docs/specs/`, and
`docs/reviews/` — a coordination layer where agents can pick up work items,
work from specifications, and leave review artifacts.

**Why this exists:** Every repo benefits from hierarchical docs, but the right
structure varies by type (monorepo, service, library, CLI, webapp). Scripts
detect what already exists, assess gaps, and generate only what's missing —
so the output is accurate, not generic boilerplate.

**The multi-level hierarchy this skill creates or integrates with:**

```
L-1: ~/.claude/projects/<project>/memory/MEMORY.md  (auto memory, Claude-managed)
     → Claude's learned notes from previous sessions; first 200 lines loaded

L0: CLAUDE.md              (≤200 lines, always loaded + @import support)
    → project name, 2-3 sentence purpose, key commands, pointer map
    → CLAUDE.local.md (personal, gitignored — detected but not generated)

L1: docs/OVERVIEW.md       (≤400 lines, loaded on demand)
    → architecture diagram, components table, data flow

L2: docs/{component}.md    (≤300 lines each, loaded on demand)
    → deep dive per component: patterns, key files, gotchas

L3: .claude/rules/*.md     (≤100 lines each, auto-loaded by Claude Code
    → domain conventions  when editing matched file types)
    → ~/.claude/rules/*.md (user-level rules, applies across projects)
```

**Why these token budgets:** Startup context in Claude Code is ~8,000 tokens
before the user types anything (system prompt, CLAUDE.md, auto memory, skills,
environment). CLAUDE.md is loaded on every task — beyond 200 lines adherence
drops and irrelevant tokens are always paid. Rules files are tiny domains —
beyond 100 lines they're trying to do too much. Deeper docs are on-demand so
budgets are more generous. (Source: Claude Code official docs 2026 + Liu et al.
2023 "Lost in the Middle" on context placement effects.)

---

## Phase 0: Guard Rails

Check we are inside a git repository:
```bash
git rev-parse --git-dir 2>/dev/null || echo "NOT_GIT"
```

If not in a git repo, warn the user and ask if they want to proceed anyway.
The scripts work on any directory but git history enriches component detection.

Check for a prior run:
```bash
cat .agentify-lock 2>/dev/null
```

If the lock file exists, show its date and a summary of what was generated,
then ask: **"Update (fill gaps, improve low-scoring files) or Reset (regenerate
everything from scratch)?"** Default to **Update**.

**Update mode algorithm** (when user chooses Update):
1. Parse the lock: read `files_created`, `files_updated`, `files_kept`
2. In Phase 2: run `audit_context.py` as normal — scores are the truth
3. For every file tracked in the lock:
   - Score >80 → keep it (do not regenerate)
   - Score 60-80 → mark for Improve
   - Score <60 → mark for Regenerate
   - **Staleness override**: if `stale_docs` from the audit lists a file
     (score >80 but high git activity since lock_date), mark it for Improve
     even though the score is high
4. Files on disk but NOT in the lock → score as if new; apply same thresholds
5. Files that should exist per Phase 3 design but do NOT → mark as Create (score 0)

This ensures idempotency: a score-80+ file is never unnecessarily rewritten,
but a degraded or missing file is always caught. Staleness detection catches
docs that look good on paper but are out of date with recent code changes.

Check for auto memory and AGENTS.md:
```bash
cat ~/.claude/projects/*/memory/MEMORY.md 2>/dev/null | head -5
cat AGENTS.md 2>/dev/null
```
Note: auto memory is Claude-managed — never overwrite it. If `AGENTS.md` exists,
it will be used as source material.

Create the working directory:
```bash
mkdir -p /tmp/agentify
```

---

## Phase 1: Analyze

Map the repo structure to a JSON data model:

```bash
python3 $SKILL_DIR/scripts/analyze_repo.py . > /tmp/agentify/analysis.json
```

Read the output and print a human summary:
```
Project:    {project_name} ({project_type})
Language:   {primary_language} ({lang_breakdown top-3})
Size:       {size_bucket} ({total_lines:,} lines, {file_count} files)
Components: {component_dirs names, comma-separated}
Existing docs:  {existing_docs paths or "none"}
Existing rules: {existing_rules paths or "none"}
Commands found: {key_commands summary}
Coordination:   plans/{N plans} specs/{N specs} reviews/{N reviews} (or "none")
Multi-agent:    {has_multiagent_signals: yes/no}
Service pkgs:   {service_packages names or "none (not a monorepo)"}
Mode:           interactive (default) | non-interactive (--yes detected)
```

If the script fails (e.g. not in a git repo, or Python not available), fall
back to manual inspection: list top-level directories with `ls -la`, read
README.md if present, and infer the structure manually before continuing.
For the manual fallback, populate these fields from your inspection:
- `project_name` = directory name
- `project_type` = "unknown" (refine in Phase 3 design)
- `component_dirs` = top-level dirs with >5 files (count manually)
- `key_commands` = read from README or Makefile
- `existing_docs` = `find . -name "*.md" -not -path "./.git/*"`
- `coordination_summary` = check if `docs/plans/`, `docs/specs/`, `docs/reviews/` exist
- `has_multiagent_signals` = check if `AGENTS.md` or `.claude/agents/` exists

---

## Phase 2: Audit

Score existing context documents against best practices:

```bash
python3 $SKILL_DIR/scripts/audit_context.py . > /tmp/agentify/audit.json
```

Read the output and print a human-readable summary:
```
AUDIT RESULTS
─────────────
CLAUDE.md:        {score}/100  ({line_count} lines, budget ≤200)
  Issues:   {list or "none"}
  Strengths:{list or "none"}

.claude/rules/:   {count} files
  {per-file score summary}

docs/OVERVIEW.md: {score}/100 or "missing"
docs/ components: {count} files or "none"

Coordination dirs:
  docs/plans/:   {score}/100 or "missing" ({N} artifact files)
  docs/specs/:   {score}/100 or "missing" ({N} artifact files)
  docs/reviews/: {score}/100 or "missing" ({N} artifact files)

Stale docs (high score but active since last lock — mark for Improve):
  {list from stale_docs or "none"}

Action plan:
  Regenerate (<60): {list}
  Improve  (60-80): {list}
  Keep     (>80):   {list}
```

---

## Phase 3: Design

Read `references/hierarchy-patterns.md` for layering principles, templates,
and the "Lost in the Middle" mitigation strategy.

Read `references/project-types.md` for type-specific doc architecture based
on `project_type` from Phase 1.

Propose the documentation architecture for this specific repo. Print:

```
DOCUMENTATION PLAN
──────────────────
CLAUDE.md:            {create / update (score N→target) / keep}
  Lines 1-30:   project name, purpose, 3-5 key commands
  Lines 31-180: {key constraints or conventions if any}
  Lines 181-200: pointer map ({N} entries)

.claude/rules/ files:
  {domain}.md  →  paths: [{globs}]  ({create / update / keep})
  ...

.claude/context-map.md:  {create / update / keep}

docs/OVERVIEW.md:     {create / update / keep}
  Sections: architecture diagram (Mermaid), components table,
            data flow sequence diagram, external dependencies

docs/ component files:
  {component}.md  ({create / update / keep})  ...

docs/NAVIGATION.md:   {create / update / keep}

Agent Coordination (show only if has_multiagent_signals OR user explicitly requested):
  docs/plans/   → {create README stub / already exists ({N} plans) / skip}
  docs/specs/   → {create README stub / already exists ({N} specs) / skip}
  docs/reviews/ → {create README stub / already exists ({N} reviews) / skip}
  (if neither condition applies, list as "optional — confirm below")

Total to create: {N}   Total to update: {N}   Total to keep: {N}
```

If `has_multiagent_signals` is false and user didn't request coordination dirs,
mention them as optional in the plan printout: "Coordination dirs (docs/plans/,
docs/specs/, docs/reviews/) are available for multi-agent repos — include them?"

**Non-interactive mode:** If the invocation prompt contains `--yes` or
`--non-interactive`, skip this pause entirely. Log: "Non-interactive mode:
proceeding without confirmation." Then proceed to Phase 4 with the full plan
as designed. Skip and cancel are not available in non-interactive mode.

**Interactive mode** (default): **Pause here.** Ask the user:
"Proceed with this plan? (yes / edit / skip / cancel)"

- **yes** → proceed to Phase 4 as printed
- **edit** → accept their specific changes (e.g., "don't create docs/services.md",
  "skip coordination dirs"), re-print the updated plan, then ask again
- **skip N** → mark file N as "skipped by user"; do not generate it; remove from lock
- **cancel** → print "agentify cancelled. No files written." Stop. Do NOT emit DONE:

---

## Phase 4: Generate

Before filling any template, read `references/template-syntax.md` for the
placeholder resolution rules (simple replacement, conditional blocks, repeat
blocks). After filling, delete all remaining `{{...}}` markers — the output
file must contain no `{{` or `}}` strings.

**Monorepo check:** Read `project_type` from analysis.json.
- If `project_type == "monorepo"` → follow the **Monorepo Pattern** below.
- Otherwise → follow the **Standard Pattern** (phases 4.1–4.7).

### Monorepo Pattern

Read `references/project-types.md` (Monorepo section, including "Phase 4 Execution")
for the full doc structure and service detection rules. Follow that pattern instead
of Standard phases 4.1–4.7.

---

### Standard Pattern

Process files in this order (dependencies first — context-map.md is LAST because
it links to all other generated files):

1. CLAUDE.md
2. .claude/rules/*.md files
3. docs/OVERVIEW.md
4. docs/{component}.md files
5. docs/NAVIGATION.md
6. .claude/context-map.md (LAST — must reference all files created in steps 1-5)

For each file apply the action from Phase 3:
- **Keep** (scored >80): skip it, note "kept as-is"
- **Improve** (scored 60-80): read the existing file, apply targeted fixes
- **Create / Regenerate** (scored <60 or missing): generate from scratch

**After writing each file, enforce the token budget:**
```bash
wc -l < {file_path}
```
If over budget, trim immediately. Trim strategy: always move overflow DOWN
the hierarchy (never up). CLAUDE.md overflow → OVERVIEW; OVERVIEW overflow
→ component docs.

### 4.1 CLAUDE.md (≤200 lines)

Use `templates/CLAUDE.md.tmpl` as the structure. Fill in from analysis.json:
- Project name from `project_name`
- Purpose: synthesize from README first paragraph + manifest description +
  recent git log. Be specific. Never just "A project for X."
- Commands from `key_commands` (build, test, run, lint)
- Pointer map: one row per component doc + one row per rules file

**Placement rule (from "Lost in the Middle" research):**
- Lines 1–30: name, purpose, commands — highest value, primacy position
- Lines 181–200: Navigation pointer table — recency position, easy to scan
- Middle: any key constraints or conventions (2-4 unusual rules only)

**Do not put** architecture diagrams, component tables, or long explanations
in CLAUDE.md. Those belong in OVERVIEW.md.

**Agentify header:** prepend this as line 1 of every file you create or update:
```
<!-- agentify: generated {YYYY-MM-DD} | score-before: {prior_score_or_0} | source: 1.3.0 -->
```
When **keeping** a file as-is (score >80, not stale): leave the header unchanged.
When **improving**: update the date but keep the prior `score-before` value.
When **regenerating**: use score-before: 0 and today's date.

**`@import` commands split:** after drafting the CLAUDE.md content, count lines:
```bash
wc -l < /tmp/agentify/claude_draft.md
```
If >160 lines: extract the `## Commands` section into `.claude/commands.md`, then
replace it in CLAUDE.md with `@.claude/commands.md`. This keeps CLAUDE.md lean
and makes commands independently editable without touching the main file.
Only split when genuinely over 160 lines — small repos should keep commands inline.

### 4.2 .claude/rules/ files (≤100 lines each)

Read `references/path-rules-guide.md` for YAML frontmatter syntax and glob
patterns.

Create `.claude/` and `.claude/rules/` directories if they don't exist:
```bash
mkdir -p .claude/rules
```

One rules file per detected domain. Detect domains from `component_dirs` and
`lang_breakdown` in analysis.json. Typical domains (adjust to actual repo):
- `api.md` → paths: `["src/api/**", "api/**", "**/routes/**", "**/handlers/**"]`
- `testing.md` → paths: `["tests/**", "**/*.test.*", "**/*.spec.*"]`
- `frontend.md` → paths: `["src/components/**", "src/pages/**", "frontend/**"]`
- `database.md` → paths: `["src/db/**", "migrations/**", "**/models/**"]`
- `cli.md` → paths: `["cmd/**", "src/cli/**", "**/commands/**"]`

Use `templates/rule.md.tmpl` for structure. Fill in conventions actually
observed in the repo (read 2-3 representative files per domain before writing).
Do not invent conventions — extract them from the code.

After creating each rules file, verify its globs match real files:
```bash
python3 $SKILL_DIR/scripts/audit_context.py . --check-globs
```
This uses `glob_matches_files()` which handles brace expansion (`{src,tests}/**/*.ts`)
correctly — unlike `find -path` which does not support brace syntax. If any
glob mismatch is reported: fix the pattern or remove the rule.

### 4.3 .claude/context-map.md (≤150 lines)

Use `templates/context-map.md.tmpl`. Every entry must be a `topic → file`
mapping. Do not put explanations here — they belong in the target files.

Only add entries for files that actually exist. After writing, run:
```bash
python3 $SKILL_DIR/scripts/audit_context.py . --check-pointers
```
Fix any broken pointers before moving on.

### 4.4 docs/OVERVIEW.md (≤400 lines)

Apply the agentify header rule (same as Phase 4.1) to all files in phases 4.4–4.7.

Create `docs/` if needed: `mkdir -p docs`

Sections in order:
1. **Project overview** (3-5 sentences — more depth than CLAUDE.md, still concise)
2. **Architecture diagram** — Mermaid `graph TD`, ≤15 nodes (top-level components
   only; internal sub-structure belongs in component docs)
3. **Components table** — name, responsibility, key files (2-3 per component)
4. **Data flow** — Mermaid `sequenceDiagram` for the primary request/data path
5. **External dependencies** — services, databases, APIs this project calls
6. **Read more** — links to each docs/{component}.md

### 4.5 docs/{component}.md files (≤300 lines each)

One file per entry in `component_dirs` from analysis.json.

Each file contains:
- Purpose and scope (3-5 sentences)
- Key files table (path, one-line description)
- Internal architecture (Mermaid `graph LR` if >3 sub-files)
- Important patterns (3-5 conventions actually used in this component)
- Gotchas (look in git log for repeated fixes in this directory:
  `git log --oneline -- {component_path}/ | head -20`)
- See also (cross-links to related component docs)

### 4.6 docs/NAVIGATION.md (≤50 lines)

Explains the doc system to anyone (or any agent) who opens it. Cover:
- The hierarchy and what each level is for
- How to update docs when the repo changes
- Token budget reminders
- "Run `/agentify update` to refresh all docs"

### 4.7 docs/plans/, docs/specs/, docs/reviews/ (≤80 lines README each)

Only process these if the user confirmed them during the Phase 3 pause.
Read `references/agent-coordination-guide.md` before proceeding.

1. Create directories: `mkdir -p docs/plans docs/specs docs/reviews`

2. For each directory, create a `README.md` stub using the matching template:
   - `docs/plans/README.md`   → `templates/plan.md.tmpl`
   - `docs/specs/README.md`   → `templates/spec.md.tmpl`
   - `docs/reviews/README.md` → `templates/review.md.tmpl`
   Fill `{{project_name}}` and `{{date}}`. Enforce ≤80 lines after writing.

3. **Never create or overwrite** any `*.md` file other than `README.md` in these
   directories. All other files are agent work artifacts.

4. If a coordination dir already exists with artifact files, skip `README.md`
   creation only if it already scores >80 (run `audit_context.py`); otherwise
   regenerate the stub but leave artifact files untouched.

5. Add to CLAUDE.md navigation table (only for dirs actually created):
   ```
   | Implementation plans | docs/plans/ |
   | Feature specs        | docs/specs/ |
   | Review findings      | docs/reviews/ |
   ```

6. Fill the `{{optional_coordination_section:...}}` block in `context-map.md`
   (it will be included because dirs exist now).

---

## Phase 5: Verify

### 5.1 Token budget check
```bash
wc -l CLAUDE.md .claude/rules/*.md .claude/context-map.md docs/*.md docs/plans/README.md docs/specs/README.md docs/reviews/README.md 2>/dev/null | sort -rn
```
Print any file over budget. Fix immediately (trim by moving content down).

### 5.2 Pointer consistency check
```bash
python3 $SKILL_DIR/scripts/audit_context.py . --check-pointers
```
Every `see {file}` / `read {file}` reference in CLAUDE.md and context-map.md
must point to a file that exists on disk. Report and fix any broken pointers.

### 5.3 Self-consistency check
Verify manually:
- Every Navigation table row in CLAUDE.md has a corresponding file on disk
- Every component listed in docs/OVERVIEW.md has a `docs/{component}.md`
- Every `.claude/rules/*.md` has at least one `paths:` glob matching real files
- docs/NAVIGATION.md exists and explains the system
- Every coordination dir in the CLAUDE.md navigation table has a README.md on disk
- context-map.md "Agent Coordination" section only appears if dirs were created
- Every agentify-managed file has an agentify header (`<!-- agentify:`) on line 1

Print:
```
VERIFICATION COMPLETE
─────────────────────
Files generated/updated: {N}
Broken pointers fixed:   {N}
Token budget violations: {N} (all resolved)
```

---

## Phase 6: Lock and Complete

Write `.agentify-lock` (JSON):
```json
{
  "date": "YYYY-MM-DD",
  "skill_version": "1.4.0",
  "project_name": "...",
  "project_type": "...",
  "files_created": [...],
  "files_updated": [...],
  "files_kept": [...],
  "coordination_dirs": ["docs/plans", "docs/specs", "docs/reviews"]
}
```
Omit `coordination_dirs` entirely if no coordination dirs were created.

Print the final summary:
```
agentify complete
────────────────────
Created:  {list}
Updated:  {list}
Kept:     {list}

Cold-start navigation:
  Entry point       → CLAUDE.md (always loaded)
  Architecture      → docs/OVERVIEW.md
  Components        → docs/{name}.md
  Domain rules      → .claude/rules/ (auto-loaded by Claude Code)
  Find anything     → .claude/context-map.md
  Agent coordination → docs/plans/, docs/specs/, docs/reviews/ (if created)
```

Emit the parseable completion signal:
```
DONE: agentify — {N} files created/updated for {project_name} ({project_type})
```
