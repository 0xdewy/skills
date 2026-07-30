# Skills

AI behavior packs that coding agents can load for specialized roles — spawning a
dialectic council to debate an implementation, or a Playwright tester that
exercises every feature of an app without writing a single assertion. Skills
are closer to workflows than prompt templates: they define phases, roles, and
completion signals, not just what to say.

---

## Install

First, install the `skill` CLI to your system:

```bash
./install.sh
```

This copies `skill` to a directory on your PATH so you can use it from anywhere.

```bash
skill install-all            # install every skill in this repo
skill install <path|url>     # install one skill from a local dir or git URL
skill remove  <name>         # remove one
skill list                   # list installed skills
skill update  <name>         # pull latest for git-cloned skills
```

See [INSTALL.md](INSTALL.md) for Python and system requirements.

---


Every skill declares when it activates and when it stays silent:

```yaml
description: Does X. TRIGGER on: "audit my design", "fix the UI".
             SKIP on: "performance issues", "add a backend endpoint".
```

When your message matches a TRIGGER phrase, the agent loads that skill.
When it matches a SKIP phrase, the agent ignores it. That's the idea.

```
You: "audit my app's design"
Agent: [loads frontend-ux-designer skill]
Agent: "Evaluating layout consistency, typography, color, spacing..."
```

---

## The Skills

**Orchestration** — skills that spawn and coordinate multiple sub-agents:

| Skill | What it does |
|---|---|
| [implementer](skills/implementer/SKILL.md) | Implement → blind Skeptic pass + scored Review → Fix loop until 10/10 quality |
| [one-shot-project](skills/one-shot-project/SKILL.md) | Full project builder: Architect, PM, parallel implementers, tester |
| [code-smellz](skills/code-smellz/SKILL.md) | Parallel bug-hunter, simplifier, optimizer, and security auditor |
| [shrinkray](skills/shrinkray/SKILL.md) | Reduces codebase to its smallest correct form: dead code, ghost files, duplication, verbosity |
| [brainstormers](skills/brainstormers/SKILL.md) | Dialectical thinker sub-agents debate ideas until convergence |
| [startup-ideation](skills/startup-ideation/SKILL.md) | Parallel idea engines + Champion-vs-Assassin dialectic rank startup concepts |
| [researcher](skills/researcher/SKILL.md) | Rigorous literature research with adversarial Proponent/Falsifier and cited synthesis |

**Quality** — skills that demand excellence through adversarial refinement:

| Skill | What it does |
|---|---|
| [student-counsel](skills/student-counsel/SKILL.md) | Student works, philosophers review in dialectic rounds until consensus |

**Frontend & Testing** — browser-based QA and design auditing:

| Skill | What it does |
|---|---|
| [frontend-twerkin](skills/frontend-twerkin/SKILL.md) | Starts the app, tests every feature with Playwright, auto-fixes failures |
| [frontend-ux-designer](skills/frontend-ux-designer/SKILL.md) | Design audit: layout, typography, color, spacing; produces critique + fixes |

**Knowledge & Reference** — skills that bring deep domain expertise:

| Skill | What it does |
|---|---|
| [teach-me](skills/teach-me/SKILL.md) | Learn any codebase with Mermaid diagrams |
| [rust-evm](skills/rust-evm/SKILL.md) | EVM internals: revm, Foundry, bytecode, Yul, gas optimization |
| [hyperliquid](skills/hyperliquid/SKILL.md) | Hyperliquid developer reference: HyperCore/HyperEVM APIs, signing, HIPs |
| [polymarketv2](skills/polymarketv2/SKILL.md) | Polymarket v2 APIs and SDKs: Gamma, Data, CLOB, auth, orders |
| [web-scraping](skills/web-scraping/SKILL.md) | Playwright, httpx, anti-bot evasion, pagination, structured extraction |
| [simple-memory](skills/simple-memory/SKILL.md) | Persistent factual memory for skills in an append-only JSONL store |

**Voice** — skills that shape how the agent speaks:

| Skill | What it does |
|---|---|
| [ego](skills/ego/SKILL.md) | Confident, non-sycophantic voice: commit when warranted, cut ritual hedging |

**Meta** — skills that create, curate, and constrain other skills:

| Skill | What it does |
|---|---|
| [skill-creator](skills/skill-creator/SKILL.md) | Create, test, and publish new skills |
| [agentify](skills/agentify/SKILL.md) | Layered agent-doc system for a repo: CLAUDE.md, .claude/rules/, context-map, docs hierarchy |

---

## Design Principles

A few things I've found useful when building skills:

> **Composable.** Skills can call skills. Every skill emits a `DONE:` completion
> signal so orchestrators know when a sub-agent has finished and what it
> produced. One skill can spawn another — `code-smellz` dispatches four parallel
> auditors, each of which is itself a skill-like role.

> **Dialectic.** Structured disagreement often surfaces what agreement misses. Several
> skills use adversarial review — sub-agents that genuinely argue with each
> other — to surface flaws a single pass would miss. `student-counsel` won't
> accept work until a council of philosophers reaches consensus that it is
> beautiful. `implementer` includes a blind Skeptic pass that reviews the
> output without seeing the original question — flaws that survive context
> collapse under it.

> **Self-critical.** Several skills — `skill-creator`, `code-smellz`,
> `student-counsel` — include mechanisms for revising not just the output
> but the process itself. A skill that can't improve itself misses its own
> potential.

---

## Creating a Skill

Skills are `SKILL.md` files with YAML frontmatter that declare their name,
description, and activation contract:

```markdown
---
name: my-skill
description: What it does. TRIGGER on: "these phrases". SKIP on: "those phrases".
---

## Phase 0: Understand the problem
## Phase 1: Do the work
## Phase 2: Verify

DONE: <output> — <summary>
```

To create one properly, use the skill that knows how:

```
Use the skill-creator skill
```

Or read [skills/skill-creator/SKILL.md](skills/skill-creator/SKILL.md) directly.

---

MIT License. See [LICENSE](LICENSE).
