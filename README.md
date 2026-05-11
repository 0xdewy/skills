# Skills

AI behavior packs that transform coding agents into specialized roles. Spawn a
dialectic council that debates your implementation, or a Playwright tester that
exercises every feature of your app without writing a single assertion. Skills
are not prompt templates — they teach agents *how* to work, not just what to
say.

---

## Install

```bash
./install-skills.sh
```

The interactive installer detects Claude, OpenCode, and Hermes and symlinks
skills into each. For CI or scripting:

```bash
./install-skills.sh --install-all    # install everything
./install-skills.sh --list           # see what's installed
```

You can also use the standalone `skill` CLI from anywhere:

```bash
skill install ./skills/my-skill    # install a local skill
skill remove my-skill              # remove one
skill list                         # show installed skills
```

See [INSTALL.md](INSTALL.md) for Python and system requirements.

---

## How Skills Work

Every skill declares when it activates and when it stays silent:

```yaml
description: Does X. TRIGGER on: "audit my design", "fix the UI".
             SKIP on: "performance issues", "add a backend endpoint".
```

When your message matches a TRIGGER phrase, the agent loads that skill.
When it matches a SKIP phrase, the agent ignores it. That's the contract.

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
| [implementer](skills/implementer/SKILL.md) | Implement → Review → Fix loop until 10/10 quality |
| [one-shot-project](skills/one-shot-project/SKILL.md) | Full project builder: Architect, PM, parallel implementers, tester |
| [code-smellz](skills/code-smellz/SKILL.md) | Parallel bug-hunter, simplifier, optimizer, and security auditor |
| [brainstormers](skills/brainstormers/SKILL.md) | Dialectical thinker sub-agents debate ideas until convergence |
| [dialectic-council](skills/dialectic-council/SKILL.md) | Multi-model debate: Claude + DeepSeek, OpenAI, Gemini, MiniMax |

**Quality** — skills that demand excellence through adversarial refinement:

| Skill | What it does |
|---|---|
| [platonic-beauty](skills/platonic-beauty/SKILL.md) | Execute tasks with beauty as the supreme constraint; Socratic review |
| [oracle-skeptic](skills/oracle-skeptic/SKILL.md) | Generator proposes answers; Skeptic hunts flaws until none remain |
| [look-for-flaws](skills/look-for-flaws/SKILL.md) | Submit work to a dialectic of philosophers; only beauty passes |

**Frontend & Testing** — browser-based QA and design auditing:

| Skill | What it does |
|---|---|
| [frontend-twerkin](skills/frontend-twerkin/SKILL.md) | Starts the app, tests every feature with Playwright, auto-fixes failures |
| [frontend-ux-designer](skills/frontend-ux-designer/SKILL.md) | Design audit: layout, typography, color, spacing; produces critique + fixes |

**Knowledge & Reference** — skills that bring deep domain expertise:

| Skill | What it does |
|---|---|
| [teach-me](skills/teach-me/SKILL.md) | Socratic masterclass on any codebase with Mermaid diagrams |
| [rust-evm](skills/rust-evm/SKILL.md) | EVM internals: revm, Foundry, bytecode, Yul, gas optimization |
| [prediction_markets](skills/prediction_markets/SKILL.md) | Polymarket and Kalshi: APIs, CLOB trading, auth, order types |
| [web-scraping](skills/web-scraping/SKILL.md) | Playwright, httpx, anti-bot evasion, pagination, structured extraction |

**Meta** — skills that create, curate, and constrain other skills:

| Skill | What it does |
|---|---|
| [skill-creator](skills/skill-creator/SKILL.md) | Create, test, and publish new skills |
| [stakeholder-of-last-resort](skills/stakeholder-of-last-resort/SKILL.md) | Speaks for absent parties facing foreseeable harm in decisions |

---

## Philosophy

Skills are not prompt templates. A prompt template says *what to say*. A skill
says *how to think* — it defines phases, roles, convergence criteria, and
completion signals.

> **Composable.** Skills call skills. Every skill emits a `DONE:` completion
> signal so orchestrators know when a sub-agent has finished and what it
> produced. One skill can spawn another — `code-smellz` dispatches four parallel
> auditors, each of which is itself a skill-like role.

> **Dialectic.** The best ideas emerge from structured disagreement. Several
> skills use adversarial review — sub-agents that genuinely argue with each
> other — to surface flaws a single pass would miss. `platonic-beauty` won't
> accept work until a council of philosophers reaches consensus that it is
> beautiful. `oracle-skeptic` pits a Generator against a Skeptic who has never
> seen the original question.

> **Self-critical.** Skills decay. The `skill-creator`, `code-smellz`, and
> `platonic-beauty` skills all include mechanisms for revising not just the
> output but the process itself. A skill that can't improve itself is already
> obsolete.

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
