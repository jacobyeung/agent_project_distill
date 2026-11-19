"""Independent reviewer rerun of sb_maskfail endpoints, per-frame kinds and selected attribution arms.
Uses sb_kbox4's unchanged geometry, Objects (A0), lifted (A2) and session_distance pricing; the
classification and frame-replacement code here is written from RULES.md, not copied from the kit."""
import gzip, json, pickle, sys, time
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
BOX = Path('/scratch/jjyeung/orch_n30/sb_kbox4')
sys.path.insert(0, str(BOX))
import train_pricing as T
T.torch.set_num_threads(8)
OUT = HERE / 'tmp/rr'; OUT.mkdir(parents=True, exist_ok=True)
IDS = Path('/scratch/jjyeung/n30_mirror/sb_headacc2/K1_ROWSETS/K1_TRAIN_1037.txt')
LAB = Path('/scratch/jjyeung/n30_mirror/gt_audit/gt_audit/work/k1audit/K1_LABELS_CORRECTED.jsonl')
THRESH = (.3, .5, .7)
ORDER = ['no_proposal', 'omitted_selection', 'wrong_instance', 'wrong_class', 'partial_mask',
         'merged_instances', 'other_mask_error', 'correct']
ARMS = {'ind/no_proposal': {'no_proposal'}, 'ind/omitted_selection': {'omitted_selection'},
        'ind/wrong_class': {'wrong_class'}, 'cum/omitted_selection': set(ORDER[:2]),
        'cum/wrong_class': set(ORDER[:4]), 'cum/other_mask_error': set(ORDER[:7]), 'cum/correct': set(ORDER)}


def kind(rec, t):
    """RULES.md, rules 1-8 in order, plus absent_both / MISSING."""
    if not rec['valid']:
        return 'MISSING'
    vis, area = rec['visible'], rec['served_area']
    if not vis and area == 0:
        return 'absent_both'
    if vis and rec['iou'] >= t:
        return 'correct'
    if vis and not rec['pool_touches']:
        return 'no_proposal'
    if vis and area == 0:
        return 'omitted_selection'
    if rec['n_merged'] >= 2:
        return 'merged_instances'
    if rec['dom_id'] is not None and rec['dom_id'] != rec['instance'] and rec['dom_frac'] >= .5:
        return 'wrong_instance' if rec['dom_label'] == rec['label'] else 'wrong_class'
    if vis and rec['precision'] >= .8:
        return 'partial_mask'
    return 'other_mask_error'


def overlay(name, base, gt, frames):
    """Per-frame replacement: frames in `frames` take the GT-raster lift, all others keep A0."""
    obj = dict(name=name, seen=False, frames=[], visible=[], areas={}, points={}, boxes={})
    for f in range(1, 33):
        src = gt if f in frames else base
        if f in src['visible']:
            obj['visible'].append(f); obj['areas'][str(f)] = src['areas'][str(f)]
        if f in src['frames']:
            obj['frames'].append(f); obj['points'][str(f)] = src['points'][str(f)]
    if obj['frames']:
        obj['seen'] = True
        obj['best'] = min(obj['frames'], key=lambda f: (-obj['areas'][str(f)], f))
    return obj


def price(row, geo, objs):
    try:
        pred, refusal, _, _ = T.pricing.session_distance(row, geo, objs, T.G, 'best1')
    except (ValueError, KeyError, IndexError) as exc:
        pred, refusal = None, type(exc).__name__
    return pred, refusal


def capture(c, ids, labels, head):
    stub = c['canonical'].replace('/', '__')
    dest = OUT / (stub + '.pkl')
    if dest.exists():
        return
    t0 = time.monotonic()
    rows = [r for r in c['rows'] if r['id'] in ids]
    geo, cache, meta, tower, receipt = T.R.geometry(c)
    gt, rawgt = T.R.gt_arrays(c)
    raster = rawgt.get('inst', rawgt.get('instances')); valid = rawgt['valid'].astype(bool)
    gt['raster'] = raster; gt['valid'] = valid
    inst = gt['instances']
    labmap = {int(i): str(n) for i, n in zip(rawgt['ids'], rawgt['labels'])}
    ref = json.loads(gzip.decompress(T.read(T.R.TABLES / (stub + '.json.gz'))))
    objects = T.Objects(c, cache, geo, head, gt, ref)
    names = sorted({n for r in rows for n in r['operands']})
    base, gtobj, recs = {}, {}, []
    for n in names:
        iid = int(c['gt_name_ids'][n][0])
        a0, _ = objects.get(n, 'A0')
        base[n] = a0
        gtobj[n] = T.lifted(n, (raster == iid) & valid[:, None, None], geo)
        d = objects.data[n]; choice = d['A0']
        sel = {}
        if choice >= 0:
            for p in d['tracks'][choice].proposals:
                assert p.frame not in sel
                sel[p.frame] = p.index
        intrack = {(p.frame, p.index) for t in d['tracks'] for p in t.proposals}
        for f in range(1, 33):
            target = inst[f - 1] == iid
            tarea = int(target.sum())
            m = d['raw'][f - 1][sel[f]]['mask'][::2, ::2] if f in sel else np.zeros_like(target)
            area = int(m.sum()); inter = int(np.count_nonzero(m & target)); union = area + tarea - inter
            pool = []
            for k, p in enumerate(d['raw'][f - 1]):
                pm = p['mask'][::2, ::2]; pi = int(np.count_nonzero(pm & target)); pu = int(pm.sum()) + tarea - pi
                pool.append((pi / pu if pu else 0., pi, float(p['score']), (f, k) in intrack, k == sel.get(f)))
            ids_, cnt = np.unique(inst[f - 1][m], return_counts=True)
            ann = [(int(k), int(v)) for k, v in zip(ids_, cnt) if int(k) in labmap]
            dom = max(ann, key=lambda x: (x[1], -x[0])) if ann else (None, 0)
            merged = [k for k, v in ann if area and v / area >= .1 and v / int(np.count_nonzero(inst[f - 1] == k)) >= .1]
            best = max(pool, default=(0., 0, 0., False, False))
            rec = dict(capture=c['canonical'], object=n, instance=iid, frame=f, label=labmap.get(iid),
                       valid=bool(valid[f - 1]), visible=tarea > 0, served_area=area,
                       iou=(inter / union) if union else None, precision=inter / area if area else 0.,
                       pool_touches=any(x[1] > 0 for x in pool), n_merged=len(merged),
                       dom_id=dom[0], dom_label=labmap.get(dom[0]), dom_frac=dom[1] / area if area else 0.,
                       share_native=float(np.mean(raster[f - 1] == iid)),
                       pool_best_iou=best[0], pool_best_score=best[2], pool_best_intrack=best[3],
                       pool_correct={str(t): dict(any=any(x[0] >= t for x in pool),
                                                  liftable=any(x[0] >= t and x[2] >= .3 for x in pool),
                                                  in_track=any(x[0] >= t and x[3] for x in pool)) for t in THRESH})
            rec['kinds'] = {str(t): kind(rec, t) for t in THRESH}
            recs.append(rec)
        objects.data.pop(n); objects.stage.raw.pop(n)
    prices = {}
    kinds = {(r['object'], r['frame']): r['kinds']['0.5'] for r in recs}
    arms = {'A0': base, 'A2': gtobj}
    for arm, active in ARMS.items():
        arms[arm] = {n: overlay(n, base[n], gtobj[n], {f for f in range(1, 33) if kinds[(n, f)] in active}) for n in names}
    for arm, objs in arms.items():
        for row in rows:
            pred, refusal = price(row, geo, objs)
            prices[(arm, row['id'])] = dict(arm=arm, row_id=row['id'], room=c['room'], capture=c['canonical'],
                                            prediction=pred, refusal=refusal, label=labels[row['id']])
    with dest.open('wb') as f:
        pickle.dump(dict(records=recs, prices=prices, rows=[r['id'] for r in rows]), f, protocol=5)
    print(json.dumps(dict(capture=c['canonical'], names=len(names), rows=len(rows), s=round(time.monotonic() - t0, 1))), flush=True)


def main():
    ids = set(T.read(IDS).decode().split()); assert len(ids) == 1037
    labels = {}
    for line in T.read(LAB).decode().splitlines():
        r = json.loads(line)
        if r['id'] in ids:
            assert r['split'] == 'train'; labels[r['id']] = r['corrected']
    assert set(labels) == ids
    pin = json.loads(T.read(BOX / 'pinned_train.json'))
    caps = [c for c in pin['captures'] if any(r['id'] in ids for r in c['rows'])]
    assert len(caps) == 209 and all(c['k1_split'] == 'train' for c in caps)
    headpath = T.R.SEL / 'work/run_iso'
    head, _ = T.R.load_head(headpath)
    lo, hi = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (0, len(caps))
    for c in sorted(caps, key=lambda c: c['canonical'])[lo:hi]:
        T.PINS.clear()
        capture(c, ids, labels, head)


if __name__ == '__main__':
    main()
