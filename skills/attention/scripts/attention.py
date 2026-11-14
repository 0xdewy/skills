#!/usr/bin/env python3
"""List the open pull requests that need the signed-in GitHub user.

Reads GitHub through `gh api graphql`, or a saved response with --input.
"""
import argparse
import json
import subprocess
import sys

QUERY = """
query {
  mine: search(query: "is:pr is:open author:@me archived:false", type: ISSUE, first: 100) {
    issueCount
    nodes { ... on PullRequest {
      url title isDraft mergeable mergeStateStatus reviewDecision
      commits(last: 1) { nodes { commit { statusCheckRollup { state } } } }
      reviewThreads(first: 100) { nodes { isResolved } }
    } }
  }
  asked: search(query: "is:pr is:open review-requested:@me archived:false", type: ISSUE, first: 100) {
    issueCount
    nodes { ... on PullRequest { url title } }
  }
}
"""

# Printed in this order: what blocks other people first.
GROUPS = [
    ("review", "Review requested from you"),
    ("changes", "Changes requested on your PR"),
    ("threads", "Unresolved review threads"),
    ("conflict", "Conflicts with the base branch"),
    ("checks", "Checks failing"),
    ("behind", "Behind the base branch"),
    ("merge", "Approved and ready to merge"),
]


def reasons(pr):
    """Return the group keys that apply to one of the user's own PRs."""
    found = []
    if pr.get("reviewDecision") == "CHANGES_REQUESTED":
        found.append("changes")
    open_threads = sum(1 for t in pr["reviewThreads"]["nodes"] if not t["isResolved"])
    if open_threads:
        found.append("threads")
    if pr.get("mergeable") == "CONFLICTING":
        found.append("conflict")
    commits = pr["commits"]["nodes"]
    rollup = (commits[0]["commit"].get("statusCheckRollup") or {}) if commits else {}
    if rollup.get("state") in ("FAILURE", "ERROR"):
        found.append("checks")
    if pr.get("mergeStateStatus") == "BEHIND":
        found.append("behind")
    if pr.get("reviewDecision") == "APPROVED" and not found and not pr.get("isDraft"):
        found.append("merge")
    return found


def report(data):
    groups = {key: [] for key, _ in GROUPS}
    for pr in data["asked"]["nodes"]:
        groups["review"].append(pr)
    mine = data["mine"]["nodes"]
    for pr in mine:
        for key in reasons(pr):
            groups[key].append(pr)
    lines = []
    for key, title in GROUPS:
        if not groups[key]:
            continue
        lines.append(f"{title} ({len(groups[key])})")
        for pr in groups[key]:
            draft = " [draft]" if pr.get("isDraft") else ""
            lines.append(f"  {pr['url']}{draft}  {pr['title']}")
        lines.append("")
    own = {pr["url"] for key, prs in groups.items() if key != "review" for pr in prs}
    lines.append(
        f"{len(own)} of your {len(mine)} open PRs need you; "
        f"{len(groups['review'])} from others wait for your review."
    )
    unknown = sum(1 for pr in mine if pr.get("mergeable") == "UNKNOWN")
    if unknown:
        lines.append(f"GitHub has not computed conflicts for {unknown} yet; run again in a minute.")
    for part in ("mine", "asked"):
        if data[part]["issueCount"] > len(data[part]["nodes"]):
            lines.append(f"Only the first {len(data[part]['nodes'])} of {data[part]['issueCount']} were checked.")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", help="saved GraphQL response to read instead of calling gh")
    args = parser.parse_args()
    if args.input:
        with open(args.input) as handle:
            payload = json.load(handle)
    else:
        command = ["gh", "api", "graphql", "-f", f"query={QUERY}"]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:  # GitHub sometimes returns an empty body once
            result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            sys.exit(f"gh failed: {result.stderr.strip()}")
        payload = json.loads(result.stdout)
    print(report(payload["data"]))


if __name__ == "__main__":
    main()
