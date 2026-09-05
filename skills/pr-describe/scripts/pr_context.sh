#!/usr/bin/env bash
# Gather everything needed to describe a pull request into one directory.
#
# Usage:
#   pr_context.sh [<number|url|branch>] --out DIR       existing PR, via gh
#   pr_context.sh --base <ref> [--head <ref>] --out DIR  no PR yet: local diff
#
# Writes meta.json, body.md, commits.txt, stat.txt, diff.patch, issues.md,
# template.md, and me.txt. Every file is created, possibly empty, so callers
# can rely on the layout. Read-only: never edits the PR or the worktree.
set -euo pipefail

out="" base="" head="" pr=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --out) out="$2"; shift 2 ;;
    --base) base="$2"; shift 2 ;;
    --head) head="$2"; shift 2 ;;
    -h|--help) sed -n '2,10p' "$0"; exit 0 ;;
    *) pr="$1"; shift ;;
  esac
done
[[ -n "$out" ]] || { echo "error: --out DIR is required" >&2; exit 2; }
mkdir -p "$out"

write_template() {
  local root
  root=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
  : > "$out/template.md"
  local f
  for f in "$root/.github/PULL_REQUEST_TEMPLATE.md" "$root/.github/pull_request_template.md" \
           "$root/PULL_REQUEST_TEMPLATE.md" "$root/docs/PULL_REQUEST_TEMPLATE.md"; do
    if [[ -f "$f" ]]; then cat "$f" > "$out/template.md"; return; fi
  done
  if [[ -d "$root/.github/PULL_REQUEST_TEMPLATE" ]]; then
    for f in "$root"/.github/PULL_REQUEST_TEMPLATE/*; do
      { echo "<!-- $(basename "$f") -->"; cat "$f"; echo; } >> "$out/template.md"
    done
  fi
}

if [[ -n "$base" ]]; then
  head="${head:-HEAD}"
  range="$base...$head"
  git log --format='%h %s%n%b' "$range" > "$out/commits.txt"
  git diff -M --stat "$range" > "$out/stat.txt"
  git diff -M "$range" > "$out/diff.patch"
  : > "$out/body.md"
  : > "$out/issues.md"
  git config user.name > "$out/me.txt" 2>/dev/null || : > "$out/me.txt"
  python3 - "$out" "$base" "$head" <<'PY'
import json, sys
out, base, head = sys.argv[1:4]
meta = {"mode": "local", "number": None, "title": "", "url": "", "author": "",
        "base": base, "head": head, "labels": [], "closingIssues": []}
json.dump(meta, open(f"{out}/meta.json", "w"), indent=2)
PY
  write_template
  echo "wrote $out (local diff $range)"
  exit 0
fi

command -v gh >/dev/null || {
  echo "error: gh is required for PR mode; use --base <ref> for a local diff" >&2; exit 2; }

fields='number,title,body,url,author,baseRefName,headRefName,baseRefOid,headRefOid'
fields="$fields,labels,closingIssuesReferences,commits,files,isDraft,additions,deletions"
if [[ -n "$pr" ]]; then
  gh pr view "$pr" --json "$fields" > "$out/raw.json"
else
  gh pr view --json "$fields" > "$out/raw.json"
fi

python3 - "$out" <<'PY'
import json, sys
out = sys.argv[1]
raw = json.load(open(f"{out}/raw.json"))
meta = {
    "mode": "pr", "number": raw["number"], "title": raw["title"], "url": raw["url"],
    "author": raw["author"]["login"], "base": raw["baseRefName"], "head": raw["headRefName"],
    "baseSha": raw.get("baseRefOid"), "headSha": raw.get("headRefOid"),
    "isDraft": raw.get("isDraft"), "labels": [l["name"] for l in raw.get("labels", [])],
    "closingIssues": [i["number"] for i in raw.get("closingIssuesReferences", [])],
    "additions": raw.get("additions"), "deletions": raw.get("deletions"),
    "files": [f["path"] for f in raw.get("files", [])],
}
json.dump(meta, open(f"{out}/meta.json", "w"), indent=2)
open(f"{out}/body.md", "w").write(raw.get("body") or "")
with open(f"{out}/commits.txt", "w") as fh:
    for c in raw.get("commits", []):
        fh.write(f"{c['oid'][:8]} {c['messageHeadline']}\n")
        if c.get("messageBody"):
            fh.write(c["messageBody"].rstrip() + "\n")
        fh.write("\n")
# Stat with rename detection when both commits exist locally; else gh's file list.
import subprocess
b, h = meta["baseSha"], meta["headSha"]
have = lambda sha: sha and subprocess.run(["git", "cat-file", "-e", sha], capture_output=True).returncode == 0
if have(b) and have(h):
    stat = subprocess.run(["git", "diff", "-M", "--stat", f"{b}...{h}"], capture_output=True, text=True).stdout
else:
    rows = sorted(raw.get("files", []), key=lambda f: -(f.get("additions", 0) + f.get("deletions", 0)))
    stat = "".join(f"{f['path']}  +{f.get('additions', 0)} -{f.get('deletions', 0)}\n" for f in rows)
    stat += "(rename detection unavailable: base/head commits not fetched locally)\n"
open(f"{out}/stat.txt", "w").write(stat)
PY

# gh refuses diffs over 300 files; fall back to fetching the PR and diffing locally.
diff_ok=0
if [[ -n "$pr" ]]; then
  gh pr diff "$pr" > "$out/diff.patch" 2> "$out/.diff-err" && diff_ok=1
else
  gh pr diff > "$out/diff.patch" 2> "$out/.diff-err" && diff_ok=1
fi
if [[ $diff_ok -eq 0 ]]; then
  read -r num base_branch base_sha head_sha < <(python3 -c "import json;m=json.load(open('$out/meta.json'));print(m['number'],m['base'],m['baseSha'],m['headSha'])")
  git fetch -q origin "pull/$num/head" 2>/dev/null || true
  git fetch -q origin "$base_branch" 2>/dev/null || true
  if git cat-file -e "$base_sha" 2>/dev/null && git cat-file -e "$head_sha" 2>/dev/null; then
    git diff -M "$base_sha...$head_sha" > "$out/diff.patch"
    git diff -M --stat "$base_sha...$head_sha" > "$out/stat.txt"
  else
    { echo "diff unavailable: $(tr -d '\n' < "$out/.diff-err")"
      echo "stat.txt lists the files; fetch the PR locally for hunks"; } > "$out/diff.patch"
  fi
fi
rm -f "$out/.diff-err"

python3 - "$out" <<'PY'
import json, subprocess, sys
out = sys.argv[1]
meta = json.load(open(f"{out}/meta.json"))
with open(f"{out}/issues.md", "w") as fh:
    for n in meta["closingIssues"]:
        r = subprocess.run(["gh", "issue", "view", str(n), "--json", "number,title,body"],
                           capture_output=True, text=True)
        if r.returncode:
            fh.write(f"## #{n}\n\n(unavailable: {r.stderr.strip()})\n\n")
            continue
        i = json.loads(r.stdout)
        fh.write(f"## #{i['number']}: {i['title']}\n\n{i.get('body') or ''}\n\n")
PY

gh api user --jq .login > "$out/me.txt" 2>/dev/null || : > "$out/me.txt"
write_template
echo "wrote $out (PR $(python3 -c "import json;m=json.load(open('$out/meta.json'));print(f\"#{m['number']} by {m['author']}\")"))"
