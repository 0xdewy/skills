#!/usr/bin/env python3
"""Append a self-contained memory entry to a JSONL file.

Usage:
    python store.py --content "text" --tags "tag1,tag2" --type "fact"
                    [--entities "e1,e2"] [--source "user"]
                    [--file path/to/memory.jsonl] [--force]
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone


def generate_id(date_str, existing_ids):
    """Generate mem-YYYY-MM-DD-NNN based on existing entries for the same date."""
    prefix = f"mem-{date_str}-"
    max_n = 0
    for eid in existing_ids:
        if eid.startswith(prefix):
            try:
                n = int(eid[len(prefix):])
                if n > max_n:
                    max_n = n
            except ValueError:
                pass
    return f"{prefix}{max_n + 1:03d}"


def load_existing_entries(filepath):
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


def content_similarity(a, b):
    """Simple similarity check: ratio of shared words to total unique words."""
    words_a = set(re.findall(r"\w+", a.lower(), re.UNICODE))
    words_b = set(re.findall(r"\w+", b.lower(), re.UNICODE))
    if not words_a or not words_b:
        return 0.0
    union = words_a | words_b
    intersection = words_a & words_b
    return len(intersection) / len(union)


def find_near_duplicate(content, existing_entries, threshold=0.85):
    """Check if content is identical or very similar to any existing entry."""
    content_lower = content.strip().lower()
    for entry in existing_entries:
        existing_content = entry.get("content", "").strip().lower()
        if not existing_content:
            continue
        if content_lower == existing_content:
            return entry
        sim = content_similarity(content, existing_content)
        if sim >= threshold:
            return entry
    return None


def validate_fields(content, tags, entry_type):
    """Ensure required fields are present and valid."""
    valid_types = {"fact", "pattern", "event", "preference", "insight"}
    errors = []
    if not content or not content.strip():
        errors.append("--content is required and must not be empty")
    if not tags:
        errors.append("--tags is required")
    if entry_type not in valid_types:
        errors.append(f"--type must be one of: {', '.join(sorted(valid_types))}")
    return errors


def main():
    parser = argparse.ArgumentParser(
        description="Append a memory entry to a JSONL file"
    )
    parser.add_argument("--content", required=True, help="Self-contained memory content")
    parser.add_argument("--tags", required=True, help="Comma-separated tag keywords")
    parser.add_argument("--type", required=True, dest="entry_type",
                        help="Type: fact, pattern, event, preference, insight")
    parser.add_argument("--entities", default="", help="Comma-separated entity names")
    parser.add_argument("--source", default="user", help="Source: user, observation, or skill name")
    parser.add_argument("--file", default="memory/memory.jsonl", dest="filepath",
                        help="Path to the JSONL memory file")
    parser.add_argument("--force", action="store_true",
                        help="Write even if a near-duplicate exists")
    args = parser.parse_args()

    content = args.content.strip()
    tags = [t.strip().lower() for t in args.tags.split(",") if t.strip()]
    entry_type = args.entry_type.strip().lower()
    entities = [e.strip() for e in args.entities.split(",") if e.strip()]
    source = args.source.strip()

    errors = validate_fields(content, tags, entry_type)
    if errors:
        print("Validation errors:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(1)

    existing = load_existing_entries(args.filepath)
    existing_ids = [e.get("id", "") for e in existing]

    if not args.force:
        dup = find_near_duplicate(content, existing)
        if dup:
            print(json.dumps(dup, indent=2))
            print(
                f"Near-duplicate found (id={dup['id']}). Use --force to write anyway.",
                file=sys.stderr,
            )
            sys.exit(2)

    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    timestamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    entry = {
        "id": generate_id(date_str, existing_ids),
        "timestamp": timestamp,
        "type": entry_type,
        "content": content,
        "entities": entities,
        "tags": tags,
        "source": source,
        "consolidated_into": None,
    }

    os.makedirs(os.path.dirname(args.filepath) or ".", exist_ok=True)
    with open(args.filepath, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(json.dumps(entry, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
