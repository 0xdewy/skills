"""git-show regressions: collector batching and failure bounds, dashboard rendering."""
import copy
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "git-show" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import collect  # noqa: E402
from collect import Client, Failure, compare_branch, declared_dependencies, normalize, resolve_dependencies  # noqa: E402
from render import render  # noqa: E402

TEMPLATE = (SCRIPTS.parent / "assets/dashboard.html").read_text()
DEMO = json.loads(TEMPLATE.split('<script id="snapshot" type="application/json">')[1].split('</script>')[0])


def pr(number=1, head='topic', base='main'):
    return {'number': number, 'title': 'Fix', 'url': f'https://github.com/acme/repo/pull/{number}',
            'isDraft': False, 'author': {'login': 'someone-else'}, 'headRefName': head,
            'headRefOid': 'abc', 'headRepository': {'nameWithOwner': 'acme/repo'},
            'baseRefName': base, 'baseRepository': {'nameWithOwner': 'acme/repo'},
            'additions': 1, 'deletions': 0, 'changedFiles': 1, 'createdAt': 'now', 'updatedAt': 'now',
            'mergeable': 'UNKNOWN', 'reviewDecision': None,
            'reviewRequests': {'totalCount': 0, 'nodes': []},
            'comments': {'totalCount': 0, 'nodes': []},
            'reviewThreads': {'totalCount': 0, 'nodes': []},
            'commits': {'nodes': [{'commit': {'oid': 'abc', 'statusCheckRollup': None}}]}}


class CollectorTests(unittest.TestCase):
    def test_declared_targets_resolve_once_without_expanding_scope(self):
        p = pr()
        p['body'] = 'Depends on other/repo#4'
        repo = normalize('acme/repo', 'main', [p, dict(p, number=2)], None)
        with patch.object(Client, 'call', return_value={'state': 'closed', 'merged_at': 'now'}) as call:
            resolve_dependencies(Client(), [repo])
        self.assertEqual(call.call_count, 1)
        self.assertTrue(all(n['dependencies'][0]['state'] == 'MERGED' for n in repo['nodes'] if n['kind'] == 'pr'))
        self.assertEqual(len(repo['nodes']), 3)

    def test_comparison_uses_captured_shas_and_preserves_unknown(self):
        p = pr()
        p['baseRefOid'] = 'old-base'
        p['baseRef'] = {'target': {'oid': 'def'}}
        node = normalize('acme/repo', 'main', [p], None)['nodes'][-1]
        client = Client()
        with patch.object(client, 'call', return_value={'ahead_by': 5, 'behind_by': 3, 'status': 'diverged'}) as call:
            compare_branch(client, 'acme/repo', node)
        self.assertEqual(call.call_args.args[0], 'repos/acme/repo/compare/def...abc?per_page=1')
        self.assertEqual(node['branchState']['behind'], 3)
        self.assertNotIn('error', node['branchState'])
        with patch.object(client, 'call', side_effect=Failure('Unavailable')):
            compare_branch(client, 'acme/repo', node)
        self.assertNotIn('behind', node['branchState'])
        self.assertEqual(node['branchState']['error'], 'Unavailable')
        p['baseRef'] = None
        node = normalize('acme/repo', 'main', [p], None)['nodes'][-1]
        with patch.object(client, 'call') as call:
            compare_branch(client, 'acme/repo', node)
        call.assert_not_called()
        self.assertNotIn('behind', node['branchState'])

    def test_dependency_declarations_are_not_ancestry_or_arbitrary_mentions(self):
        body = '''Related to #2
Depends on #3, other/repo#4 and https://github.com/other/repo/pull/5
- Blocked by: #3
<!-- Depends on #6 -->
```text
Depends on #7
```
'''
        deps = declared_dependencies(body, 'acme/repo', 'https://github.com/acme/repo/pull/1')
        self.assertEqual([d['target'] for d in deps], [
            'github.com/acme/repo#3', 'github.com/other/repo#4', 'github.com/other/repo#5'])
        p = pr()
        p['body'] = body
        node = normalize('acme/repo', 'main', [p], None)['nodes'][-1]
        self.assertEqual(node['parent'], 'github.com/acme/repo:branch:main')
        self.assertEqual(node['dependencies'], deps)

    def test_repository_pages_not_per_pr(self):
        def page(nodes, more):
            return {'data': {'repository': {'defaultBranchRef': {'name': 'main'}, 'pullRequests': {
                'nodes': nodes, 'pageInfo': {'hasNextPage': more, 'endCursor': 'next'}}}}}
        client = Client()
        with patch.object(client, 'call', side_effect=[page([pr(i) for i in range(50)], True), page([pr(51)], False)]) as call:
            result = client.repository('acme/repo')
        self.assertEqual(len(result[2]), 51)
        self.assertEqual(call.call_count, 2)
        self.assertEqual(call.call_args_list[1].args[1]['variables']['cursor'], 'next')

    def test_schema_failure_stops_fleet(self):
        response = subprocess.CompletedProcess([], 1, '', "gh: Field 'detailUrl' doesn't exist on type 'CheckRun'")
        client = Client()
        with patch.object(collect.subprocess, 'run', return_value=response) as run:
            self.assertIsNotNone(client.repository('acme/one')[3])
            self.assertIsNotNone(client.repository('acme/two')[3])
        self.assertEqual(run.call_count, 1)

    def test_timeout_retries_once_then_stops(self):
        client = Client()
        with patch.object(collect.subprocess, 'run', side_effect=subprocess.TimeoutExpired('gh', 30)) as run:
            self.assertIsNotNone(client.repository('acme/one')[3])
            self.assertIsNotNone(client.repository('acme/two')[3])
        self.assertEqual(run.call_count, 2)
        self.assertLessEqual(run.call_args.kwargs['timeout'], 30)

    def test_budget_stops_without_call(self):
        client = Client()
        client.deadline = 0
        with patch.object(collect.subprocess, 'run') as run:
            self.assertIsNotNone(client.repository('acme/repo')[3])
        run.assert_not_called()

    def test_inventory_partial_failure_retains_page(self):
        client = Client()
        with patch.object(client, 'call', side_effect=[[{'full_name': f'acme/r{i}'} for i in range(100)], Failure('rate limit')]):
            repos, error = client.inventory('orgs/acme/repos')
        self.assertEqual(len(repos), 100)
        self.assertEqual(error, 'rate limit')

    def test_stack_identity_and_cycle(self):
        a, b = pr(), pr(2, 'child', 'topic')
        out = normalize('acme/repo', 'main', [a, b], None)
        self.assertEqual(out['nodes'][-1]['parent'], 'github.com/acme/repo#1')
        fork = copy.deepcopy(a)
        fork['headRepository']['nameWithOwner'] = 'fork/repo'
        out = normalize('acme/repo', 'main', [fork, b], None)
        self.assertIn(':branch:', out['nodes'][-1]['parent'])
        a['baseRefName'] = 'child'
        out = normalize('acme/repo', 'main', [a, b], None)
        self.assertTrue(any(d['label'] == 'Base cycle' for n in out['nodes'] for d in n.get('details', [])))

    def test_legacy_ci_partial_threads_and_no_author_filter(self):
        p = pr()
        p['commits']['nodes'][0]['commit']['statusCheckRollup'] = {'contexts': {
            'totalCount': 31, 'nodes': [{'context': 'legacy-ci', 'state': 'FAILURE', 'targetUrl': 'https://example.com/check'}]}}
        p['reviewThreads'] = {'totalCount': 21, 'nodes': [{'isResolved': True}]}
        n = normalize('acme/repo', 'main', [p], None)['nodes'][-1]
        labels = [s['label'] for s in n['signals']]
        self.assertIn('1 checks: FAILURE', labels)
        self.assertIn('Checks partial', labels)
        self.assertIn('≥0 unresolved threads · partial', labels)
        self.assertEqual(n['author'], 'someone-else')
        self.assertIn('Readiness unverified', labels)


class DashboardTests(unittest.TestCase):
    def test_branch_state_and_downstream_impact(self):
        data = copy.deepcopy(DEMO)
        data['repos'][0]['nodes'][1].pop('branchState', None)
        parent = data['repos'][0]['nodes'][4]
        parent.update(head='feature/parent', base='main', branchState={
            'ahead': 12, 'behind': 4, 'mergeable': 'MERGEABLE', 'headOid': 'abcdef', 'baseOid': '123456'})
        child = data['repos'][0]['nodes'][5]
        child['branchState'] = {'ahead': 2, 'behind': 0, 'mergeable': 'CONFLICTING'}
        data['repos'][0]['nodes'][2]['dependencies'][0]['state'] = 'MERGED'
        self.browser(data, '''
          const parent=document.getElementById(ids.get('b170'));
          check(parent.querySelector('.branch-path').textContent.includes('feature/parent → main'),'visible refs');
          check(parent.querySelector('.branch-state').textContent.includes('12 ahead · 4 behind'),'divergence');
          check(parent.querySelector('.impact').textContent.includes('3 descendant'),'descendant impact');
          check(parent.querySelector('.branch-state').textContent.includes('does not require a rebase'),'no false rebase requirement');
          const child=document.getElementById(ids.get('b250'));
          check(child.querySelector('.branch-state').textContent.includes('Conflicts with base'),'conflict takes precedence');
          check(child.querySelector('.branch-state').textContent.includes('parent first'),'parent first guidance');
          check(document.getElementById(ids.get('b253')).querySelector('.branch-state').textContent.includes('unknown'),'missing comparison unknown');
          check(document.getElementById(ids.get('b222')).querySelector('.dep').textContent.includes('merged · integration not verified'),'merged dependency is not integration proof');
          document.querySelector('[data-filter=dependencies]').click();
          check(document.getElementById(ids.get('br60')),'retains dependency target');
          check(!document.getElementById(ids.get('s27')),'hides unrelated PR');
          document.querySelector('[data-filter=branch]').click();
          check(document.getElementById(ids.get('b170')),'branch attention');
        ''')

    def test_invalid_topology(self):
        for nodes in ([{'id': 'a', 'kind': 'pr', 'parent': 'missing'}],
                      [{'id': 'a', 'kind': 'pr', 'parent': 'a'}],
                      [{'id': 'a', 'kind': 'pr'}, {'id': 'a', 'kind': 'branch'}]):
            with self.subTest(nodes=nodes), self.assertRaises(ValueError):
                render({'repos': [{'nodes': nodes}]}, TEMPLATE)
        with self.assertRaises(ValueError):
            render({'repos': [{'nodes': [{'id': 'a', 'kind': 'branch'}]}] * 2}, TEMPLATE)

    def browser(self, snapshot, assertions, width=1440):
        chromium = shutil.which('chromium')
        if not chromium:
            self.skipTest('Chromium unavailable')
        script = '''<script>
        try {
          const check=(value,message)=>{if(!value)throw Error(message)};
        ''' + assertions + '''
          document.body.dataset.test='PASS';
        } catch(error) {document.body.dataset.test='FAIL: '+error.message;}
        </script>'''
        with tempfile.TemporaryDirectory(prefix='git-show-test-') as folder:
            path = Path(folder) / 'test.html'
            path.write_text(render(snapshot, TEMPLATE).replace('</html>', script + '</html>'))
            result = subprocess.run([chromium, '--headless', '--no-sandbox', '--disable-gpu',
                                     '--dump-dom', f'--window-size={width},1000', path.as_uri()],
                                    capture_output=True, text=True, timeout=30, check=True)
        status = re.search(r'data-test="([^"]*)"', result.stdout)
        self.assertEqual(status.group(1) if status else 'Test script did not complete', 'PASS')

    def test_tree_filters_and_dependencies(self):
        self.browser(DEMO, '''
          check(document.querySelectorAll('.repo').length===3,'repository count');
          check(document.querySelectorAll('.row').length===13,'PR count');
          document.querySelector('[data-filter=bad]').click();
          check(document.getElementById(ids.get('b-main')),'retains base');
          check(document.getElementById(ids.get('b234')),'retains failing child');
          check(!document.getElementById(ids.get('b253')),'hides unmatched sibling');
          document.querySelector('[data-filter=all]').click();
          const search=document.getElementById('search');search.value='numbered HD';
          search.dispatchEvent(new Event('input'));
          check(document.getElementById(ids.get('b170')),'retains search ancestor');
          document.querySelector('.dep a').click();
          check(document.getElementById(ids.get('br60')),'dependency reveals target');
          check(location.hash==='#'+ids.get('br60'),'dependency navigates to target');
          document.querySelector('[data-filter=draft]').click();
          check(document.getElementById(ids.get('s27')),'draft with changes requested');
          check(!document.getElementById(ids.get('b253')),'non-draft hidden');
        ''')

    def test_hostile_content(self):
        data = copy.deepcopy(DEMO)
        node = data['repos'][0]['nodes'][1]
        node['title'] = '</script><img src=x onerror=alert(1)>'
        node['url'] = 'javascript:alert(1)'
        node['details'] = [{'label': 'Feedback', 'text': '<svg onload=alert(2)>', 'url': 'data:text/html,bad'}]
        self.browser(data, '''
          check(!document.querySelector('img,svg'),'untrusted text became markup');
          check(!document.querySelector('a[href^="javascript:"],a[href^="data:"]'),'unsafe URL');
          check(document.querySelector('.name').textContent.includes('onerror=alert(1)'),'title preserved as text');
        ''')

    def test_empty_and_inaccessible_scope(self):
        self.browser({'scope': 'private org', 'collectedAt': '2026-09-09T00:00:00Z',
                      'coverage': '0 accessible repositories; inventory incomplete',
                      'gaps': ['Repository access denied'], 'repos': []}, '''
          check(!document.getElementById('empty').hidden,'empty state');
          check(document.getElementById('notices').textContent.includes('denied'),'access gap');
          check(document.querySelectorAll('.repo').length===0,'fabricated repository');
        ''')

    def test_narrow_layout(self):
        self.browser(DEMO, '''
          check(document.documentElement.scrollWidth<=innerWidth,'page overflow');
          check([...document.querySelectorAll('.tree')].every(x=>getComputedStyle(x).overflowX==='auto'),'tree scrolling');
        ''', width=500)


if __name__ == '__main__':
    unittest.main()
