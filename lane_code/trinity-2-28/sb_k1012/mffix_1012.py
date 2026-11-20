"""Mask failure attribution (sb_mffix) first table on the 1,012 rows outside the withheld rooms (bash run.sh mffix_1012.py).
Uses the kit's priced counterfactual rows, its record classes and its paired_bootstrap (summarize_train.contrast)."""
import json, sys
from common import B, OUT, PINS, pin, sha, write, rowset

KIT = B/'sb_mffix/kit'
sys.path.insert(0, str(KIT))
import analyze as A  # noqa: E402


def attribution(cf, base, gt, ids):
    """analyze.price's ATTRIBUTION block on the rows in ids."""
    pick = lambda rows: [r for r in rows if r['row_id'] in ids]
    base, gt = pick(base), pick(gt)
    out = dict(baseline=100*float(A.np.mean([A.T.M.mra(r['prediction'], r['label']) for r in base])),
               raster=100*float(A.np.mean([A.T.M.mra(r['prediction'], r['label']) for r in gt])), gap=A.paired_bootstrap(gt, base), thresholds={})
    for t in A.THRESH:
        out['thresholds'][str(t)] = {}
        for mode in ['independent', 'cumulative']:
            out['thresholds'][str(t)][mode] = {}; prev = base
            for kind in A.KINDS:
                rows = pick(cf[f'{t}/{mode}/{kind}']); assert len(rows) == len(ids)
                b = A.paired_bootstrap(rows, base)
                b.update(refusals=sum(r['prediction'] is None for r in rows), mra=out['baseline']+b['estimate'], gap_fraction=b['estimate']/out['gap']['estimate'])
                if mode == 'cumulative':
                    b['increment'] = A.paired_bootstrap(rows, prev)
                out['thresholds'][str(t)][mode][kind] = b; prev = rows
    return out


def counts(records, ids):
    s = A.stats([r for r in records if r['row'] in ids])
    return dict(visible_valid=s['visible_valid'], failure=s['failure'], all_frame_failure=s['all_frame_failure'])


def main():
    out = KIT/'out'
    for f in ['COUNTERFACTUAL_ROWS.json', 'ATTRIBUTION.json', 'MASKFAIL.json']:
        assert sha(out/f) == sha(B/'sb_mffix/out'/f), f
    cfj = json.loads(A.T.read(out/'COUNTERFACTUAL_ROWS.json')); kit_attr = json.loads(A.T.read(out/'ATTRIBUTION.json'))
    records = json.loads(A.T.read(out/'MASKFAIL.json'))['records']; splits = json.loads(A.T.read(out/'SPLITS.json'))
    cf = {}
    for r in cfj['rows']:
        cf.setdefault(r['arm'], []).append(r)
    ids_full = set(A.T.read(A.IDS).decode().splitlines()); ids = set(rowset('K1_TRAIN_1012.txt'))
    endpoints = {}
    with open(A.BOX/'out/box_ladder/PER_ITEM.jsonl') as f:
        for line in f:
            r = json.loads(line)
            if r['arm'] in ('A0_deployed', 'A2_gt_masks') and r['row_id'] in ids_full and 'chosen_arm' not in r:
                endpoints.setdefault(r['arm'], []).append(r)
    pin(A.BOX/'out/box_ladder/PER_ITEM.jsonl')
    base = sorted(endpoints['A0_deployed'], key=lambda r: r['row_id']); gt = sorted(endpoints['A2_gt_masks'], key=lambda r: r['row_id'])
    assert len(base) == len(gt) == 1037

    full = attribution(cf, base, gt, ids_full)
    strip = lambda x: json.loads(json.dumps(A.T.clean(x)))
    parity = dict(gap=strip(full['gap']) == kit_attr['gap'], thresholds=strip(full['thresholds']) == kit_attr['thresholds'],
                  counts=counts(records, ids_full)['failure'] == splits['overall']['failure'])
    assert all(parity.values()), parity
    sub = attribution(cf, base, gt, ids)
    c_full, c_sub = counts(records, ids_full), counts(records, ids)
    table = []
    for k in A.KINDS:
        i0, i1 = full['thresholds']['0.5']['independent'][k], sub['thresholds']['0.5']['independent'][k]
        u0, u1 = full['thresholds']['0.5']['cumulative'][k], sub['thresholds']['0.5']['cumulative'][k]
        table.append(dict(kind=k, frames_1037=c_full['failure']['0.5'].get(k, 0), frames_1012=c_sub['failure']['0.5'].get(k, 0),
                          share_1012=100*c_sub['failure']['0.5'].get(k, 0)/c_sub['visible_valid'],
                          independent_1037=dict(estimate=i0['estimate'], ci95=i0['ci95'], refusals=i0['refusals']),
                          independent_1012=dict(estimate=i1['estimate'], ci95=i1['ci95'], refusals=i1['refusals']),
                          ordered_increment_1012=dict(estimate=u1['increment']['estimate'], gap_share=u1['increment']['estimate']/sub['gap']['estimate']),
                          cumulative_1012=dict(estimate=u1['estimate'], ci95=u1['ci95']),
                          ci_excludes_zero_1037=i0['ci95'][0] > 0 or i0['ci95'][1] < 0, ci_excludes_zero_1012=i1['ci95'][0] > 0 or i1['ci95'][1] < 0,
                          rank_1037=None, rank_1012=None))
    for key in ('1037', '1012'):
        order = sorted(table, key=lambda x: -x[f'independent_{key}']['estimate'])
        for n, x in enumerate(order, 1):
            x[f'rank_{key}'] = n
    PINS.update(A.T.PINS)
    write('MFFIX_1012.json', dict(
        scope='sb_mffix first table (IoU 0.5) on K1_TRAIN_1012: the kit\'s 48 priced counterfactual arms restricted to the 1,012 rows, '
              'paired against A0 with its paired_bootstrap (10,000 room draws, seed 20261119); counts are visible valid operand-frames.',
        parity_1037=parity, gap=dict(v1037=dict(estimate=full['gap']['estimate'], ci95=full['gap']['ci95'], a0=full['baseline'], a2=full['raster']),
                                     v1012=dict(estimate=sub['gap']['estimate'], ci95=sub['gap']['ci95'], a0=sub['baseline'], a2=sub['raster'], rooms=sub['gap']['rooms'])),
        visible_frames=dict(v1037=c_full['visible_valid'], v1012=c_sub['visible_valid']), first_table=table,
        attribution_1012=sub))
    for x in table:
        print(x['kind'], x['frames_1037'], x['frames_1012'], round(x['independent_1037']['estimate'], 4), round(x['independent_1012']['estimate'], 4),
              [round(v, 4) for v in x['independent_1012']['ci95']], x['ci_excludes_zero_1037'], x['ci_excludes_zero_1012'])
    print('gap', full['gap']['estimate'], sub['gap']['estimate'], sub['gap']['ci95'])


if __name__ == '__main__':
    main()
