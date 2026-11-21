"""GTC-B step 1: arm b tracker seeds, deterministic, with sha256 of every seed mask; t and s seeds are rebuilt only to prove
they equal lever6/gtc/out/SEEDS_GTC.json byte for byte (and its seed npz arrays bit for bit), and are not written again.

b (t_big, ORCH ANSWER 2026-11-21T21:37Z): the bound GT instance raster (gt['inst'] == binding instance) on the anchor where its
  area at 240x320 is largest (ties go to the lowest anchor); tracked forward and backward over the 32 anchors (K1 carry rule,
  as s). Operands whose instance is on no anchor get no seed (NOT_VISIBLE) and keep empty masks, as in t. One unit per
  (capture, instance), as t.
t, s: unchanged from the GTC kit (first visible anchor; K1 S_A0 served seed).
Seeds go to the tracker at 480x640 through the served raster's resize (routed_features.resize, nearest, zoom order 0).
Writes out/SEEDS_GTCB.json and out/seeds/<capture>.npz (b units only; packbits, 240x320 and 480x640).
Usage: p1cpu python seeds.py
"""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gtc_common as G


MIN_PIXELS = 1  # the GTC t rule (first anchor with >= 1 pixel); fixed here, so the t seeds match SEEDS_GTC


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


def largest_visible(target):
    """1-based anchor where the instance's area is largest (np.argmax: ties go to the lowest anchor), or None when it has no pixel."""
    area = np.asarray(target, bool).reshape(len(target), -1).sum(1)
    return int(np.argmax(area))+1 if area.any() else None


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
            bslot = largest_visible(target)
            if bslot is None:
                rec['b'] = dict(status='NOT_VISIBLE')
            else:
                unit = f'b_{instance}'
                if unit not in c['units']:
                    c['units'][unit] = dict(unit=unit, arm='b', seed_slot=bslot, instance_id=instance, direction='both')
                    c['arrays'][unit] = target[bslot-1]
                rec['b'] = dict(status='OK', unit=unit, slot=bslot)
            records.append(rec)
    return caps, records


def unit_entries(c, arms, R):
    """(npz arrays, unit records) of one capture's units of the given arms, in the GTC kit's order and format."""
    arrays, units = {}, []
    chosen = [(k, v) for k, v in c['units'].items() if v['arm'] in arms]
    for unit, u in sorted(chosen, key=lambda kv: (kv[1]['arm'] != 't', kv[0])):
        m240 = np.asarray(c['arrays'][unit], bool)
        m480 = G.seed_to_canvas(m240, R.resize)
        arrays[unit+'__240'] = np.packbits(m240.reshape(-1)); arrays[unit+'__480'] = np.packbits(m480.reshape(-1))
        units.append(dict(u, seed_sha256_240=G.mask_sha(m240), seed_sha256_480=G.mask_sha(m480),
                          area_240=int(m240.sum()), share_240=float(m240.mean()),
                          roundtrip_exact=bool(np.array_equal(G.canvas_to_grid(m480), m240))))
    return arrays, units


def inputs_record(R):
    return dict(relift=str(G.RELIFT), relift_sha256=G.sha256_file(G.RELIFT), depth=str(G.DEPTH), depth_sha256=G.sha256_file(G.DEPTH),
                t1=str(R.BASE/'cap/t1.gz'), items=str(G.ITEMS), items_sha256=G.sha256_file(G.ITEMS))


def ts_text(R, caps, records, gtc):
    """SEEDS_GTC.json text rebuilt from this run's t and s seeds, in the GTC kit's exact format. Each capture's seeds_file and
    seeds_sha256 are taken from SEEDS_GTC (npz zip headers carry write times), after its arrays are checked bit for bit."""
    files = {c['capture']: c for c in gtc['captures']}
    if list(files) != list(caps):
        raise AssertionError('capture list differs from SEEDS_GTC')
    out = []
    for cap, c in caps.items():
        arrays, units = unit_entries(c, ('t', 's'), R)
        f = files[cap]
        if G.sha256_file(f['seeds_file']) != f['seeds_sha256']:
            raise AssertionError('GTC seed file differs from its recorded sha256: '+f['seeds_file'])
        with np.load(f['seeds_file'], allow_pickle=False) as z:
            if sorted(z.files) != sorted(arrays):
                raise AssertionError('t/s seed units differ from the GTC npz: '+cap)
            for k, v in arrays.items():
                if z[k].dtype != v.dtype or z[k].shape != v.shape or z[k].tobytes() != v.tobytes():
                    raise AssertionError('t/s seed array differs from the GTC npz: %s %s' % (cap, k))
        out.append(dict(capture=cap, dataset=G.dataset(cap), seeds_file=f['seeds_file'], seeds_sha256=f['seeds_sha256'], units=units))
    recs = [{k: v for k, v in r.items() if k != 'b'} for r in records]
    count = lambda arm, st: sum(r[arm]['status'] == st for r in recs)
    summary = dict(operands=len(recs), items=len({r['item_id'] for r in recs}), captures=len(out),
                   t=dict(ok=count('t', 'OK'), not_visible=count('t', 'NOT_VISIBLE'), units=sum(u['arm'] == 't' for c in out for u in c['units'])),
                   s=dict(ok=count('s', 'OK'), no_served_object=count('s', 'NO_SERVED_OBJECT'), unseen=count('s', 'UNSEEN'),
                          units=sum(u['arm'] == 's' for c in out for u in c['units'])),
                   roundtrip_exact_seeds=sum(u['roundtrip_exact'] for c in out for u in c['units']),
                   seeds=sum(len(c['units']) for c in out))
    body = dict(schema='gtc-seeds-v1', summary=summary, captures=out, objects=recs,
                rules=dict(t='bound GT instance raster (gt.inst == instance) on its first anchor with >= 1 pixel; tracked forward only; '  # SEEDS_GTC's wording
                             'earlier anchors empty; one unit per (capture, instance)',
                           s='K1 S_A0: served selected_masks on the deployed lift best frame (lift_plain: largest mask area among frames '
                             'with lifted points, ties lowest); none without a served object or when the lift does not see it; '
                             'one unit per (capture, slot, seed mask)',
                           resize='240x320 -> 480x640 by routed_features.resize (ndimage.zoom order 0, prefilter off); '
                                  'tracker 480x640 -> 240x320 by served path resize-to-SHAPE then [::2, ::2]',
                           seed_mask_sha256='sha256(json(shape) + packbits(C order))'),
                inputs=inputs_record(R))
    return getattr(json, '_a0_dumps', json.dumps)(body, allow_nan=False, separators=None, indent=1)+'\n'


def assert_ts_unchanged(R, caps, records):
    """t and s seeds of this build equal SEEDS_GTC.json byte for byte (and its npz arrays bit for bit)."""
    raw = G.SEEDS_TS.read_bytes()
    if ts_text(R, caps, records, json.loads(raw)).encode() != raw:
        raise AssertionError('t or s seeds differ from SEEDS_GTC.json')
    return G.sha256_bytes(raw)


def seed_facts(units, records):
    """Seed facts of arm b (not results): unit count, median and min area at 240x320, count under 200 px, and the items
    whose every operand has a b seed of >= 200 px."""
    area = np.array([u['area_240'] for u in units])
    amap = {(u['capture'], u['unit']): u['area_240'] for u in units}
    ok = {}
    for r in records:
        good = r['b']['status'] == 'OK' and amap[(r['capture'], r['b']['unit'])] >= 200
        ok[r['item_id']] = ok.get(r['item_id'], True) and good
    return dict(units=len(units), median_area_240=float(np.median(area)), min_area_240=int(area.min()), max_area_240=int(area.max()),
                under_200=int((area < 200).sum()), under_50=int((area < 50).sum()),
                items_all_seeds_200=sum(ok.values()))


def main(argv=None):
    import argparse
    argparse.ArgumentParser().parse_args(argv)
    R = G.load_relift(); R.dependencies()
    refs = {r['item_id']: r for r in json.loads(G.ITEMS.read_text())['items']}
    items, objects, _ = G.eligible(R, refs)
    rows = R.read_records(R.BASE/'cap/t1.gz', refs)
    depths = G.depth_rows(R)
    caps, records = build(R, refs, rows, depths, items, objects)
    ts_sha = assert_ts_unchanged(R, caps, records)
    out, flat = [], []
    for cap, c in caps.items():
        arrays, units = unit_entries(c, G.B_ARMS, R)
        if not units:
            continue
        dest = G.OUT/'seeds'/(G.stub(cap)+'.npz'); dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_name(dest.name+'.tmp.npz')
        np.savez_compressed(tmp, **arrays); tmp.replace(dest)
        out.append(dict(capture=cap, dataset=G.dataset(cap), seeds_file=str(dest), seeds_sha256=G.sha256_file(dest), units=units))
        flat += [dict(u, capture=cap) for u in units]
    recs = [dict(item_id=r['item_id'], capture=r['capture'], name=r['name'], instance_id=r['instance_id'], b=r['b']) for r in records]
    summary = dict(operands=len(recs), items=len({r['item_id'] for r in recs}), captures=len(caps), captures_with_b=len(out),
                   b=dict(ok=sum(r['b']['status'] == 'OK' for r in recs), not_visible=sum(r['b']['status'] == 'NOT_VISIBLE' for r in recs),
                          units=len(flat)),
                   seed_facts=seed_facts(flat, recs),
                   seed_facts_by_dataset={d: seed_facts([u for u in flat if G.dataset(u['capture']) == d],
                                                        [r for r in recs if G.dataset(r['capture']) == d])
                                          for d in ('ARKit', 'ScanNet/ScanNet++')},
                   roundtrip_exact_seeds=sum(u['roundtrip_exact'] for u in flat))
    body = dict(schema='gtcb-seeds-v1', summary=summary, captures=out, objects=recs,
                ts_unchanged=dict(seeds_gtc=str(G.SEEDS_TS), sha256=ts_sha, byte_identical=True,
                                  note='t and s seeds rebuilt by this script equal SEEDS_GTC.json byte for byte and its npz arrays bit for bit'),
                rules=dict(b='bound GT instance raster (gt.inst == instance) on the anchor where its area at 240x320 is largest (ties lowest '
                             'anchor); tracked forward and backward over the 32 anchors under the K1 carry rule; operands whose instance is '
                             'on no anchor have no seed and keep empty masks; one unit per (capture, instance)',
                           resize='240x320 -> 480x640 by routed_features.resize (ndimage.zoom order 0, prefilter off); '
                                  'tracker 480x640 -> 240x320 by served path resize-to-SHAPE then [::2, ::2]',
                           seed_mask_sha256='sha256(json(shape) + packbits(C order))'),
                inputs=inputs_record(R))
    G.write_json(G.SEEDS_B, body)
    print(json.dumps(dict(units=len(flat), ok=summary['b']['ok'], not_visible=summary['b']['not_visible'], ts_byte_identical=True)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
