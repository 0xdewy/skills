# Worker Prompts

Load with `../common/patterns/worker-slice.md` only at dispatch or review.

## Dispatch

```text
You are worker <id> in a project-manager run.
OBJECTIVE: <slice>
DEPENDENCIES: <accepted inputs>
ALLOWED WRITES: <paths>
OUTPUT: <workspace>/workers/<id>/
ACCEPTANCE: <criteria>
VERIFY: <command>

Follow the worker-slice contract. Do not broaden scope or spawn agents.
```

## Review

```text
Review worker <id> only against its acceptance criteria, owned paths, diff, and
verification evidence. Return ACCEPT or NEEDS_REVISION with cited defects and
one minimal revision request. Do not edit files.
```

## Competing Candidate

```text
Build candidate <id> in isolation. Use the shared acceptance criteria and
verification commands. Optimize only for <declared angle>. Do not inspect or
copy another candidate.
```
