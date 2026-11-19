"""Price carried tracks through sb_kbox4's unchanged ladder (lifted, evaluate, session_distance) on all 1,037 rows.

Arms per (seed set, frame set): C_best1 (rule best1) and C_fused (each fold's rule from FREEZE.json fused_folds).
An operand without a carried track (refused seed) is the empty object and its rows refuse, scored 0.
Usage: python mc_price.py <track_dir> <price_dir> [n_captures|all|canonical,...]   (p1cpu interpreter)
"""
import json, sys, time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from types import SimpleNamespace as NS
import numpy as np
import mc_common as C
import mc_ladder as L
import mc_measure as MS
import mc_track_io as IO

STATE = {}


def init_worker():
    caps, labels, rowids, tableids, folds, truth, head = L.setup(threads=1)
    freeze = C.read_json(C.BOX/'out/box_ladder/FREEZE.json')
    STATE.update(caps={c['canonical']: c for c in caps}, labels=labels, rowids=rowids, folds=folds, truth=truth,
                 fused={int(k): v['rule'] for k, v in freeze['fused_folds'].items()})


def downsample(masks, shape):
    """Canvas masks (480 x 640) go to the 240 x 320 serving canvas the way A0's served masks do ([::2, ::2])."""
    if masks.shape[1:] == tuple(shape):
        return masks
    if masks.shape[1:] == (2*shape[0], 2*shape[1]):
        return masks[:, ::2, ::2]
    from scipy import ndimage
    return np.stack([ndimage.zoom(m, (shape[0]/m.shape[0], shape[1]/m.shape[1]), order=0, prefilter=False) for m in masks])


def price_capture(canonical, track_file, arm_tag, maskfail):
    t = L.T()
    import predicted
    started = time.monotonic()
    c = STATE['caps'][canonical]
    rows = [r for r in c['rows'] if r['id'] in STATE['rowids']]
    names = sorted({n for r in rows for n in r['operands']})
    geo, cache, meta, gt, gt_raw, ref = L.capture_inputs(c)
    del cache
    track = IO.read_track(track_file) if track_file and Path(track_file).exists() else dict(objects=[], status='MISSING')
    byname = {o['name']: o for o in track['objects']}
    shape = gt['instances'].shape[1:]
    classes = {int(i): str(n) for i, n in zip(gt_raw['ids'], gt_raw['labels'])}
    mf = {}
    for r in maskfail:
        mf[(r['row'], r['object'], r['frame'])] = r
    objects, diags, table, carried_masks = {}, {}, [], {}
    for name in names:
        iid = int(c['gt_name_ids'][name][0])
        o = byname.get(name)
        if o is None:
            objects[name] = t.empty(name)
            diags[name] = dict(carry_status='NO_SEED')
            carried_masks[name] = np.zeros((32,)+tuple(shape), bool)
            continue
        native = IO.anchor_masks(o)
        objects[name] = t.lifted(name, native if native.shape[1:] != C.CANVAS else native[:, ::2, ::2], geo)
        masks = downsample(native, shape)
        carried_masks[name] = masks
        truth = gt['instances'] == iid
        seed = o['seed_slot']
        members = [NS(frame=a['slot'], mask=masks[a['slot']-1]) for a in o['anchors'] if a['carried'] and not a['seed'] and masks[a['slot']-1].any()]
        prec = predicted.member_precision(members, truth)
        seed_member = NS(frame=seed, mask=masks[seed-1])
        seed_major = t.majority([seed_member], gt['instances'])
        major_hits = sum(seed_major is not None and t.majority([m], gt['instances']) == seed_major for m in members)
        seed_iou = C.iou(masks[seed-1], truth[seed-1])
        diags[name] = dict(carry_status='OK', seed_slot=seed, seed_iou=seed_iou, on_target=bool(seed_iou is not None and seed_iou >= .5),
                           carried_slots=[a['slot'] for a in o['anchors'] if a['carried']],
                           member_precision=prec, seed_majority=seed_major, majority_correct=major_hits)
        for a in o['anchors']:
            f = a['slot']-1
            table.append(dict(capture=canonical, name=name, instance=iid, slot=a['slot'], seed=a['seed'], carried=a['carried'],
                              score=a['score'], area=float(masks[f].mean()), iou=C.iou(masks[f], truth[f]) if gt['valid'][f] else None,
                              valid=bool(gt['valid'][f]), raster_share=float(np.mean(gt['raster'][f] == iid))))
    fold = STATE['folds'][c['room']]
    items = t.evaluate(c, rows, geo, objects, f'C_best1/{arm_tag}', 'best1', STATE['labels'], STATE['folds'], STATE['truth'], gt, diags, meta)
    items += t.evaluate(c, rows, geo, objects, f'C_fused/{arm_tag}', STATE['fused'][fold], STATE['labels'], STATE['folds'], STATE['truth'], gt, diags, meta)
    for r in items:
        r['fusion_rule'] = 'best1' if r['arm'].startswith('C_best1') else STATE['fused'][fold]
    records = []
    for row in rows:
        for name in row['operands']:
            iid = int(c['gt_name_ids'][name][0])
            best = objects[name].get('best')
            for f in range(32):
                base = mf.get((row['id'], name, f+1))
                if base is None:
                    raise KeyError(f'MASKFAIL record missing {canonical} {row["id"]} {name} {f+1}')
                keep = {k: base[k] for k in ('capture', 'dataset', 'object', 'instance', 'frame', 'source_frame', 'class', 'share_bin',
                                              'deployed_best_iou', 'teacher_best_iou', 'deployed_candidate_count', 'row')}
                keep['pricing_best_frame'] = best
                rec = MS.frame_record(keep, carried_masks[name][f], gt['instances'][f], gt['raster'][f], iid, classes, gt['valid'][f])
                records.append({k: rec[k] for k in ('capture', 'dataset', 'row', 'object', 'instance', 'frame', 'iou', 'valid', 'visible',
                                                    'share', 'served_area', 'pricing_best_frame', 'failure_kinds', 'deployed_best_iou',
                                                    'teacher_best_iou', 'class', 'share_bin')})
    return dict(capture=canonical, room=c['room'], fold=fold, track_status=track.get('status', 'OK'), items=items, table=table,
                records=records, seconds=time.monotonic()-started, pins=C.all_pins())


def main():
    track_root, price_root = Path(sys.argv[1]), Path(sys.argv[2])
    limit = sys.argv[3] if len(sys.argv) > 3 else 'all'
    seed_set, frame_set = track_root.name.split('_', 2)[0]+'_'+track_root.name.split('_', 2)[1], track_root.name.split('_', 2)[2]
    arm_tag = f'{seed_set}/{frame_set}'
    t0 = time.monotonic()
    init_worker()
    caps = sorted(STATE['caps'])
    if limit.isdigit():
        caps = caps[:int(limit)]
    elif limit != 'all':
        caps = [k for k in caps if k in limit.split(',')]
    mf = L.maskfail_records()
    jobs = [(k, str(track_root/(C.stub(k)+'.json.gz')), arm_tag, mf.get(k, [])) for k in caps]
    price_root.mkdir(parents=True, exist_ok=True)
    done = []
    with ProcessPoolExecutor(8, initializer=init_worker) as pool:
        for res in pool.map(price_capture, *zip(*jobs)):
            pins = res.pop('pins')
            C.PINS.clear(); C.PINS.update(pins)
            sha = C.write_json(price_root/(C.stub(res['capture'])+'.json.gz'), res, gz=True)
            done.append(dict(capture=res['capture'], sha256=sha, seconds=res['seconds'], track_status=res['track_status']))
    C.PINS.clear()
    for d in done:
        C.PINS[str(price_root/(C.stub(d['capture'])+'.json.gz'))] = d['sha256']
    C.code_pins()
    C.write_json(price_root/'PRICE_INDEX.json', dict(arm=arm_tag, track_root=str(track_root), captures=done, seconds=time.monotonic()-t0))
    print(json.dumps(dict(arm=arm_tag, captures=len(done), seconds=time.monotonic()-t0,
                          missing_tracks=sum(d['track_status'] == 'MISSING' for d in done))), flush=True)


if __name__ == '__main__':
    main()
