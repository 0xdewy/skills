---
name: simple-memory
description: >-
  Persistent factual memory for LLM skills. Stores, retrieves, and consolidates
  knowledge in an append-only JSONL file. Use when the user explicitly wants
  persisted memory: "remember this", "store this for later", "save this note",
  "what have you stored about X", "search my saved memories", "recall my note
  about X", "consolidate my saved notes", or "summarize my memories". SKIP on:
  ordinary web lookups, codebase/file searches, casual mentions of memory,
  browser history, CPU/RAM memory, or any query where "look up" means search
  current files or the internet rather than saved skill memory.
license: MIT
metadata:
  author: 0xdewy
  version: 1.1.0
  category: memory
  tags:
    - memory
    - persistence
    - jsonl
    - retrieval
    - consolidation
---

# Simple Memory

A persistent memory system for skills that need to remember facts, user
preferences, patterns, and insights across sessions. Based on the SimpleMem
architecture, it uses an append-only JSONL store with three operations:
store, retrieve, and consolidate.

## Why This Exists

LLM agents with fixed context windows cannot retain information across
sessions. Storing raw conversation logs creates unbounded, low-density
context. Simple Memory compresses observations into self-contained units
at write time, keeps retrieval fast with deterministic filters, and
supports consolidation to prevent the active index from growing unbounded.

## Storage Location

Default file: `memory/memory.jsonl` (relative to the directory containing this SKILL.md)

If the file does not exist, create it as an empty file. Lines beginning
with `#` are treated as comments and skipped by the scripts. Each data
line is one JSON record.

## Memory Format

Each line in the JSONL file is one JSON object with these fields:

```json
{"id": "mem-2026-05-13-001", "timestamp": "2026-05-13T14:30:00Z", "type": "fact|pattern|event|preference|insight", "content": "Self-contained statement with pronouns resolved and times absolute", "entities": ["entity-names"], "tags": ["keywords"], "source": "user|observation|skill-name", "consolidated_into": null}
```

Fields:
- **id**: `mem-YYYY-MM-DD-NNN`, stable and unique
- **timestamp**: ISO-8601 UTC of capture time
- **type**: `fact`, `pattern`, `event`, `preference`, or `insight`
- **content**: One self-contained sentence. Pronouns resolved to entity names, relative times converted to absolute ISO-8601. Must remain intelligible without original conversational context.
- **entities**: Named entity strings this memory concerns
- **tags**: Lowercase keywords for retrieval and clustering (1-5 typical)
- **source**: Who produced this — `user`, `observation`, or a skill name
- **consolidated_into**: `null` normally; set to summary entry ID after consolidation

The canonical format specification is at `skills/common/memory-guide.md`.

## Privacy and Scope

Default to the invoking skill's own `memory/memory.jsonl`. Do not read another
skill's memory file unless the user explicitly asks for cross-skill recall or the
other skill's instructions explicitly require it for the current task.

Do not store secrets, credentials, access tokens, private keys, government IDs,
or sensitive personal data unless the user explicitly asks to save that exact
information and understands it will be persisted in plaintext JSONL.

## Operations

### Store — when the user shares a fact, preference, or observation

Triggers: "remember X", "store this", "save that", "note to self", any
explicit request to persist information, or when the skill discovers a
pattern worth keeping.

Run `scripts/store.py` with the content, tags, type, entities, and source.
The script normalizes the input: it requires you to resolve pronouns to
entity names and convert relative times to absolute ISO-8601 timestamps
*in the content string you pass*. The script handles ID generation,
timestamping, near-duplicate detection, and JSONL append.

```
python scripts/store.py \
  --content "User prefers dark mode in all editors" \
  --tags "preference,editor,theme" \
  --type "preference" \
  --entities "user" \
  --source "user"
```

If a near-duplicate exists (identical or very similar content), the script
prints the existing record and exits without appending. Override with
`--force` to write anyway.

### Retrieve — when the user asks about past information

Triggers: "what do I know about X", "do you remember", "recall",
"look up", "what did I say about", "find the note about", any query
about stored information.

Run `scripts/retrieve.py` with filters:

```
# By content search
python scripts/retrieve.py --query "dark mode" --limit 10

# By tag
python scripts/retrieve.py --tag "preference" --limit 20

# By entity + time range
python scripts/retrieve.py --entity "user" --after "2026-01-01"

# Combined
python scripts/retrieve.py --query "editor" --type "preference" --limit 5
```

The script returns matching entries as a JSON array. For complex queries
(multi-hop reasoning, temporal questions), use the script output as a
candidate set and apply LLM semantic ranking to select only the truly
relevant entries. This mirrors SimpleMem's adaptive retrieval: narrow
scope for simple lookups, broader candidate set for complex reasoning.

### Consolidate — when the memory file accumulates many related entries

Triggers: "consolidate my memories", "summarize my notes", "clean up
memory", or when the file grows past ~100 entries with obvious clusters.

1. Run `scripts/consolidate.py` to find candidate clusters:
   ```
   python scripts/consolidate.py --min-cluster 3 --tag-overlap 0.6
   ```
   The script groups entries whose tag sets share Jaccard overlap above
   the threshold. It only outputs candidate groups; it never modifies
   the file.

2. For each cluster, read the entry contents and synthesize a higher-level
   abstract entry. Example: 12 entries about "ordered latte at 8am" →
   "User regularly drinks coffee in the morning". Write the abstract
   entry with `type: "pattern"` and `source: "consolidation"`.

3. Run `scripts/consolidate.py --mark-consolidated <summary-id> --ids <id1,id2,...>`
   to update each original entry's `consolidated_into` field. This rewrites
   the file (a backup is saved to `memory.jsonl.bak`). Do NOT delete the
   originals — they serve as an archive for detailed recall.

## Cross-Skill Usage

Every skill that needs persistent memory should:
1. Create its own `memory/memory.jsonl` (empty file).
2. Read `skills/common/memory-guide.md` for the canonical format.
3. Use the bundled scripts (`store.py`, `retrieve.py`, `consolidate.py`)
   or reimplement them following the same JSONL format.

Because the format is identical across skills, cross-skill memory is possible,
but it is permissioned. Ask before reading another skill's memory file and state
which file will be read. Prefer copying only the specific retrieved facts needed
for the current task into the response or working notes.

## Completion Format

End memory operations with one of:

```
DONE: memory/memory.jsonl — stored 1 memory
DONE: memory/memory.jsonl — retrieved N memories for "<query>"
DONE: memory/memory.jsonl — consolidated N memories into <summary-id>
```

## Scripts

All scripts are zero-dependency (Python stdlib only) and live in
`scripts/`:

| Script | Purpose |
|--------|---------|
| `store.py` | Append a memory entry to the JSONL file |
| `retrieve.py` | Query entries by content, tag, entity, type, or time range |
| `consolidate.py` | Find clusters of related entries by tag overlap |

Each script supports `--help` for usage. They read from and write to
`memory/memory.jsonl` by default; use `--file` to specify an alternate
path.

The scripts handle the deterministic work: appending, grep-filtering,
and cluster-finding. The LLM handles the intelligent work: normalizing
raw user input into self-contained memory units, semantic near-duplicate
detection, summarization during consolidation, and semantic ranking
during complex retrieval.

## Templates

`templates/memory.jsonl` is an empty starter file with a commented
example entry showing the format.
