"""NF-A scorer, fixed before any run.

Per type: the score in each order (read 0 = production order, read 1 = reversed), the paired
difference reverse minus production in points with the room bootstrap (10,000 draws, seed 0;
resample rooms, keep every item of a sampled room, ratio of sums, as h1eval.statistics.bootstrap),
and the share of items whose final answer changes.
Item score: 0 for a capped read (finish max_calls), else the reader's output scores.answer
(the scoring that reproduces 171253's registered baselines). Final answer: h1eval.scorers.answer_text.
Rule (ANSWER 1902Z, ORCH RULING 2310Z item 2): a type FAILS the floor if the paired difference's
95% interval lies wholly at or beyond 0.5 points from 0 (lower >= 0.5 or upper <= -0.5), or if
more than 5% of its paired items change their final answer.
"""
import argparse
import json
import math
import re
from collections import defaultdict
from pathlib import Path

import numpy as np

ORDER = ('camera_displacement', 'camera_rotation', 'camera_movement_direction',
         'object_abs_distance', 'room_size_estimation')
DRAWS = 10000
SEED = 0
INFO_SEED = 20261115  # h1eval.statistics.SEED; printed for continuity, not used by the rule
MARGIN = 0.5
SHARE = 0.05


def bootstrap(values, seed=SEED, draws=DRAWS):
    groups = defaultdict(list)
    for room, value in values:
        if value is not None and math.isfinite(float(value)):
            groups[room].append(float(value))
    if not groups:
        return dict(value=None, ci95=None, n=0, rooms=0)
    groups = [groups[k] for k in sorted(groups)]
    sums = np.array([sum(v) for v in groups]); counts = np.array([len(v) for v in groups])
    rng = np.random.default_rng(seed); samples = []
    for start in range(0, draws, 200):
        indices = rng.integers(0, len(groups), size=(min(200, draws - start), len(groups)))
        samples.extend((sums[indices].sum(1) / counts[indices].sum(1)).tolist())
    return dict(value=float(sums.sum() / counts.sum()), ci95=np.quantile(samples, [.025, .975]).tolist(),
                n=int(counts.sum()), rooms=len(groups))


def answer_text(output):
    if output.get('finish') == 'max_calls':
        return ''
    text = output.get('text', ''); m = re.findall(r'<answer>\s*(.*?)\s*</answer>', text, re.S)
    if m:
        return m[-1].strip()
    if '</think>' in text:
        return text.rsplit('</think>', 1)[1].split('<|', 1)[0].strip()
    return text.split('<|', 1)[0].strip()


def item_score(output):
    if output.get('finish') == 'max_calls':
        return 0.0, False
    value = (output.get('scores') or {}).get('answer')
    if value is None:
        return 0.0, True
    return float(value), False


def read_journal(path):
    rows = []
    if not path.exists():
        return rows
    with path.open() as f:
        for line in f:
            if not line.endswith('\n'):
                raise ValueError('incomplete journal tail: %s' % path)
            row = json.loads(line)
            if row.get('complete') is not True:
                raise ValueError('uncommitted record')
            rows.append(row)
    return rows


def load_read(root, read):
    base = Path(root) / 'metadata/reads' / str(read) / 'metadata/journals'
    rows, bound = {}, {}
    for t, kind in enumerate(ORDER):
        d = base / str(t) / '0'
        env = d / 'environment.json'
        if env.exists():
            bound[kind] = json.loads(env.read_text())['binding']['ids']
        journal = read_journal(d / 'items.jsonl')
        for r in journal:
            if r['id'] in rows:
                raise ValueError('duplicate item')
            rows[r['id']] = r
        if journal:
            bound[kind + '#executed'] = [r['id'] for r in journal]
    return rows, bound


def order_checks(items, bound, read):
    want = items['forward_ids'] if read == 0 else items['reverse_ids']
    seq = items['forward_type_sequence'] if read == 0 else items['reverse_type_sequence']
    kind_of = items['_kind']
    checks = {}
    for kind in seq:
        planned = [i for i in want if kind_of[i] == kind]
        ids = bound.get(kind)
        executed = bound.get(kind + '#executed', [])
        checks[kind] = dict(bound_exact=ids == planned,
                            executed_prefix=executed == planned[:len(executed)], executed=len(executed))
    return checks


def score(returned, items_path, out=None):
    items = json.loads(Path(items_path).read_text())
    reads = {i: load_read(returned, i) for i in (0, 1)}
    items['_kind'] = dict(zip(items['forward_ids'], items['forward_types']))
    for i in (0, 1):
        for r in reads[i][0].values():
            if items['_kind'].get(r['id'], r['type']) != r['type']:
                raise ValueError('item type differs')
    chosen = set(items['forward_ids'])
    result = dict(rule=__doc__.split('Rule')[1].strip(), seed=SEED, draws=DRAWS, types={},
                  order={str(i): order_checks(items, reads[i][1], i) for i in (0, 1)})
    for i in (0, 1):
        extra = set(reads[i][0]) - chosen
        if extra:
            raise ValueError('read %d holds items outside the list' % i)
    for kind in items['types']:
        ids = [x for x in items['forward_ids'] if items['_kind'].get(x) == kind]
        planned = items['per_type'][kind]
        f, r = reads[0][0], reads[1][0]
        paired = [x for x in ids if x in f and x in r]
        per = []
        for x in paired:
            sf, uf = item_score(f[x]['output']); sr, ur = item_score(r[x]['output'])
            per.append(dict(id=x, room=f[x]['room_key'], forward=sf, reverse=sr, unscored=uf or ur,
                            changed=answer_text(f[x]['output']) != answer_text(r[x]['output']),
                            finish=[f[x]['output'].get('finish'), r[x]['output'].get('finish')]))
            if f[x]['room_key'] != r[x]['room_key']:
                raise ValueError('paired room differs')
        diff = bootstrap([(p['room'], 100 * (p['reverse'] - p['forward'])) for p in per])
        info = bootstrap([(p['room'], 100 * (p['reverse'] - p['forward'])) for p in per], seed=INFO_SEED)
        changed = sum(p['changed'] for p in per)
        share = changed / len(per) if per else None
        lo, hi = diff['ci95'] if diff['ci95'] else (None, None)
        # ANSWER 1902Z as written (RULING 2310Z item 2): the paired difference itself, |diff| >= 0.5 points; the interval is printed, not used.
        points_fails = diff.get('value') is not None and abs(diff['value']) >= MARGIN
        interval_beyond_margin = lo is not None and (lo >= MARGIN or hi <= -MARGIN)
        share_fails = share is not None and share > SHARE
        result['types'][kind] = dict(
            planned=planned, forward_n=sum(x in f for x in ids), reverse_n=sum(x in r for x in ids),
            paired=len(per), complete=len(per) == planned,
            score_forward=100 * sum(p['forward'] for p in per) / len(per) if per else None,
            score_reverse=100 * sum(p['reverse'] for p in per) / len(per) if per else None,
            difference=diff, difference_info_seed_20261115=info['ci95'],
            changed_answers=changed, changed_share=share,
            score_changed=sum(p['forward'] != p['reverse'] for p in per),
            unscored=sum(p['unscored'] for p in per),
            capped=[sum(p['finish'][0] == 'max_calls' for p in per), sum(p['finish'][1] == 'max_calls' for p in per)],
            points_fails=points_fails, interval_beyond_margin=interval_beyond_margin, share_fails=share_fails,
            floor_fails=bool(points_fails or share_fails) if per else None,
            changed_ids=[p['id'] for p in per if p['changed']])
    if out:
        out = Path(out); out.mkdir(parents=True, exist_ok=True)
        (out / 'SCORES_NFA.json').write_text(json.dumps(result, indent=1, sort_keys=True) + '\n')
        (out / 'SCORES_NFA.md').write_text(report(result))
    return result


def report(result):
    lines = ['# NF-A: one served read in two item orders (reverse minus production, points)', '',
             'Rule: ' + ' '.join(result['rule'].split()), '',
             '| type | paired/planned | production | reverse | diff [95%, seed 0] | answers changed | floor |',
             '|---|---|---|---|---|---|---|']
    for kind, v in result['types'].items():
        d = v['difference']
        ci = '[%+.2f, %+.2f]' % tuple(d['ci95']) if d['ci95'] else 'n/a'
        verdict = 'n/a' if v['floor_fails'] is None else ('FAILS' if v['floor_fails'] else 'holds')
        if not v['complete']:
            verdict += ' (incomplete)'
        lines.append('| %s | %d/%d | %s | %s | %s %s | %d (%s) | %s |' % (
            kind, v['paired'], v['planned'],
            '%.2f' % v['score_forward'] if v['score_forward'] is not None else 'n/a',
            '%.2f' % v['score_reverse'] if v['score_reverse'] is not None else 'n/a',
            '%+.2f' % d['value'] if d['value'] is not None else 'n/a', ci, v['changed_answers'],
            '%.1f%%' % (100 * v['changed_share']) if v['changed_share'] is not None else 'n/a', verdict))
    lines += ['', 'Order checks (bound = worker binding equals the planned order; executed = journal order is its prefix):']
    for read, checks in result['order'].items():
        lines.append('- read %s: %s' % (read, ', '.join('%s bound %s executed %s (%d)' % (
            k, c['bound_exact'], c['executed_prefix'], c['executed']) for k, c in checks.items())))
    return '\n'.join(lines) + '\n'


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--returned', required=True, help='extracted result.tar.gz of the NF-A job')
    p.add_argument('--items', required=True); p.add_argument('--out', required=True)
    a = p.parse_args()
    r = score(a.returned, a.items, a.out)
    print((Path(a.out) / 'SCORES_NFA.md').read_text())
