# Persistent Memory Pattern

Skills accumulate factual knowledge, user preferences, and discovered
patterns in an append-only JSONL store so they build a queryable knowledge
base across sessions without unbounded context growth.

## Architecture

```
memory/
  memory.jsonl       ← append-only, one JSON record per line
```

A single file. No indexes, no secondary stores. The JSONL format is chosen
because it is append-only (no full-file parse to write), grep-friendly
(search lines without parsing), and trivially script-parseable in any
language.

## Storage Format

Each line is one JSON object:

```json
{"id": "mem-2026-05-13-001", "timestamp": "2026-05-13T14:30:00Z", "type": "fact|pattern|event|preference|insight", "content": "Self-contained statement with pronouns resolved and times absolute", "entities": ["entity-names"], "tags": ["keywords"], "source": "user|observation|skill-name", "consolidated_into": null}
```

Every field except `consolidated_into` is required on write. Field meanings:

- **id**: unique, stable; pattern `mem-YYYY-MM-DD-NNN` (date + zero-padded
  auto-increment per date). Stable IDs let other records reference this one.
- **timestamp**: ISO-8601 UTC when the memory was captured, not when the
  described event occurred.
- **type**: one of `fact` (discrete truth), `pattern` (recurring observation),
  `event` (something that happened), `preference` (user likes/dislikes),
  `insight` (derived conclusion).
- **content**: a single self-contained sentence. Ambiguous pronouns
  ("he"/"it") must be resolved to named entities. Relative times ("next
  Tuesday") must be converted to absolute ISO-8601. The content must remain
  intelligible without its original conversational context.
- **entities**: list of named entity strings this memory concerns.
- **tags**: list of lowercase keyword strings for retrieval and clustering.
  Prefer nouns over verbs; 1–5 tags is typical.
- **source**: who or what produced this memory — `user`, `observation`, or a
  skill name.
- **consolidated_into**: null normally. When a consolidation step replaces
  this record with an abstract summary, set to the ID of the summary record.

## Store

Store is the only frequent write operation. JSONL is chosen because it
supports append-only writes: no full-file parse, no in-place editing, no
risk of corrupting existing data.

When capturing new information:

1. Normalize the input into a self-contained unit: resolve all pronoun
   references to entity names, convert relative times to absolute ISO-8601
   timestamps, and prune low-entropy filler (pleasantries, confirmations).
   This is the SimpleMem "semantic structured compression" idea — each
   memory unit must stand alone.
2. Assign a type, extract entities, and choose 1–5 tags.
3. Check for near-duplicates: if a record with identical or very similar
   content already exists, skip the write or update the existing record's
   timestamp. Exact deduplication can be done by script; semantic near-duplicate
   detection is an LLM judgment call.
4. Generate an ID (`mem-<today>-<next-number>`), set the timestamp to now,
   append the JSON line to `memory/memory.jsonl`.

## Retrieve

Basic retrieval is deterministic and script-driven:

- Filter by tag, entity, type, or time range (after/before).
- Full-text case-insensitive substring search on the content field.
- Limit to N most recent entries.

For complex queries (multi-hop, temporal reasoning), the LLM should rank the
script-filtered results semantically, selecting only the entries actually
relevant to the question. This mirrors SimpleMem's "adaptive query-aware
retrieval": narrow scope for simple lookups, broader for complex reasoning.

## Consolidate

When the memory file accumulates many low-level observations about the same
topic, run consolidation:

1. Script identifies candidate clusters: groups of entries whose tag sets
   share Jaccard overlap above a threshold (default 0.6), with at least N
   entries per cluster (default 3).
2. The LLM reviews each cluster and produces a higher-level abstract entry
   (e.g., 15 "ordered latte" records → "User regularly drinks coffee in the
   morning"). This is the SimpleMem "recursive consolidation" step.
3. The script marks each original entry's `consolidated_into` field to
   reference the new summary's ID via `consolidate.py --mark-consolidated`.
   This is an explicit maintenance operation (infrequent, user-triggered)
   that rewrites the file — a backup is saved to `memory.jsonl.bak` first.
   Do NOT delete the originals — they remain as an archive for detailed
   recall.

Consolidation keeps the active knowledge surface compact without losing
fidelity — detailed records are archived in-place, retrievable on demand.

## Cross-Skill Usage

Each skill maintains its own `memory/memory.jsonl`. The format is identical
across all skills, so any skill can read any other skill's memory file for
cross-skill awareness. A skill that needs persistent factual knowledge
declares a `memory/` directory and follows this guide.

Skills that only need performance tracking should use the episodic memory
pattern (`learnings/episodic.md`) instead.

## When to Use

Use persistent memory when:
- The skill needs to remember facts, user preferences, or discovered patterns
  across sessions.
- The stored information is useful for retrieval (not just self-improvement).
- The volume justifies structured storage with querying.

Use episodic memory (rolling-window learnings file) when:
- The skill only needs recent performance observations.
- The information is for the skill's own refinement, not user queries.
- Context budget is tight and a 10-line window suffices.

The two systems are complementary. A skill may use both: episodic for
self-improvement, persistent for knowledge that serves user queries.
