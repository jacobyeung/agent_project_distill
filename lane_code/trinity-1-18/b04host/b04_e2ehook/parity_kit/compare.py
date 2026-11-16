"""Paired room bootstrap using the existing price_agg script unchanged."""
import argparse
from contextlib import redirect_stdout
import io
from pathlib import Path
import runpy
import sys

from parity_kit.common import LANE, OLD, key, read, rows, tasks, write


def call_texts(result):
    d = result.get('decode', result) or {}
    calls = d.get('calls', [])
    if isinstance(calls, dict):
        calls = calls['records']
    return [c['call'] for c in calls]


def divergence(a, b):
    for i, (left, right) in enumerate(zip(a, b)):
        if left != right:
            return i
    return min(len(a), len(b)) if len(a) != len(b) else None


def agreement(new, old):
    a, b = call_texts(new), call_texts(old)
    first = divergence(a, b)
    return dict(new=a, old=b, identical=a == b, first_divergence_call=first,
                common_prefix_calls=min(len(a), len(b)) if first is None else first,
                first_divergence_character=(divergence(a[first], b[first])
                    if first is not None and first < min(len(a), len(b)) else None))


def compare(new_files, old_file, out, settings=None):
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    old_rows = [r for r in rows(old_file) if r.get('arm', 'unflagged') == 'unflagged']
    old = {r['key']: r for r in old_rows}
    if len(old) != len(old_rows):
        raise ValueError('duplicate baseline keys')
    new = [r for p in new_files for r in rows(p)]
    if len({r['key'] for r in new}) != len(new):
        raise ValueError('duplicate new keys; compare one arm at a time')
    if len({r.get('arm') for r in new}) > 1:
        raise ValueError('mixed arms')
    paired, calls = [], {}
    for r in new:
        b = old[r['key']]
        if (r['room'], r['question_type']) != (b['room'], b['question_type']):
            raise ValueError('paired metadata differs')
        label = 'released_answer' if b['stratum'] == 'primary' else 'answer'
        paired.append(dict(key=r['key'], type=b['question_type'], room=b['room'],
                           old=b['scores'][label], new=r['scores'][label]))
        if b['question_type'].startswith('camera_'):
            calls[r['key']] = agreement(r, b)
    if not paired:
        raise ValueError('no paired rows')
    price = out / 'paired.json'
    write(price, dict(rows=paired))
    argv, output = sys.argv, io.StringIO()
    try:
        sys.argv = [str(LANE / 'tests/price_agg.py'), str(price), 'new']
        with redirect_stdout(output):
            runpy.run_path(str(LANE / 'tests/price_agg.py'), run_name='__main__')
    finally:
        sys.argv = argv
    (out / 'TABLE.txt').write_text(output.getvalue())
    write(out / 'CALL_AGREEMENT.json', dict(items=calls, identical=sum(v['identical'] for v in calls.values()),
                                            total=len(calls)))
    write(out / 'COVERAGE.json', dict(baseline=len(old), paired=len(paired),
                                     missing=sorted(set(old) - {r['key'] for r in new})))
    print(output.getvalue(), end='')
    return read(out / 'paired_new_paired.json')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--new', nargs='+', required=True)
    p.add_argument('--old', default=str(OLD))
    p.add_argument('--out', required=True)
    a = p.parse_args()
    compare(a.new, a.old, a.out)


if __name__ == '__main__':
    main()
