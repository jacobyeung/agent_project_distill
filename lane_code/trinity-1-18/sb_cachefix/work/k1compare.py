"""Compare the four k1diag variants; check today's A0 against sb_kbox4's published A0 rows.

Writes work/K1DIAG.json; exits 1 if a parity gate fails.
"""
import collections, json, sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PER_ITEM = Path('/scratch/jjyeung/orch_n30/sb_kbox4/out/box_ladder/PER_ITEM.jsonl')
VARIANTS = ('today', 'fixed', 'alias_today', 'alias_fixed')


def mra(pred, gt):
    if pred is None:
        return 0.
    return float(np.mean([abs(pred-gt)/abs(gt) < 1-t for t in np.arange(.5, .96, .05)]))


def load(variant):
    caps = [json.loads(p.read_text()) for p in sorted((HERE/'k1diag'/variant).glob('*.json'))]
    rows = {r['row_id']: r for c in caps for r in c['rows']}
    names = {(c['capture'], n): v for c in caps for n, v in c['names'].items()}
    return caps, rows, names


def contrast(left, right):
    """summarize_train.contrast: paired MRA difference, 10,000 physical-room draws, seed 20261119."""
    ids = sorted(left)
    assert set(ids) == set(right)
    rooms = sorted({left[i]['room'] for i in ids})
    idx = {r: k for k, r in enumerate(rooms)}
    delta = np.array([mra(left[i]['prediction'], left[i]['label'])-mra(right[i]['prediction'], right[i]['label']) for i in ids])
    clusters = [idx[left[i]['room']] for i in ids]
    sums = np.bincount(clusters, weights=delta, minlength=len(rooms))
    counts = np.bincount(clusters, minlength=len(rooms))
    draws = np.random.default_rng(20261119).integers(0, len(rooms), (10000, len(rooms)))
    boot = sums[draws].sum(1)/counts[draws].sum(1)
    mean = lambda rows: 100*float(np.mean([mra(rows[i]['prediction'], rows[i]['label']) for i in ids]))
    return dict(rows=len(ids), rooms=len(rooms), left_mra=mean(left), right_mra=mean(right),
                estimate=float(100*delta.mean()), ci95=(100*np.percentile(boot, [2.5, 97.5])).tolist(),
                draws=10000, seed=20261119)


def changes(a, b, an, bn):
    rows = collections.Counter()
    for i in a:
        rows['prediction'] += a[i]['prediction'] != b[i]['prediction']
        rows['box'] += a[i]['box'] != b[i]['box']
        rows['refusal'] += a[i]['refusal_code'] != b[i]['refusal_code']
        rows['member_frames'] += a[i]['member_frames'] != b[i]['member_frames']
        rows['any'] += any(a[i][k] != b[i][k] for k in ('prediction', 'box', 'refusal_code', 'member_frames'))
    names = collections.Counter()
    for k in an:
        names['selected'] += an[k]['selected'] != bn[k]['selected']
        names['accepted'] += an[k]['accepted'] != bn[k]['accepted']
        names['x'] += an[k]['x_sha256'] != bn[k]['x_sha256']
        names['proposals'] += an[k]['proposals_sha256'] != bn[k]['proposals_sha256']
    return dict(rows=len(a), names=len(an), row_changes=dict(rows), name_changes=dict(names))


def main():
    data = {v: load(v) for v in VARIANTS}
    published = {}
    for line in PER_ITEM.read_text().splitlines():
        r = json.loads(line)
        if r['arm'] == 'A0_deployed':
            published[r['row_id']] = r
    today = data['today'][1]
    parity = dict(rows=len(published), matched=sum(
        i in today and all(today[i][k] == published[i][k] for k in ('prediction', 'refusal_code', 'box', 'member_frames', 'label'))
        for i in published))
    out = dict(
        captures={v: len(d[0]) for v, d in data.items()},
        module_sha256={v: sorted({json.dumps(c['module_sha256'], sort_keys=True) for c in d[0]}) for v, d in data.items()},
        a0_parity_vs_sb_kbox4=parity,
        mixed_frames_entering_stage1={v: sum(c['mixed_frames'] for c in d[0]) for v, d in data.items()},
        presence_outside_lift_range={v: sum(n['presence_outside_lift_range'] for n in d[2].values()) for v, d in data.items()},
        candidates={v: sum(n['candidates'] for n in d[2].values()) for v, d in data.items()},
        fixed_vs_today=dict(changes(data['fixed'][1], today, data['fixed'][2], data['today'][2]),
                            contrast=contrast(data['fixed'][1], today)),
        alias_fixed_vs_alias_today=dict(changes(data['alias_fixed'][1], data['alias_today'][1], data['alias_fixed'][2], data['alias_today'][2]),
                                        contrast=contrast(data['alias_fixed'][1], data['alias_today'][1])),
        alias_today_vs_today=dict(contrast=contrast(data['alias_today'][1], today)),
        alias_fixed_vs_today=dict(contrast=contrast(data['alias_fixed'][1], today)))
    gates = dict(parity=parity['matched'] == parity['rows'] == 1037,
                 identical=out['fixed_vs_today']['row_changes'].get('any', 0) == 0 and not any(out['fixed_vs_today']['name_changes'].values()),
                 single_presence=out['mixed_frames_entering_stage1']['fixed'] == 0)
    out['gates'] = dict(gates, passed=all(gates.values()))
    (HERE/'K1DIAG.json').write_text(json.dumps(out, indent=1)+'\n')
    print(json.dumps(out, indent=1))
    sys.exit(0 if out['gates']['passed'] else 1)


if __name__ == '__main__':
    main()
