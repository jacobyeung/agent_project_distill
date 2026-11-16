"""Lane-path ratchet for the trainer tree: count literal lane paths per file and compare with a baseline.

    python3 -m tools.treegit.lane_paths --root trainer              # print counts as JSON
    python3 -m tools.treegit.lane_paths --root trainer --check      # compare with LANE_PATH_BASELINE.json
    python3 -m tools.treegit.lane_paths --root trainer --write-baseline

A file fails when its count rises above the baseline or when a file absent from the baseline holds a
literal. Counts may fall freely; rewrite the baseline after a tree build lowers them. Python 3.6 safe.
"""
import argparse
import json
import os
import sys

from tools.orchkit.util import read_json, write_json

LITERALS = ('/scratch/jjyeung/orch_', '/home/jjyeung/', '/data2/jjyeung/')
SKIP_DIRS = ('.git', '__pycache__', 'artifacts')
BASELINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'LANE_PATH_BASELINE.json')


def count_literals(text):
    return sum(text.count(lit) for lit in LITERALS)


def scan(root):
    """Map each relative *.py path under root that holds a literal to its literal count."""
    counts = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for name in sorted(filenames):
            if not name.endswith('.py'):
                continue
            path = os.path.join(dirpath, name)
            with open(path, 'rb') as handle:
                n = count_literals(handle.read().decode('utf-8', 'replace'))
            if n:
                counts[os.path.relpath(path, root).replace(os.sep, '/')] = n
    return counts


def compare(baseline, counts):
    """Return one message per file whose count rose or that is new; empty when the ratchet holds."""
    bad = []
    for rel in sorted(counts):
        if rel not in baseline:
            bad.append('%s: new file holds %d lane-path literal(s)' % (rel, counts[rel]))
        elif counts[rel] > baseline[rel]:
            bad.append('%s: %d lane-path literal(s), baseline %d' % (rel, counts[rel], baseline[rel]))
    return bad


def load_baseline(path=BASELINE):
    return read_json(path)['counts']


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--root', required=True)
    ap.add_argument('--baseline', default=BASELINE)
    g = ap.add_mutually_exclusive_group()
    g.add_argument('--check', action='store_true')
    g.add_argument('--write-baseline', action='store_true')
    a = ap.parse_args(argv)
    counts = scan(a.root)
    if a.write_baseline:
        write_json(a.baseline, {'literals': list(LITERALS), 'files': len(counts),
                                'total': sum(counts.values()), 'counts': counts})
        print('wrote %s: %d files, %d literals' % (a.baseline, len(counts), sum(counts.values())))
        return 0
    if a.check:
        bad = compare(load_baseline(a.baseline), counts)
        for line in bad:
            print(line)
        return 1 if bad else 0
    print(json.dumps(counts, indent=1, sort_keys=True))
    return 0


if __name__ == '__main__':
    sys.exit(main())
