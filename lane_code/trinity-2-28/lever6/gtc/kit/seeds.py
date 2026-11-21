"""Step 2: one tracker seed per (item, operand) and arm, deterministic, with sha256 of every seed mask.

t (GT seed): the bound GT instance raster (relift's `target` = gt['inst'] == binding instance) on the FIRST anchor where it
  has at least one pixel; frames before that anchor are empty by definition. One unit per (capture, instance).
s (served seed, K1 S_A0 rule, sb_cachk/kit_v2/mc_seeds.py a0_seed): the served mask (T1 row's selected_masks, cell a's input)
  on obj['best'] of the deployed lift (grounding.lift_bestspread -> lift_plain best: largest mask area among frames with lifted
  points, ties lowest); none when the operand has no served object or the lift does not see it. One unit per distinct
  (capture, seed anchor, seed mask).
Seeds go to the tracker at 480x640 through the served raster's resize (routed_features.resize, nearest, zoom order 0), the
same rule K1 used for S_GT seeds. Writes out/SEEDS_GTC.json and out/seeds/<capture>.npz (packbits, 240x320 and 480x640).
Usage: p1cpu python seeds.py [--t-min-pixels N]   (default 1 = the ruling's 'first anchor where visible')
"""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gtc_common as G


MIN_PIXELS = 1  # registered default: "visible" = at least one pixel; --t-min-pixels N changes it (recorded in the rules)


def first_visible(target, min_pixels=1):
    """1-based first anchor where the instance has at least min_pixels pixels, or None."""
    vis = np.asarray(target, bool).reshape(len(target), -1).sum(1) >= min_pixels
    return int(np.argmax(vis))+1 if vis.any() else None


def served_seed(R, name, obj, g):
    """(status, slot, masks) for the s arm; masks are the served (32,240,320) selected masks."""
    if obj is None:
        return 'NO_SERVED_OBJECT', None, np.zeros((32,)+G.GRID, bool)
    masks = R.masks_array(obj['selected_masks'])
    lift = R.grounding.lift_bestspread(name, masks, g)
    if not lift['seen']:
        return 'UNSEEN', None, masks
    return 'OK', int(lift['best']), masks


def build(R, refs, rows, depths, items, objects):
    caps = {}
    records = []
    by_item = {}
    for o in objects:
        by_item.setdefault(o['item_id'], []).append(o)
    gt_of = {i['item_id']: i['gt_path'] for i in items}
    for cap in sorted({i['capture'] for i in items}):
        caps[cap] = dict(capture=cap, units={}, arrays={})
    loaded = {}
    for it in items:
        cap, iid = it['capture'], it['item_id']
        if cap not in loaded:
            loaded.clear()
            with np.load(gt_of[iid], allow_pickle=False) as z:
                loaded[cap] = (z['inst'].copy(), R.restore(depths[cap]))
        inst, g = loaded[cap]
        row = rows[iid]; served = {o['name'].strip().lower(): o for o in row['objects']}
        c = caps[cap]
        for o in by_item[iid]:
            name, instance = o['name'], o['instance_id']
            target = inst == instance
            rec = dict(item_id=iid, capture=cap, name=name, instance_id=instance)
            slot = first_visible(target, MIN_PIXELS)
            if slot is None:
                rec['t'] = dict(status='NOT_VISIBLE')
            else:
                unit = f't_{instance}'
                if unit not in c['units']:
                    seed = target[slot-1]
                    c['units'][unit] = dict(unit=unit, arm='t', seed_slot=slot, instance_id=instance, direction='forward')
                    c['arrays'][unit] = seed
                rec['t'] = dict(status='OK', unit=unit, slot=slot)
            status, sslot, masks = served_seed(R, name, served.get(name.strip().lower()), g)
            if status != 'OK':
                rec['s'] = dict(status=status)
            else:
                seed = masks[sslot-1]
                h = G.mask_sha(seed)
                unit = f's_{sslot}_{h[:16]}'
                if unit not in c['units']:
                    c['units'][unit] = dict(unit=unit, arm='s', seed_slot=sslot)
                    c['arrays'][unit] = seed
                rec['s'] = dict(status='OK', unit=unit, slot=sslot)
            records.append(rec)
    return caps, records


def main(argv=None):
    global MIN_PIXELS
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument('--t-min-pixels', type=int, default=1)
    MIN_PIXELS = ap.parse_args(argv).t_min_pixels
    if MIN_PIXELS < 1:
        raise SystemExit('--t-min-pixels must be >= 1')
    R = G.load_relift(); R.dependencies()
    refs = {r['item_id']: r for r in json.loads(G.ITEMS.read_text())['items']}
    items, objects, _ = G.eligible(R, refs)
    rows = R.read_records(R.BASE/'cap/t1.gz', refs)
    depths = G.depth_rows(R)
    caps, records = build(R, refs, rows, depths, items, objects)
    out = []
    for cap, c in caps.items():
        arrays = {}
        units = []
        for unit, u in sorted(c['units'].items(), key=lambda kv: (kv[1]['arm'] != 't', kv[0])):
            m240 = np.asarray(c['arrays'][unit], bool)
            m480 = G.seed_to_canvas(m240, R.resize)
            arrays[unit+'__240'] = np.packbits(m240.reshape(-1)); arrays[unit+'__480'] = np.packbits(m480.reshape(-1))
            units.append(dict(u, seed_sha256_240=G.mask_sha(m240), seed_sha256_480=G.mask_sha(m480),
                              area_240=int(m240.sum()), share_240=float(m240.mean()),
                              roundtrip_exact=bool(np.array_equal(G.canvas_to_grid(m480), m240))))
        dest = G.OUT/'seeds'/(G.stub(cap)+'.npz'); dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_name(dest.name+'.tmp.npz')
        np.savez_compressed(tmp, **arrays); tmp.replace(dest)
        out.append(dict(capture=cap, dataset=G.dataset(cap), seeds_file=str(dest), seeds_sha256=G.sha256_file(dest), units=units))
    count = lambda arm, st: sum(r[arm]['status'] == st for r in records)
    summary = dict(operands=len(records), items=len({r['item_id'] for r in records}), captures=len(out),
                   t=dict(ok=count('t', 'OK'), not_visible=count('t', 'NOT_VISIBLE'), units=sum(u['arm'] == 't' for c in out for u in c['units'])),
                   s=dict(ok=count('s', 'OK'), no_served_object=count('s', 'NO_SERVED_OBJECT'), unseen=count('s', 'UNSEEN'),
                          units=sum(u['arm'] == 's' for c in out for u in c['units'])),
                   roundtrip_exact_seeds=sum(u['roundtrip_exact'] for c in out for u in c['units']),
                   seeds=sum(len(c['units']) for c in out))
    body = dict(schema='gtc-seeds-v1', summary=summary, captures=out, objects=records,
                rules=dict(t=f'bound GT instance raster (gt.inst == instance) on its first anchor with >= {MIN_PIXELS} pixel(s) at 240x320; tracked forward only; '
                             'earlier anchors empty; one unit per (capture, instance)',
                           s='K1 S_A0: served selected_masks on the deployed lift best frame (lift_plain: largest mask area among frames '
                             'with lifted points, ties lowest); none without a served object or when the lift does not see it; '
                             'one unit per (capture, slot, seed mask)',
                           resize='240x320 -> 480x640 by routed_features.resize (ndimage.zoom order 0, prefilter off); '
                                  'tracker 480x640 -> 240x320 by served path resize-to-SHAPE then [::2, ::2]',
                           seed_mask_sha256='sha256(json(shape) + packbits(C order))'),
                inputs=dict(relift=str(G.RELIFT), relift_sha256=G.sha256_file(G.RELIFT), depth=str(G.DEPTH), depth_sha256=G.sha256_file(G.DEPTH),
                            t1=str(R.BASE/'cap/t1.gz'), items=str(G.ITEMS), items_sha256=G.sha256_file(G.ITEMS)))
    G.write_json(G.OUT/'SEEDS_GTC.json', body)
    print(json.dumps(summary))
    return 0


if __name__ == '__main__':
    sys.exit(main())
