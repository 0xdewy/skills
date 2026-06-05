#!/usr/bin/env python3
"""Query a JSONL memory file by content, tags, entities, type, or time range.

Usage:
    python retrieve.py [--query "search terms"] [--tag "tag"]
                       [--entity "entity"] [--type "fact"]
                       [--after "2024-01-01"] [--before "2025-01-01"]
                       [--limit 20] [--file path/to/memory.jsonl]
                       [--include-consolidated]
"""

import argparse
import json
import os
import sys
from datetime import datetime


def load_entries(filepath):
    """Read all JSON lines from file, skipping comments and blank lines."""
    entries = []
    if not os.path.exists(filepath):
        return entries
    with open(filepath, "r") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            try:
                entries.append(json.loads(stripped))
            except json.JSONDecodeError:
                continue
    return entries


def parse_date(date_str):
    """Parse a date string like 2024-01-01 or 2024-01-01T00:00:00Z."""
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date: {date_str}")


def matches(entry, query, tag, entity, entry_type, after, before,
            include_consolidated):
    """Check if an entry matches all specified filter criteria."""
    if not include_consolidated and entry.get("consolidated_into") is not None:
        return False

    if query:
        content = entry.get("content", "")
        if query.lower() not in content.lower():
            return False

    if tag:
        entry_tags = [t.lower() for t in entry.get("tags", [])]
        if tag.lower() not in entry_tags:
            return False

    if entity:
        entry_entities = [e.lower() for e in entry.get("entities", [])]
        if entity.lower() not in entry_entities:
            return False

    if entry_type:
        if entry.get("type", "").lower() != entry_type.lower():
            return False

    if after or before:
        ts = entry.get("timestamp", "")
        if not ts:
            return False
        try:
            entry_dt = parse_date(ts[:19])
        except ValueError:
            return False
        if after and entry_dt < after:
            return False
        if before and entry_dt > before:
            return False

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Query a JSONL memory file"
    )
    parser.add_argument("--query", default=None,
                        help="Case-insensitive substring search on content")
    parser.add_argument("--tag", default=None, help="Filter by exact tag match")
    parser.add_argument("--entity", default=None, help="Filter by exact entity match")
    parser.add_argument("--type", default=None, dest="entry_type",
                        help="Filter by entry type")
    parser.add_argument("--after", default=None,
                        help="Only entries with timestamp >= this (ISO date)")
    parser.add_argument("--before", default=None,
                        help="Only entries with timestamp <= this (ISO date)")
    parser.add_argument("--limit", type=int, default=20,
                        help="Max entries to return (default: 20)")
    parser.add_argument("--file", default="memory/memory.jsonl", dest="filepath",
                        help="Path to the JSONL memory file")
    parser.add_argument("--include-consolidated", action="store_true",
                        help="Include entries that have been consolidated into a summary")
    args = parser.parse_args()

    try:
        after_dt = parse_date(args.after) if args.after else None
    except ValueError as e:
        print(f"Error parsing --after: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        before_dt = parse_date(args.before) if args.before else None
    except ValueError as e:
        print(f"Error parsing --before: {e}", file=sys.stderr)
        sys.exit(1)

    entries = load_entries(args.filepath)
    results = []

    for entry in entries:
        if matches(entry, args.query, args.tag, args.entity, args.entry_type,
                   after_dt, before_dt, args.include_consolidated):
            results.append(entry)
            if len(results) >= args.limit:
                break

    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
