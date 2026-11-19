"""Path-only replay of the supplied Git inventories (Python 3.6+)."""
import ast
import collections
import gzip
import json
from pathlib import Path
import re
import sys


def rules(script):
    tree = ast.parse(script.read_text())
    scope = {'re': re}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            if node.targets[0].id in ('SUBSTR', 'DIRRE', 'KEEPDIRRE', 'PATHRE'):
                module = ast.parse('')
                module.body = [node]
                exec(compile(module, str(script), 'exec'), scope)
        elif isinstance(node, ast.FunctionDef) and node.name in ('protected_dir', 'excluded_dir'):
            module = ast.parse('')
            module.body = [node]
            exec(compile(module, str(script), 'exec'), scope)
    return scope


def parse(line):
    size, sha, path = line.rstrip('\n').split(' ', 2)
    if path.startswith('"'):
        path = ast.literal_eval(path).encode('latin1').decode('utf8', 'surrogateescape')
    parts = path.split('/')
    if parts[0] != 'lane_code':
        return int(size), 'repository', path
    if parts[1] == 'orch_n30':
        return int(size), '/'.join(parts[1:3]), '/'.join(parts[3:])
    return int(size), parts[1], '/'.join(parts[2:])


def excluded(path, scope):
    parts = path.split('/')
    for i, name in enumerate(parts[:-1]):
        q = '/' + '/'.join(parts[:i+1]) + '/'
        if scope['excluded_dir'](name, q):
            return q.strip('/')
    # The existing substring gate also applies to filenames. No extension/size gate.
    if any(s in '/' + path for s in scope['SUBSTR']):
        return 'file-substring:' + '/'.join(parts[:-1])
    return None


def main():
    package = Path(__file__).resolve().parents[1]
    inventories = Path(sys.argv[1]) if len(sys.argv) > 1 else package.parent / 'in/commits'
    scope = rules(package / 'tools/lane_code_filter.py')
    rows, totals, groups = [], {}, {}
    labels = ['trinity-1-18', 'trinity-2-28', 'trinity-3-30', 'orch_n30/tools', 'orch_n30/briefs', 'repository']
    for source in sorted(inventories.glob('*.gz')):
        commit = source.name.split('_')[1]
        counts = {label: [0, 0, 0, 0] for label in labels}
        buckets = {'kept': collections.Counter(), 'excluded': collections.Counter(),
                   'kept_parents': collections.Counter(), 'excluded_roots': collections.Counter()}
        with gzip.open(str(source), 'rt') as stream:
            for line in stream:
                size, label, path = parse(line)
                reject = excluded(path, scope) if label != 'repository' else None
                row = counts.setdefault(label, [0, 0, 0, 0])
                row[0] += 1; row[1] += size
                if not reject:
                    row[2] += 1; row[3] += size
                key = 'excluded' if reject else 'kept'
                # Nonoverlapping buckets: label plus first five directory components.
                group = label + '/' + '/'.join(path.split('/')[:-1][:5])
                buckets[key][group] += size
                if reject:
                    buckets['excluded_roots'][label + '/' + reject] += size
                else:
                    buckets['kept_parents'][label + '/' + '/'.join(path.split('/')[:-1])] += size
        for label, values in sorted(counts.items()):
            rows.append([commit, label] + values)
        totals[commit] = [sum(v[i] for v in counts.values()) for i in range(4)]
        groups[commit] = {key: value.most_common() for key, value in buckets.items()}
    result = dict(rows=rows, totals=totals, groups=groups,
                  largest_commit=max(totals, key=lambda c: totals[c][1]))
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
