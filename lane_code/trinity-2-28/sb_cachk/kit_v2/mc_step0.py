"""Dry-run step 0: the carry_precision predicate reproduces the ladder's own merge-eligibility numbers.

For every operand of the 209 captures and each tau, train_pricing.Objects.get(name, 'A0', tau) runs unchanged; the
kit's injection path (mc_ladder.carry_diag, the one mc_price applies to carried tracks) feeds the same seed track and
merged members to get() on a bare Objects and must agree on every object. summarize_train.precision then aggregates
both and must equal out/box_ladder/MERGE_ELIGIBILITY.json (390/538 = 72.49% at tau 0.25), overall and per other-four folds.
Usage: python mc_step0.py [n_captures|all]   (p1cpu interpreter)
"""
import json, sys, time
from concurrent.futures import ProcessPoolExecutor
import mc_common as C
import mc_ladder as L

STATE = {}


def init_worker():
    caps, labels, rowids, tableids, folds, truth, head = L.setup(threads=1)
    STATE.update(caps={c['canonical']: c for c in caps}, rowids=rowids, folds=folds, head=head)


def one(canonical):
    t = L.T()
    c = STATE['caps'][canonical]
    rows = [r for r in c['rows'] if r['id'] in STATE['rowids']]
    names = sorted({n for r in rows for n in r['operands']})
    geo, cache, meta, gt, gt_raw, ref = L.capture_inputs(c)
    objects = t.Objects(c, cache, geo, STATE['head'], gt, ref)
    out = []
    for name in names:
        iid = int(c['gt_name_ids'][name][0])
        for tau in t.M.TAUS:
            _, diag = objects.get(name, 'A0', tau)
            d = objects.data[name]
            mine = (0, 0, None)
            if d['A0'] >= 0:
                merged = next(o for o in d['merges'][tau] if d['A0'] in o['ids'])
                _, inj = L.carry_diag(c, geo, gt, name, d['tracks'][d['A0']].proposals, merged['members'], d['raw'])
                mine = (inj['added'], inj['correct'], inj['seed_majority'])
            ladder = (diag['added'], diag['correct'], diag.get('seed_majority'))
            out.append(dict(name=name, instance=iid, tau=tau, ladder=ladder, kit=mine, equal=tuple(mine) == tuple(ladder)))
        objects.data.pop(name, None); objects.stage.raw.pop(name, None)
    return dict(capture=canonical, room=c['room'], fold=STATE['folds'][c['room']], objects=out, pins=C.all_pins())


def rows_for(results, tau, which):
    """One ladder-format row per object: summarize_train.objects dedups by (capture, instance) as it does for the ladder."""
    S = L.S()
    rows = []
    for r in results:
        for o in r['objects']:
            if o['tau'] != tau:
                continue
            added, correct, _ = o[which]
            rows.append(dict(capture=r['capture'], room=r['room'], fold=r['fold'], diagnostics={o['name']: dict(
                instance=o['instance'], added=added, correct=correct, first_gt=None, gt_longest=None, printed_longest=None)}))
    return rows, S


def main():
    C.scoring_guard(C.OUT/'dry')
    limit = sys.argv[1] if len(sys.argv) > 1 else 'all'
    t0 = time.monotonic()
    init_worker()
    caps = sorted(STATE['caps'])
    if limit.isdigit():
        caps = caps[:int(limit)]
    with ProcessPoolExecutor(8, initializer=init_worker) as pool:
        results = list(pool.map(one, caps))
    for r in results:
        C.PINS.update(r.pop('pins'))
    stored = C.read_json(C.BOX/'out/box_ladder/MERGE_ELIGIBILITY.json')
    table = []
    for row in stored['rows']:
        tau = row['tau']
        entry = dict(tau=tau, stored=row['all_train'])
        for which in ('ladder', 'kit'):
            rows, S = rows_for(results, tau, which)
            entry[which] = S.precision(rows)
            entry[which+'_other_four_folds'] = {str(k): S.precision([x for x in rows if x['fold'] != k]) for k in range(5)}
        entry['reproduced'] = (limit == 'all' and entry['kit'] == row['all_train'] and entry['ladder'] == row['all_train']
                               and entry['kit_other_four_folds'] == row['other_four_folds'])
        table.append(entry)
    objs = [o for r in results for o in r['objects']]
    summary = dict(captures=len(results), object_taus=len(objs), predicate_equal=sum(o['equal'] for o in objs),
                   reproduced=all(e['reproduced'] for e in table),
                   tau_025=next(e['kit'] for e in table if abs(e['tau']-.25) < 1e-9))
    C.code_pins()
    C.write_json(C.OUT/'dry/STEP0_PRECISION.json', dict(
        step='dry-run step 0: carry_precision predicate reproduces MERGE_ELIGIBILITY.json', summary=summary, table=table,
        mismatches=[dict(o, capture=r['capture']) for r in results for o in r['objects'] if not o['equal']][:20],
        seconds=time.monotonic()-t0))
    print(json.dumps(dict(summary=summary, seconds=time.monotonic()-t0)), flush=True)
    C.status(f"Dry-run step 0 (STEP0_PRECISION.json): predicate equal on {summary['predicate_equal']}/{summary['object_taus']} "
             f"object-taus; tau 0.25 {summary['tau_025']['correct']}/{summary['tau_025']['added']}; reproduced={summary['reproduced']}.")


if __name__ == '__main__':
    main()
