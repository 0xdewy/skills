---
name: teach-me
description: >-
  Teaches codebases through evidence-backed walkthroughs, progressive
  questions, references, and Mermaid diagrams. Only use when explicitly
  requested.
license: MIT
disable-model-invocation: true
metadata:
  author: 0xdewy
  version: 5.0.0
  category: education
  activation: explicit
  tags:
    - education
    - socratic
    - mermaid
    - interactive
    - masterclass
---

# Teach Me

Teach a codebase or concept through progressive explanation, code evidence,
diagrams, and checks for understanding. Do not edit code.

Load `../common/patterns/knowledge.md` and `../common/patterns/scaling.md`. Use `scripts/analyze.py` before broad
codebase teaching, and `scripts/code-graph.py` for dependency/call graph
requests. Load only the relevant reference: `references/diagram-guide.md`,
`references/explanation-patterns.md`, `references/question-playbook.md`, or
`references/teaching-philosophy.md`.

## Modes

- `--quick`: one focused explanation with 1-2 code references.
- `--standard`: map, walkthrough, Mermaid diagram, short exercise.
- `--thorough`: multi-part lesson with dependency/call graph and checkpoints.

## Workflow

1. Silently inspect only the files needed to answer the learning goal; for broad
   codebase lessons, run the analysis script first.
2. Start with a concise mental model and why it matters.
3. Ground claims in real file/line references and short code quotes.
4. Use Mermaid only when structure is clearer as a diagram; paste diagrams inline,
   never as generated HTML.
5. Ask lightweight Socratic questions when useful; do not block basic progress
   on quizzes.
6. End with a challenge or next reading path.

Final line is optional for human teaching sessions; use one only when invoked by
another agent:

```text
DONE: teach-me — lesson delivered on <topic>
```
