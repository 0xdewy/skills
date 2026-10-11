#!/usr/bin/env python3
"""Collect paged PR metadata, bounded branch comparisons, and declared dependencies."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import threading
import time
from urllib.parse import quote

from render import render

QUERY = '''query($owner:String!,$name:String!,$cursor:String) {
 repository(owner:$owner,name:$name) {
  nameWithOwner defaultBranchRef { name }
  pullRequests(first:50,states:OPEN,after:$cursor) {
   pageInfo { hasNextPage endCursor } totalCount
   nodes {
    number title body url isDraft author { login } headRefName headRefOid
    headRepository { nameWithOwner } baseRefName baseRef { target { oid } } baseRepository { nameWithOwner }
    additions deletions changedFiles createdAt updatedAt mergeable reviewDecision
    reviewRequests(first:10) { totalCount nodes { requestedReviewer {
     ... on User { login } ... on Team { slug }
    } } }
    comments(last:3) { totalCount nodes { body url createdAt author { login } } }
    reviewThreads(first:20) { totalCount nodes { isResolved } }
    commits(last:1) { nodes { commit { oid statusCheckRollup {
     contexts(first:30) { totalCount nodes {
      ... on CheckRun { name status conclusion detailsUrl }
      ... on StatusContext { context state targetUrl }
     } }
    } } } }
   }
  }
 }
}'''


class Failure(Exception):
    pass


class Client:
    def __init__(self):
        self.deadline = time.monotonic() + 120
        self.stopped = threading.Event()

    def call(self, endpoint, payload=None):
        for attempt in range(2):
            remaining = self.deadline - time.monotonic()
            if self.stopped.is_set() or remaining <= 0:
                raise Failure('Source stopped or 120-second collection budget reached')
            cmd = ['gh', 'api', '--hostname', 'github.com', endpoint]
            if payload is not None:
                cmd += ['--input', '-']
            try:
                result = subprocess.run(cmd, input=json.dumps(payload) if payload else None,
                                        capture_output=True, text=True, timeout=min(30, remaining))
            except subprocess.TimeoutExpired:
                message, transient = 'GitHub request timed out', True
            else:
                if result.returncode == 0:
                    try:
                        data = json.loads(result.stdout)
                    except ValueError:
                        self.stopped.set()
                        raise Failure('Invalid API JSON') from None
                    if not isinstance(data, dict) or not data.get('errors'):
                        return data
                    message, transient = 'GraphQL response contains errors', False
                else:
                    message = result.stderr.strip()[:300] or 'GitHub API failed'
                    transient = bool(re.search(r'timeout|timed out|connection|HTTP 50[234]', message, re.I))
                    if re.search(r'HTTP (401|403|404|429)|rate limit|Field .*doesn.t exist', message, re.I):
                        transient = False
            if not transient or attempt == 1:
                # A schema/auth/transport failure should not repeat across the fleet.
                self.stopped.set()
                raise Failure(message)
        raise AssertionError('unreachable')

    def inventory(self, endpoint):
        repos, page = [], 1
        while True:
            try:
                rows = self.call(f'{endpoint}?per_page=100&page={page}')
            except Failure as error:
                return repos, str(error)
            repos.extend(r['full_name'] for r in rows)
            if len(rows) < 100:
                return repos, None
            page += 1

    def repository(self, name):
        owner, repo = name.split('/')
        prs, cursor, branch = [], None, None
        while True:
            try:
                data = self.call('graphql', {'query': QUERY, 'variables': {
                    'owner': owner, 'name': repo, 'cursor': cursor}})
                row = data['data']['repository']
                if row is None:
                    raise Failure('Repository unavailable')
            except Failure as error:
                return name, branch, prs, str(error)
            branch = (row['defaultBranchRef'] or {}).get('name')
            page = row['pullRequests']
            prs.extend(page['nodes'])
            if not page['pageInfo']['hasNextPage']:
                return name, branch, prs, None
            cursor = page['pageInfo']['endCursor']


def declared_dependencies(body, name, url):
    """Only explicit dependency lines; references elsewhere are not dependencies."""
    found = {}
    body = re.sub(r'<!--.*?-->', '', body or '', flags=re.S)
    body = re.sub(r'(?ms)^\s*(`{3,}|~{3,}).*?^\s*\1[^\n]*', '', body)
    for line in body.splitlines():
        match = re.match(r'^\s*(?:[-*]\s+)?(?:depends on|blocked by)\s*:?\s+(.+)', line, re.I)
        if not match:
            continue
        refs = re.findall(r'https://github\.com/([\w.-]+/[\w.-]+)/pull/(\d+)\b|(?<![\w/])(?:([\w.-]+/[\w.-]+))?#(\d+)\b', match[1])
        for full_repo, full_num, short_repo, short_num in refs:
            repo, number = full_repo or short_repo or name, full_num or short_num
            target = f'github.com/{repo}#{number}'
            found[target] = {'label': f'Declared dependency · {repo}#{number}', 'target': target,
                             'url': f'https://github.com/{repo}/pull/{number}',
                             'evidenceUrl': url, 'evidence': line.strip()}
    return list(found.values())


def compare_branch(client, repo, node):
    """Pin comparisons to captured SHAs so a moving branch cannot change the pair."""
    state = node['branchState']
    for field in ('ahead', 'behind', 'status', 'url'):
        state.pop(field, None)
    if not state.get('baseOid') or not state.get('headOid'):
        state['error'] = 'Base or head SHA unavailable'
        return
    pair = quote(state['baseOid'], safe='') + '...' + quote(state['headOid'], safe='')
    try:
        result = client.call(f'repos/{repo}/compare/{pair}?per_page=1')
        ahead, behind = result.get('ahead_by'), result.get('behind_by')
        if any(type(value) is not int or value < 0 for value in (ahead, behind)):
            raise Failure('Comparison returned no valid divergence counts')
    except Failure as error:
        state['error'] = str(error)
        return
    state.update(ahead=ahead, behind=behind, status=result.get('status'),
                 url=f'https://github.com/{repo}/compare/{pair}')
    state.pop('error', None)


def resolve_dependencies(client, repos):
    """Resolve only declared targets, without expanding the repository fleet."""
    cache = {n['id']: {'state': 'OPEN'} for r in repos for n in r['nodes'] if n['kind'] == 'pr'}
    for repo in repos:
        for node in repo['nodes']:
            for dep in node.get('dependencies', []):
                target = dep['target']
                if target not in cache:
                    name, number = target.removeprefix('github.com/').split('#')
                    try:
                        result = client.call(f'repos/{name}/pulls/{number}')
                        state = 'MERGED' if result.get('merged_at') else {'open': 'OPEN', 'closed': 'CLOSED'}.get(result.get('state'), 'UNKNOWN')
                        cache[target] = {'state': state}
                    except Failure as error:
                        cache[target] = {'state': 'UNKNOWN', 'error': str(error)}
                dep.update(cache[target])


def normalize(name, branch, prs, error):
    prefix = 'github.com/' + name
    branches, nodes, heads = {}, [], {}
    def base_node(repo, ref):
        key = f'github.com/{repo}:branch:{ref}'
        branches[key] = {'id': key, 'kind': 'branch', 'title': ref}
        return key
    if branch:
        base_node(name, branch)
    for pr in prs:
        head_repo = (pr.get('headRepository') or {}).get('nameWithOwner')
        heads.setdefault((head_repo, pr['headRefName']), []).append(pr['number'])
    for pr in prs:
        details, signals = [], []
        def detail(label, text, url=None):
            details.append({'label': label, 'text': str(text), 'url': url})
        def signal(label, tone='neutral'):
            signals.append({'label': label, 'tone': tone})
        base_repo = (pr.get('baseRepository') or {}).get('nameWithOwner', name)
        parents = heads.get((base_repo, pr['baseRefName']), [])
        parent = f'{prefix}#{parents[0]}' if len(parents) == 1 and parents[0] != pr['number'] else base_node(base_repo, pr['baseRefName'])
        if len(parents) > 1:
            detail('Base ambiguity', 'Multiple open parents: '+str(parents))
        if pr['isDraft']:
            signal('Draft')
        if pr['mergeable'] == 'CONFLICTING':
            signal('Conflicts', 'bad')
        elif pr['mergeable'] == 'UNKNOWN':
            signal('Mergeability unknown', 'warn')
        decision = pr['reviewDecision'] or 'No review decision'
        signal(decision, 'bad' if decision == 'CHANGES_REQUESTED' else 'neutral')
        detail('Mergeability', pr['mergeable'])
        detail('Head SHA', pr['headRefOid'])
        commits = pr['commits']['nodes']
        commit = commits[0]['commit'] if commits else {}
        contexts = (commit.get('statusCheckRollup') or {}).get('contexts')
        checks = contexts['nodes'] if contexts else []
        if commit.get('oid') != pr['headRefOid']:
            checks = []
            signal('Head checks unverified', 'warn')
        elif not checks:
            signal('No reported checks', 'warn')
        counts = {}
        for check in checks:
            state = check.get('conclusion') or check.get('status') or check.get('state') or 'UNKNOWN'
            counts[state] = counts.get(state, 0) + 1
            detail(check.get('name') or check.get('context'), state, check.get('detailsUrl') or check.get('targetUrl'))
        for state, count in counts.items():
            tone = 'bad' if state in {'FAILURE', 'ERROR', 'TIMED_OUT', 'ACTION_REQUIRED'} else 'good' if state == 'SUCCESS' else 'warn'
            signal(f'{count} checks: {state}', tone)
        if contexts and contexts['totalCount'] > len(contexts['nodes']):
            signal('Checks partial', 'warn')
            detail('Check coverage', f"{len(contexts['nodes'])}/{contexts['totalCount']}")
        threads = pr['reviewThreads']
        unresolved = sum(not t['isResolved'] for t in threads['nodes'])
        partial = len(threads['nodes']) < threads['totalCount']
        signal(f'{"≥" if partial else ""}{unresolved} unresolved threads' + (' · partial' if partial else ''), 'warn' if unresolved or partial else 'neutral')
        detail('Thread coverage', f"{len(threads['nodes'])}/{threads['totalCount']}; thread text not collected")
        comments = pr['comments']
        detail('Conversation comments', f"{comments['totalCount']} total; latest {len(comments['nodes'])} shown")
        for comment in comments['nodes']:
            detail(f"Comment · {(comment['author'] or {}).get('login', 'deleted')} · {comment['createdAt']}", comment['body'], comment['url'])
        requests = pr['reviewRequests']
        detail('Requested reviewers', f"{requests['totalCount']} total; " + json.dumps(requests['nodes']))
        signal('Readiness unverified')
        node = {'id': f"{prefix}#{pr['number']}", 'kind': 'pr', 'parent': parent,
                'head': pr['headRefName'], 'base': pr['baseRefName'],
                'headRepo': (pr.get('headRepository') or {}).get('nameWithOwner'),
                'baseRepo': base_repo,
                'branchState': {'headOid': pr['headRefOid'],
                                'baseOid': ((pr.get('baseRef') or {}).get('target') or {}).get('oid'),
                                'mergeable': pr['mergeable'], 'error': 'Comparison not collected'},
                'dependencies': declared_dependencies(pr.get('body'), name, pr['url']),
                'author': (pr['author'] or {}).get('login', 'deleted'), 'files': pr['changedFiles'],
                'signals': signals, 'details': details}
        for field in ['number', 'title', 'url', 'additions', 'deletions', 'createdAt', 'updatedAt']:
            node[field] = pr[field]
        nodes.append(node)
    by_id = {n['id']: n for n in nodes}
    for node, pr in zip(nodes, prs):
        seen, current = set(), node['id']
        while current in by_id:
            if current in seen:
                node['parent'] = base_node(name, pr['baseRefName'])
                node['details'].append({'label': 'Base cycle', 'text': 'Cycle detected; shown under base branch'})
                break
            seen.add(current)
            current = by_id[current]['parent']
    return {'name': name, 'summary': f'{len(prs)} open PRs collected' + (' · INCOMPLETE' if error else ''),
            'nodes': list(branches.values()) + nodes}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument('--repo', action='append', help='Explicit owner/repo; repeat for a fleet')
    scope.add_argument('--org', help='Explicit GitHub organization')
    scope.add_argument('--team', help='Explicit org/team-slug')
    parser.add_argument('--out', required=True, type=Path, help='Output directory')
    args = parser.parse_args()
    names = args.repo or [args.team or args.org]
    pattern = r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+' if args.repo or args.team else r'[A-Za-z0-9_.-]+'
    if any(not re.fullmatch(pattern, n) for n in names):
        parser.error('Use explicit GitHub names, not URLs or local paths')
    client = Client()
    args.out.mkdir(parents=True, exist_ok=True)
    data = {'scope': 'GitHub · ' + ', '.join(names) + ' · all authors · open PRs',
            'collectedAt': datetime.now(timezone.utc).isoformat(), 'repos': [],
            'gaps': ['Open PR branches only; branches without open PRs, rebase history, protections, manifest pins, closed parents, local work, and review-thread text not collected. Dependencies cover explicit “Depends on” / “Blocked by” PR-body lines only; absent links do not prove independence. Readiness unverified.']}
    inventory_error = None
    if args.repo:
        repos = list(dict.fromkeys(args.repo))
    else:
        endpoint = f'orgs/{args.org}/repos' if args.org else 'orgs/{}/teams/{}/repos'.format(*args.team.split('/'))
        repos, inventory_error = client.inventory(endpoint)
    if inventory_error:
        data['gaps'].append('Inventory incomplete: ' + inventory_error)
    completed = 0
    template = (Path(__file__).resolve().parents[1] / 'assets/dashboard.html').read_text()
    def save():
        nodes = [n for r in data['repos'] for n in r['nodes'] if n['kind'] == 'pr']
        compared = sum('behind' in n['branchState'] for n in nodes)
        data['coverage'] = f'{completed}/{len(repos)} discovered repositories fully collected; ' + ('inventory incomplete' if inventory_error else 'inventory complete') + f'. Branch comparisons {compared}/{len(nodes)}; missing comparisons are unknown. Nested checks/threads/reviewers are bounded; partial counts are labeled.'
        data['repos'].sort(key=lambda r: (-sum(n['kind'] == 'pr' for n in r['nodes']), r['name']))
        (args.out / 'snapshot.json').write_text(json.dumps(data, indent=2) + '\n')
        (args.out / 'dashboard.html').write_text(render(data, template))
    def accept(result):
        nonlocal completed
        name, branch, prs, error = result
        data['repos'].append(normalize(name, branch, prs, error))
        if error:
            data['gaps'].append(name + ': ' + error)
        else:
            completed += 1
        save()
        print(f'{name}: {len(prs)} PRs' + (' · incomplete' if error else ''), flush=True)
    save()
    # Validate the exact query before fanning out, so a schema error occurs once.
    if repos:
        accept(client.repository(repos[0]))
    if len(repos) > 1:
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(client.repository, repo) for repo in repos[1:]]
            for future in as_completed(futures):
                accept(future.result())
    # Save the full overview first; comparisons share the original network budget.
    for repo in data['repos']:
        for node in repo['nodes']:
            if node['kind'] == 'pr':
                compare_branch(client, repo['name'], node)
                save()
    resolve_dependencies(client, data['repos'])
    save()
    print((args.out / 'dashboard.html').resolve())


if __name__ == '__main__':
    main()
