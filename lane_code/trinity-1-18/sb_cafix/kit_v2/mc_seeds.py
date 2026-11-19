"""Seed sets, one 480 x 640 mask per (capture, operand name) on one anchor.

S_A0  : the deployed track's served mask on its largest frame (Objects.load: A0, tracks, raw); refused operands have none.
S_GT  : the raster instance at its largest visible anchor (ceiling only, never a served arm).
S_PHR : S_A0 when each operand is called with the policy of the fold that held its room out (PHRASE_FOLDS.json, through
        the phrase kit's own pool and ArmObjects, mc_phrase); a pair (w1, w2) takes w2's call only when w1's object is not
        seen (refused or unseen). A raw-name call, first or second, is the A0 call and restores the S_A0 seed.
        NOT_YET while PHRASE_FOLDS.json does not exist; SEEDS.json records the fold file's path and sha256.
Dry-run item 1 is computed here: the rebuilt A0 served masks must equal sb_maskfail's records on every anchor and the
published A0 frames, and the seed must be the served mask on A0's best frame.
Usage: python mc_seeds.py [n_captures|all|canonical,...] [--phr-parity]   (p1cpu interpreter)
"""
import json, sys, time
from concurrent.futures import ProcessPoolExecutor
import numpy as np
import mc_common as C
import mc_ladder as L
import mc_phrase as PH

STATE = {}


def init_worker():
    caps, labels, rowids, tableids, folds, truth, head = L.setup(threads=1)
    STATE.update(caps={c['canonical']: c for c in caps}, rowids=rowids, head=head, folds=folds)


def a0_seed(objects, name, iid, gt):
    """The A0 track's seed for one call (S_A0 on the base pool, S_PHR on the phrase pool) plus its served masks."""
    d = objects.load(name)
    obj, _ = objects.get(name, 'A0')
    choice = d['A0']
    served = np.zeros((32,)+C.CANVAS, bool)
    index = [None]*32
    if choice >= 0:
        for p in d['tracks'][choice].proposals:
            served[p.frame-1] = d['raw'][p.frame-1][p.index]['mask']
            index[p.frame-1] = int(p.index)
    if choice < 0:
        return dict(status='REFUSED'), served, index, obj
    if not obj['seen']:
        return dict(status='UNSEEN'), served, index, obj
    best = obj['best']
    seed = served[best-1]
    target = gt['instances'][best-1] == iid
    value = C.iou(seed[::2, ::2], target)
    return dict(status='OK', slot=best, area=float(seed.mean()), iou=value, on_target=bool(value is not None and value >= .5),
                candidate_id=d['accepted'][choice]['candidate_id']), served, index, obj


def gt_seed(gt_raw, iid):
    from scipy import ndimage
    raster = gt_raw.get('inst', gt_raw.get('instances'))
    valid = gt_raw['valid'].astype(bool)
    share = [float(np.mean(raster[f] == iid)) if valid[f] else 0. for f in range(32)]
    if max(share) <= 0:
        return dict(status='NOT_VISIBLE'), None
    best = max(range(32), key=lambda f: (share[f], -f))
    native = raster[best] == iid
    seed = ndimage.zoom(native, (C.CANVAS[0]/native.shape[0], C.CANVAS[1]/native.shape[1]), order=0, prefilter=False)
    return dict(status='OK', slot=best+1, area=float(seed.mean()), raster_share=share[best], iou=1.0, on_target=True), seed


def phr_choice(policy, name, a0, a0_mask, call):
    """S_PHR of one operand: the policy's calls in order, each later call only while the object is not seen.
    A raw-name call is A0's own call, so it yields the S_A0 record and mask; call(phrase) -> (record, mask or None)
    runs any other phrase."""
    p, pmask = None, None
    for i, phrase in enumerate(policy):
        if i and p['status'] == 'OK':
            break
        p, pmask = (dict(a0), a0_mask) if phrase == name else call(phrase)
        p = dict(p, call=phrase, calls=i+1)
    return p, pmask


def check_one(name, served, index, obj, seed_rec, mf, pub_frames, gt_instances, iid):
    """Dry-run item 1 for one operand: rebuilt served masks against sb_maskfail and the published A0 frames."""
    frames_ok = list(obj['frames']) == list(pub_frames)
    per = []
    for f in range(32):
        m = served[f][::2, ::2]
        r = mf.get(f+1)
        target = gt_instances[f] == iid
        area = int(m.sum())
        value = C.iou(m, target) if r is None or r['valid'] else None
        per.append(r is not None and r['served_area'] == area and r['selected_proposal_index'] == index[f]
                   and ((r['iou'] is None and value is None) or (r['iou'] is not None and value is not None and abs(r['iou']-value) < 1e-12)))
    seed_ok = True
    if seed_rec['status'] == 'OK':
        areas = {f: float(served[f-1][::2, ::2].mean()) for f in obj['frames']}
        seed_ok = seed_rec['slot'] == min(obj['frames'], key=lambda f: (-areas[f], f))
    return dict(frames_equal_published=frames_ok, anchors_equal_maskfail=int(sum(per)), anchors=32, seed_is_best=seed_ok,
                passed=frames_ok and all(per) and seed_ok)


def one(canonical, published_frames, maskfail, table_status, table, parity):
    t = L.T()
    started = time.monotonic()
    c = STATE['caps'][canonical]
    rows = [r for r in c['rows'] if r['id'] in STATE['rowids']]
    names = sorted({n for r in rows for n in r['operands']})
    geo, cache, meta, gt, gt_raw, ref = L.capture_inputs(c)
    objects = t.Objects(c, cache, geo, STATE['head'], gt, ref)
    mf = {}
    for r in maskfail:
        mf.setdefault(r['object'], {})[r['frame']] = r
    out, masks = [], {}

    def phrase_seed(name, iid, phrase):
        objs, call = PH.arm_objects(c, geo, STATE['head'], gt, cache, name, phrase)
        try:
            p, pserved, _, _ = a0_seed(objs, call, iid, gt)
        finally:
            objs.unbind(call)
        return dict(p, call=call), pserved

    fold = STATE['folds'][c['room']]
    policies = table.get(fold, {}) if table is not None else {}
    for k, name in enumerate(names):
        iid = int(c['gt_name_ids'][name][0])
        rec = dict(k=k, name=name, instance=iid)
        a0, served, index, obj = a0_seed(objects, name, iid, gt)
        rec['S_A0'] = a0
        if a0['status'] == 'OK':
            masks[f'S_A0_{k}'] = served[a0['slot']-1]
        rec['check1'] = check_one(name, served, index, obj, a0, mf.get(name, {}), published_frames[name], gt['instances'], iid)
        g, gseed = gt_seed(gt_raw, iid)
        rec['S_GT'] = g
        if gseed is not None:
            masks[f'S_GT_{k}'] = gseed
        if parity:
            p, pserved = phrase_seed(name, iid, name)
            p = {kk: v for kk, v in p.items() if kk != 'call'}
            rec['phr_parity'] = p == a0 and (p['status'] != 'OK' or np.array_equal(pserved[p['slot']-1], served[a0['slot']-1]))
        if table is None:
            rec['S_PHR'] = dict(status=table_status)
        else:
            def call(phrase):
                p, pserved = phrase_seed(name, iid, phrase)
                return p, (pserved[p['slot']-1] if p['status'] == 'OK' else None)
            policy = tuple(policies.get(name, (name,)))
            p, pmask = phr_choice(policy, name, a0, masks.get(f'S_A0_{k}'), call)
            p['policy'] = list(policy)
            p['listed'] = name in policies
            p['fold'] = fold
            p['same_as_S_A0'] = bool(p['status'] == a0['status'] and (p['status'] != 'OK' or (
                p['slot'] == a0['slot'] and np.array_equal(pmask, masks[f'S_A0_{k}']))))
            rec['S_PHR'] = p
            if p['status'] == 'OK':
                masks[f'S_PHR_{k}'] = pmask
        objects.data.pop(name, None); objects.stage.raw.pop(name, None)
        out.append(rec)
    dest = C.OUT/'seeds'/(C.stub(canonical)+'.npz')
    dest.parent.mkdir(parents=True, exist_ok=True)
    arrays = {key: np.packbits(m.reshape(-1)) for key, m in masks.items()}
    np.savez_compressed(dest, shape=np.array(C.CANVAS), **arrays)
    return dict(capture=canonical, room=c['room'], objects=out, seeds_file=str(dest), seeds_sha256=C.sha256_file(dest),
                seconds=time.monotonic()-started, pins=C.all_pins())


def main():
    limit = sys.argv[1] if len(sys.argv) > 1 else 'all'
    parity = '--phr-parity' in sys.argv
    t0 = time.monotonic()
    init_worker()
    caps = sorted(STATE['caps'].values(), key=lambda c: c['canonical'])
    if limit.isdigit():
        caps = caps[:int(limit)]
    elif limit != 'all':
        only = limit.split(',')
        caps = [c for c in caps if c['canonical'] in only]
        limit = 'only'
    pub = L.published(('A0_deployed',))
    mf = L.maskfail_records()
    table_status, table, provenance = PH.table()
    jobs = []
    for c in caps:
        rows = [r for r in c['rows'] if r['id'] in STATE['rowids']]
        frames = {}
        for r in rows:
            for n in r['operands']:
                frames[n] = pub[('A0_deployed', r['id'])]['member_frames'][n]
        jobs.append((c['canonical'], frames, mf.get(c['canonical'], []), table_status, table, parity))
    with ProcessPoolExecutor(8, initializer=init_worker) as pool:
        results = list(pool.map(one, *zip(*jobs)))
    pins = {}
    for r in results:
        pins.update(r.pop('pins'))
        C.PINS[r['seeds_file']] = r['seeds_sha256']
    C.PINS.update(pins)
    objs = [o for r in results for o in r['objects']]
    count = lambda s, st: sum(o[s]['status'] == st for o in objs)
    check = dict(objects=len(objs), passed=sum(o['check1']['passed'] for o in objs),
                 captures_passed=sum(all(o['check1']['passed'] for o in r['objects']) for r in results), captures=len(results))
    summary = dict(objects=len(objs), S_A0=dict(ok=count('S_A0', 'OK'), refused=count('S_A0', 'REFUSED'), unseen=count('S_A0', 'UNSEEN'),
                                                on_target=sum(o['S_A0'].get('on_target', False) for o in objs)),
                   S_GT=dict(ok=count('S_GT', 'OK'), not_visible=count('S_GT', 'NOT_VISIBLE')),
                   S_PHR=dict(status=table_status, phrase_folds=provenance, ok=count('S_PHR', 'OK'),
                              on_target=sum(o['S_PHR'].get('on_target', False) for o in objs),
                              differs_from_S_A0=sum(not o['S_PHR'].get('same_as_S_A0', True) for o in objs),
                              second_calls=sum(o['S_PHR'].get('calls', 1) > 1 for o in objs),
                              unlisted_names=sorted({o['name'] for o in objs if o['S_PHR'].get('listed') is False}),
                              policies=sorted({'|'.join(o['S_PHR'].get('policy', [o['name']])) for o in objs if o['S_PHR'].get('policy', [o['name']]) != [o['name']]})))
    if parity:
        summary['phr_path_parity'] = dict(objects=sum('phr_parity' in o for o in objs), equal=sum(o.get('phr_parity', False) for o in objs))
    C.code_pins()
    name = 'SEEDS.json' if limit == 'all' else 'SEEDS_only.json' if limit == 'only' else f'SEEDS_first{limit}.json'
    C.write_json(C.OUT/'seeds'/name, dict(scope=f'{len(caps)} of 209 priced K1 training captures', summary=summary, check1=check,
                                          captures=results, seconds=time.monotonic()-t0,
                                          rules=dict(S_A0='served mask of the A0 track on obj["best"] (largest 240x320 area among lifted frames, ties lowest)',
                                                     S_GT='raster instance on its largest valid anchor by native share, nearest-resized to 480x640',
                                                     on_target='seed IoU >= 0.5 against the raster at 240 x 320')))
    print(json.dumps(dict(summary=summary, check1=check, seconds=time.monotonic()-t0)), flush=True)
    C.status(f'Stage 2 (seeds, {name}): check 1 {check["passed"]}/{check["objects"]} objects, {check["captures_passed"]}/{check["captures"]} captures; '
             f'S_A0 {summary["S_A0"]}, S_GT {summary["S_GT"]}, S_PHR {table_status}.')


if __name__ == '__main__':
    main()
