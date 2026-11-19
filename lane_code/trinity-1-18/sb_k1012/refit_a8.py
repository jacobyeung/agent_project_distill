"""Refit sb_kbox4's five non-null selector folds without withheld-room objects and reprice A8 where a choice changes
(bash run.sh refit_a8.py). Mirrors train_nonull_v2.main and train_pricing.one's A8 call; writes only to out/."""
import gzip, json, sys, time
from common import B, OUT, PINS, pin, write, rowset, clean

KBOX = B/'sb_kbox4'
sys.path.insert(0, str(KBOX))
import torch  # noqa: E402
import serving_reference as R  # noqa: E402
import math_v2 as M  # noqa: E402
import train_pricing as T  # noqa: E402
from selector_nonull import fit  # noqa: E402


def norm(x):
    return json.loads(json.dumps(clean(x), allow_nan=False))


def groups_and_folds():
    manifest = json.loads(R.read(R.ROOT/'pinned_train.json'))
    rowids = set(R.read(R.ROWSETS/'K1_TRAIN_1037.txt').decode().splitlines())
    caps = [c for c in manifest['captures'] if any(r['id'] in rowids for r in c['rows'])]
    folds = M.folds(c['room'] for c in caps)
    config = json.loads(R.read(R.SEL/'work/run_iso/selector_head.json'))['config']; groups = []
    for c in caps:
        rec = json.loads(gzip.decompress(R.read(R.TABLES/(c['canonical'].replace('/', '__')+'.json.gz'))))
        lab = {(r['name'], r['candidate_id']): r['y'] for r in rec['rows']}
        for name in sorted({i['name'] for i in rec['inputs']}):
            rows = [i for i in rec['inputs'] if i['name'] == name]
            groups.append(dict(object_id=c['canonical']+'::'+name, capture=c['canonical'], name=name, room=c['room'], split='train',
                               x=[i['x'] for i in rows], y=[lab[(name, i['candidate_id'])] for i in rows], candidate_ids=[i['candidate_id'] for i in rows]))
    return caps, folds, config, groups


def oof(groups, folds, config, exclude_rooms):
    choices, records = {}, []
    for fold in range(5):
        t = time.monotonic()
        training = [g for g in groups if folds[g['room']] != fold and g['room'] not in exclude_rooms]
        test = [g for g in groups if folds[g['room']] == fold]
        assert not ({g['room'] for g in training} & {g['room'] for g in test})
        head = fit(training, config)
        with torch.no_grad():
            for g in test:
                k = int(torch.argmax(head(torch.tensor(g['x'], dtype=torch.float64), None, g['name'])))
                choices[g['object_id']] = g['candidate_ids'][k]
        records.append(dict(fold=fold, train_objects=len(training), positive_train_objects=sum(any(g['y']) for g in training),
                            test_objects=len(test), seconds=time.monotonic()-t))
        print(json.dumps(dict(records[-1], excluded_rooms=len(exclude_rooms))), flush=True)
    return choices, records


def a8_rows(c, ctx, choices):
    """train_pricing.one's A8_nonull_best1 call alone, with the supplied OOF choices."""
    labels, rowids, tableids, folds, truth, head = ctx
    rows = [r for r in c['rows'] if r['id'] in rowids]; trows = [r for r in rows if r['id'] in tableids]
    geo, cache, meta, tower, receipt = R.geometry(c); gt, gt_raw = R.gt_arrays(c)
    gt['raster'] = gt_raw.get('inst', gt_raw.get('instances')); gt['valid'] = gt_raw['valid'].astype(bool)
    ref = json.loads(gzip.decompress(R.read(R.TABLES/(c['canonical'].replace('/', '__')+'.json.gz'))))
    names = sorted({n for r in rows for n in r['operands']}); objects = T.Objects(c, cache, geo, head, gt, ref, choices)
    values = {n: objects.get(n, 'A8', None) for n in names}
    return T.evaluate(c, trows, geo, {n: v[0] for n, v in values.items()}, 'A8_nonull_best1', 'best1', labels, folds, truth, gt,
                      {n: v[1] for n, v in values.items()}, meta)


def main():
    torch.set_num_threads(8); start = time.monotonic()
    legality = json.loads(open(OUT/'LEGALITY.json').read()); pin(OUT/'LEGALITY.json')
    withheld_rooms = set(legality['withheld_rooms'])
    caps, folds, config, groups = groups_and_folds()
    saved = json.loads(R.read(R.OUT/'nonull/TRAIN_OOF.json'))
    base_choices, base_records = oof(groups, folds, config, set())
    parity = dict(objects=len(saved['oof_choices']), matched=sum(base_choices.get(k) == v for k, v in saved['oof_choices'].items()),
                  train_objects_match=[r['train_objects'] for r in base_records] == [r['train_objects'] for r in saved['records']])
    parity['passed'] = parity['matched'] == parity['objects'] and set(base_choices) == set(saved['oof_choices']) and parity['train_objects_match']
    assert parity['passed'], parity
    new_choices, new_records = oof(groups, folds, config, withheld_rooms)

    keep = set(rowset('K1_TRAIN_1012.txt'))
    tableids = set(R.read(R.ROWSETS/'K1_TRAIN_TABLES_883.txt').decode().splitlines())
    kept_objects = {c['canonical']+'::'+n for c in caps for r in c['rows'] if r['id'] in keep and r['id'] in tableids for n in r['operands']}
    changed = sorted(k for k in kept_objects if k in saved['oof_choices'] and new_choices.get(k) != saved['oof_choices'][k])
    changed_caps = sorted({k.split('::')[0] for k in changed})
    print(json.dumps(dict(changed_objects=len(changed), changed_captures=len(changed_caps))), flush=True)

    # Reprice: every capture whose A8 choice changed, plus control captures repriced with the saved choices.
    caps_t, labels, rowids, tableids_t, folds_t, truth, head = T.setup()
    ctx = (labels, rowids, tableids_t, folds_t, truth, head); bycap = {c['canonical']: c for c in caps_t}
    published = {}
    for p in sorted((R.OUT/'extras').glob('*.json')):
        for r in json.loads(R.read(p))['items']:
            if r['arm'] == 'A8_nonull_best1':
                published[r['row_id']] = r
    controls = [c for c in sorted(bycap) if c not in changed_caps and any(r['id'] in tableids for r in bycap[c]['rows'])][::20]
    control_rows, repriced = [], []
    for cap in changed_caps+controls:
        rows = a8_rows(bycap[cap], ctx, saved['oof_choices'])
        control_rows += [dict(row_id=r['row_id'], capture=cap, passed=r['prediction'] == published[r['row_id']]['prediction']
                              and norm(r['box']) == published[r['row_id']]['box']) for r in rows]
        if cap in changed_caps:
            repriced += a8_rows(bycap[cap], ctx, new_choices)
        print(json.dumps(dict(capture=cap, rows=len(rows))), flush=True)
    parity['saved_choice_reprice'] = dict(rows=len(control_rows), passed=sum(x['passed'] for x in control_rows),
                                          captures=len(changed_caps)+len(controls), control_captures=len(controls))
    assert all(x['passed'] for x in control_rows), [x for x in control_rows if not x['passed']][:5]
    PINS.update(R.PINS)
    write('A8_REFIT.json', dict(
        rule='sb_kbox4 train_nonull_v2 fit (run_iso config, seed 20261116, registered math_v2 folds over 192 rooms); '
             'objects of the withheld rooms are removed from every fit fold; test objects keep their fold.',
        withheld_rooms=sorted(withheld_rooms), parity=parity, base_records=base_records, refit_records=new_records,
        refit_choices=new_choices, changed_objects_on_1012_table_rows=changed, changed_captures=changed_caps,
        repriced_rows=repriced, seconds=time.monotonic()-start))
    print('done', time.monotonic()-start, flush=True)


if __name__ == '__main__':
    main()
