---
name: agentify
description: >-
  Maps git-tracked code with a ranked outline, scoped expansion, and
  symbol or call-site XREFs. Only use when explicitly requested.
license: MIT
disable-model-invocation: true
metadata:
  author: iamky1e
  version: 2.0.0
  category: meta
  activation: explicit
  tags:
    - code-map
    - repo-map
    - context-management
    - llm-navigation
    - lazy-context
    - tree-sitter
    - codebase-indexing
    - progressive-disclosure
---

# Agentify

Generate a live, read-only code map from git-tracked source so agents can load
only the context they need.

Use `scripts/repo_map.py`. Do not write
repo files, cache under home, call network APIs, or inspect ignored/generated
trees.

## Commands

- OUTLINE: `python3 scripts/repo_map.py`.
- EXPAND: `python3 scripts/repo_map.py --expand <file|area>`.
- XREF: `python3 scripts/repo_map.py --xref <symbol>`.

## Workflow

1. Confirm repo root and git availability.
2. Generate from current tracked source, excluding build/cache/vendor dirs.
3. Return the cheapest useful view first; expand only on request.
4. Include file paths and definition line numbers.

Use `vfs-docs` for human-facing docs.
