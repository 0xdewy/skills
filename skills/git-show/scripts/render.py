#!/usr/bin/env python3
"""Embed a collected Git Show snapshot in a portable, offline dashboard."""
import argparse
import json
from pathlib import Path


def render(snapshot, template):
    ids = set()
    for repo in snapshot['repos']:
        nodes = {n['id']: n for n in repo['nodes']}
        if len(nodes) != len(repo['nodes']) or ids.intersection(nodes):
            raise ValueError('Node IDs must be globally unique')
        ids.update(nodes)
        for node in nodes.values():
            if node['kind'] not in {'branch', 'pr'}:
                raise ValueError('Node kind must be branch or pr')
            seen = {node['id']}
            parent = node.get('parent')
            while parent is not None:
                if parent not in nodes:
                    raise ValueError(f'Missing parent: {parent}')
                if parent in seen:
                    raise ValueError(f'Cycle at: {parent}')
                seen.add(parent)
                parent = nodes[parent].get('parent')
    marker = '<script id="snapshot" type="application/json">'
    start = template.index(marker) + len(marker)
    end = template.index('</script>', start)
    # An HTML parser recognizes </script> even inside JSON strings.
    payload = json.dumps(snapshot, ensure_ascii=True).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    return template[:start] + '\n' + payload + '\n' + template[end:]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('snapshot', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    template = Path(__file__).resolve().parents[1] / 'assets' / 'dashboard.html'
    args.output.write_text(render(json.loads(args.snapshot.read_text()), template.read_text()))
    print(args.output.resolve())


if __name__ == '__main__':
    main()
