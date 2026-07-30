#!/usr/bin/env python3
"""Find and manage consolidation of related memory entries by tag overlap.

Usage:
    # Find candidate clusters (read-only)
    python consolidate.py [--file path/to/memory.jsonl]
                          [--min-cluster 3] [--tag-overlap 0.6]

    # Mark entries as consolidated into a summary entry
    python consolidate.py --mark-consolidated mem-YYYY-MM-DD-NNN
                          --ids mem-2026-05-13-001,mem-2026-05-13-002
                          [--file path/to/memory.jsonl]

The first mode outputs candidate groups as JSON for LLM review.
The second mode updates originals to point to the summary — it reads
the file, modifies matching entries, and rewrites. This is a
destructive write; a backup is saved to memory.jsonl.bak first.
"""

import argparse
import json
import os
import sys
import shutil


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


def write_entries(filepath, entries):
    """Rewrite the entire JSONL file atomically via temp file and rename."""
    tmp_path = filepath + ".tmp"
    with open(tmp_path, "w") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    os.replace(tmp_path, filepath)


def jaccard(set_a, set_b):
    """Compute Jaccard similarity between two sets."""
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union)


def find_clusters(entries, min_cluster, tag_overlap):
    """Group entries into clusters based on tag overlap.

    Uses a greedy algorithm: for each entry, find all other entries whose
    tag sets have Jaccard >= tag_overlap. Build connected components from
    these pairwise relationships. Only return components with >= min_cluster
    entries.
    """
    n = len(entries)
    tag_sets = [set(e.get("tags", [])) for e in entries]

    adjacency = {i: set() for i in range(n)}
    for i in range(n):
        for j in range(i + 1, n):
            if jaccard(tag_sets[i], tag_sets[j]) >= tag_overlap:
                adjacency[i].add(j)
                adjacency[j].add(i)

    visited = set()
    clusters = []

    for i in range(n):
        if i in visited or not adjacency[i]:
            continue
        component = []
        stack = [i]
        while stack:
            node = stack.pop()
            if node in visited:
                continue
            visited.add(node)
            component.append(node)
            for neighbor in adjacency[node]:
                if neighbor not in visited:
                    stack.append(neighbor)
        if len(component) >= min_cluster:
            clusters.append(sorted(component))

    clusters.sort(key=lambda c: len(c), reverse=True)
    return clusters


def main():
    parser = argparse.ArgumentParser(
        description="Find and manage consolidation of memory entries"
    )
    parser.add_argument("--file", default="memory/memory.jsonl", dest="filepath",
                        help="Path to the JSONL memory file")
    parser.add_argument("--min-cluster", type=int, default=3,
                        help="Minimum entries per cluster (default: 3)")
    parser.add_argument("--tag-overlap", type=float, default=0.6,
                        help="Jaccard threshold for tag similarity (default: 0.6)")
    parser.add_argument("--mark-consolidated", default=None,
                        help="ID of the consolidated summary entry to mark originals with")
    parser.add_argument("--ids", default=None,
                        help="Comma-separated IDs of entries to mark as consolidated")
    args = parser.parse_args()

    # --- Mark-consolidated mode ---
    if args.mark_consolidated:
        if not args.ids:
            print("--ids is required with --mark-consolidated", file=sys.stderr)
            sys.exit(1)

        target_ids = set(i.strip() for i in args.ids.split(",") if i.strip())
        if not target_ids:
            print("--ids must contain at least one entry ID", file=sys.stderr)
            sys.exit(1)

        entries = load_entries(args.filepath)
        if not entries:
            print("No entries found in file", file=sys.stderr)
            sys.exit(1)

        # Verify consolidated ID exists
        consolidated_entry = None
        for e in entries:
            if e.get("id") == args.mark_consolidated:
                consolidated_entry = e
                break
        if not consolidated_entry:
            print(
                f"Consolidated entry {args.mark_consolidated} not found in file",
                file=sys.stderr,
            )
            sys.exit(1)

        updated = 0
        for e in entries:
            if e.get("id") in target_ids:
                e["consolidated_into"] = args.mark_consolidated
                updated += 1

        missing = target_ids - {e.get("id") for e in entries}
        if missing:
            print(
                f"Warning: {len(missing)} IDs not found: {', '.join(sorted(missing))}",
                file=sys.stderr,
            )

        # Create backup before rewriting
        backup_path = args.filepath + ".bak"
        try:
            shutil.copy2(args.filepath, backup_path)
        except OSError:
            pass

        write_entries(args.filepath, entries)
        print(json.dumps({
            "consolidated_into": args.mark_consolidated,
            "updated_count": updated,
            "updated_ids": sorted(target_ids & {e.get("id") for e in entries}),
            "backup": backup_path,
        }, indent=2))
        return

    # --- Find-clusters mode ---
    entries = load_entries(args.filepath)

    if not entries:
        print("[]")
        return

    active_entries = [
        (i, e) for i, e in enumerate(entries)
        if e.get("consolidated_into") is None
    ]

    if not active_entries:
        print("[]")
        return

    active_indices = [i for i, _ in active_entries]
    active_only = [e for _, e in active_entries]
    clusters = find_clusters(active_only, args.min_cluster, args.tag_overlap)

    output = []
    for cluster in clusters:
        group = [entries[active_indices[idx]] for idx in cluster]
        output.append(group)

    print(json.dumps(output, indent=2, ensure_ascii=False))
    print(
        f"Found {len(output)} cluster(s) across {len(entries)} total entries "
        f"({len(active_entries)} active).",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
