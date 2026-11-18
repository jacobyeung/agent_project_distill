"""Summarize complete r6 reads and paired differences against step 544."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'kit/reader'))
from r6 import CONSTANTS, COUNTS, check_capture
from room_bootstrap import paired

SEED = 20261118
DRAWS = 10000


def load_read(root):
    root = Path(root)
    registration = json.loads((ROOT/'kit/launcher/R6.json').read_text())
    check_capture(registration)
    if (root/'PARTIAL.json').exists() or json.loads((root/'SUMMARY.json').read_text()).get('complete') is not True:
        raise ValueError('Require a complete read; partial scores are not final')
    spec = json.loads((root/'SPEC.json').read_text())
    binding = spec['export_binding']
    identity = (binding['run'], spec['step'], binding['generation'])
    if spec['families'] != ['r6'] or identity not in (
            ('469ddece',544,'mstop'), ('673bc60f',200,'m200')):
        raise ValueError('Unregistered read identity')
    pin = hashlib.sha256(json.dumps(registration, sort_keys=True).encode()).hexdigest()
    if spec.get('r6_sha256') != pin or binding['step'] != spec['step']:
        raise ValueError('Read registration differs')
    path = root/'r6/ITEMS.jsonl'; raw = path.read_bytes()
    rows = [json.loads(line) for line in raw.splitlines()]
    item_raw = (ROOT/'assets'/registration['item_name']).read_bytes()
    if hashlib.sha256(item_raw).hexdigest() != registration['files'][registration['item_name']]['sha256']:
        raise ValueError('Local item asset pin differs')
    tasks = [json.loads(line) for line in item_raw.splitlines()]
    mapping = json.loads((ROOT/'evidence/R6_ID_MAP.json').read_text())
    expected = {mapping[t['id']]['id']:(t,mapping[t['id']]) for t in tasks}
    normalized = {}
    for row in rows:
        ident = mapping[row['id']]['id'] if row['id'] in mapping else row['id']
        if ident in normalized or ident not in expected:
            raise ValueError('Duplicate or unexpected item')
        task, source = expected[ident]
        if (row.get('family') != 'r6' or row.get('task_type') != task['question_type']
                or row.get('room') not in (task['room'],source['room'])
                or row.get('gold_letter') != task['answer'] or row.get('budget') != 2048
                or row.get('step') != spec['step'] or row.get('scoring_basis') != 'answer'
                or type(row.get('score')) not in (int,float) or row['score'] not in (0,1)
                or type(row.get('template_capture')) is not bool
                or row.get('predicted_letter') not in [None,*list('ABCD'[:len(task['options'])])]
                or 'predicted_letter' not in row
                or row['score'] == 1 and row['predicted_letter'] != row['gold_letter']):
            raise ValueError('Item metadata or score differs: '+ident)
        # Decoding changes only identity representation. Clusters use the room
        # field supplied by the item; no filename or question text inference.
        normalized[ident] = dict(row, id=ident, room=source['room'])
    if set(normalized) != set(expected) or Counter(r['task_type'] for r in rows) != COUNTS:
        raise ValueError('Require all 900 items, with 150 in each type')
    return dict(identity=identity, path=str(path), items_sha256=hashlib.sha256(raw).hexdigest(),
                rows=normalized)


def level(rows, baseline=None):
    values = list(rows)
    n = len(values)
    result = dict(n=n, rooms=len({r['room'] for r in values}),
                  accuracy_pct=100*sum(r['score'] for r in values)/n,
                  template_capture_n=sum(r['template_capture'] for r in values),
                  template_capture_pct=100*sum(r['template_capture'] for r in values)/n)
    if baseline is not None:result['constant_baseline_pct'] = baseline
    return result


def compare(current, base):
    def projected(rows):
        return [dict(key=r['id'], room=r['room'], stratum='r6', question_type=r['task_type'],
                     scores={'answer':r['score']}) for r in sorted(rows, key=lambda r:r['id'])]
    result = paired(projected(current), projected(base), 'answer', replicates=DRAWS, seed=SEED)
    result['wholly_below_zero'] = result['ci95_pp'][1] < 0
    return result


def summarize(read, base=None):
    current = load_read(read)
    rows = list(current['rows'].values())
    report = dict(read=current['path'], items_sha256=current['items_sha256'], identity=current['identity'],
        per_type={t:level([r for r in rows if r['task_type']==t], baseline) for t,baseline in CONSTANTS.items()},
        pooled=level(rows), capture_sha256=json.loads((ROOT/'kit/launcher/R6.json').read_text())['capture_sha256'])
    if base is not None:
        previous = load_read(base)
        if current['identity'] != ('673bc60f',200,'m200') or previous['identity'] != ('469ddece',544,'mstop'):
            raise ValueError('Pair requires run 673bc60f m200 minus run 469ddece mstop/544')
        if set(current['rows']) != set(previous['rows']):raise ValueError('Paired item sets differ')
        base_rows = list(previous['rows'].values())
        report['base'] = dict(read=previous['path'], items_sha256=previous['items_sha256'], identity=previous['identity'])
        for task, entry in report['per_type'].items():
            entry['paired'] = compare([r for r in rows if r['task_type']==task],
                                      [r for r in base_rows if r['task_type']==task])
        report['pooled']['paired'] = compare(rows,base_rows)
        harmed = [t for t,v in report['per_type'].items() if v['paired']['wholly_below_zero']]
        rises = report['pooled']['paired']['delta_pp'] > 0
        report['gate'] = dict(pooled_accuracy_rises=rises, types_wholly_below_zero=harmed,
                              passed=rises and not harmed)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--read', required=True)
    parser.add_argument('--base')
    parser.add_argument('--json', action='store_true', help='Print the same results as JSON')
    args = parser.parse_args()
    try:
        result = summarize(args.read,args.base)
    except (ValueError, KeyError, OSError) as error:
        parser.error(str(error))
    if args.json:
        print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False)); return
    print('r6/ITEMS.jsonl SHA256:',result['items_sha256'])
    if 'base' in result:print('Base r6/ITEMS.jsonl SHA256:',result['base']['items_sha256'])
    print('Type\tn\tAccuracy %\tConstant %\tCapture %' + ('\tDelta pp [room-bootstrap 95% CI]' if args.base else ''))
    for name, entry in [*result['per_type'].items(), ('pooled',result['pooled'])]:
        constant = f"{entry['constant_baseline_pct']:.1f}" if 'constant_baseline_pct' in entry else '—'
        line = f"{name}\t{entry['n']}\t{entry['accuracy_pct']:.3f}\t{constant}\t{entry['template_capture_pct']:.3f}"
        if 'paired' in entry:
            p = entry['paired']; lo, hi = p['ci95_pp']
            line += f"\t{p['delta_pp']:+.3f} [{lo:+.3f}, {hi:+.3f}]"
            if p['wholly_below_zero']:line += ' BELOW ZERO'
        print(line)
    if 'gate' in result:
        print(f'Room bootstrap: {DRAWS:,} draws; seed {SEED}; paired item-weighted differences.')
        print('Gate:', 'PASS' if result['gate']['passed'] else 'FAIL',
              '(pooled accuracy must rise; no type interval wholly below zero)')


if __name__ == '__main__':
    main()
