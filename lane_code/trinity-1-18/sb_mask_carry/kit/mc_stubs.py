"""Stub trackers in the real tracker's file format, for dry-run checks of the pricing path.

seed:    S_A0 seeds; the seed anchor alone carries, with the seed mask unchanged      -> out/dry/track/S_A0_STUBSEED
seedphr: the same on S_PHR seeds                                                     -> out/dry/track/S_PHR_STUBSEED
raster:  S_GT seeds; every anchor carries the native raster instance on valid frames -> out/dry/track/S_GT_STUBRASTER
Usage: python mc_stubs.py <seed|seedphr|raster> [n_captures|all]   (p1cpu interpreter)
"""
import json, sys, time
from concurrent.futures import ProcessPoolExecutor
import numpy as np
import mc_common as C
import mc_ladder as L
import mc_track_io as IO

KIND = {'seed': ('S_A0', 'STUBSEED'), 'seedphr': ('S_PHR', 'STUBSEED'), 'raster': ('S_GT', 'STUBRASTER')}
ROOT = C.OUT/'dry/track'
STATE = {}


def init(kind):
    if kind == 'raster':
        STATE['caps'] = {c['canonical']: c for c in L.setup(threads=1)[0]}


def build(kind, canonical, entry):
    C.PINS.clear()
    seed_set, frame_set = KIND[kind]
    seeds = IO.load_seeds(canonical)
    if kind == 'raster':
        gt, gt_raw = L.T().R.gt_arrays(STATE['caps'][canonical])
        raster, valid = gt_raw.get('inst', gt_raw.get('instances')), gt_raw['valid'].astype(bool)
    objects = []
    for o in entry['objects']:
        s = o[seed_set]
        if s['status'] != 'OK':
            continue
        slot = s['slot']
        if kind != 'raster':
            mask = seeds[f"{seed_set}_{o['k']}"]
            empty = np.zeros_like(mask)
            result = {t: ((mask, 1.) if t == slot-1 else (empty, -1.)) for t in range(32)}
            seed_mask = mask
        else:
            native = (raster == o['instance']) & valid[:, None, None]
            result = {t: (native[t], 1. if native[t].any() else -1.) for t in range(32)}
            seed_mask = native[slot-1]
        objects.append(IO.object_record(o['k'], o['name'], o['instance'], slot, list(range(32)), list(range(32)), result, seed_mask))
    dest = IO.track_path(seed_set, frame_set, canonical, ROOT)
    sha = C.write_json(dest, dict(capture=canonical, seed_set=seed_set, frame_set=frame_set, tracker=f'stub_{kind}',
                                  status='OK', objects=objects), gz=True)
    return canonical, sha


def main():
    kind = sys.argv[1]
    limit = sys.argv[2] if len(sys.argv) > 2 else 'all'
    t0 = time.monotonic()
    seeds = C.read_json(C.OUT/'seeds/SEEDS.json')
    entries = {r['capture']: r for r in seeds['captures']}
    caps = sorted(entries)
    if limit != 'all':
        caps = caps[:int(limit)]
    with ProcessPoolExecutor(8, initializer=init, initargs=(kind,)) as pool:
        done = list(pool.map(build, [kind]*len(caps), caps, [entries[k] for k in caps]))
    C.PINS.clear()
    C.pin(C.OUT/'seeds/SEEDS.json')
    C.code_pins()
    seed_set, frame_set = KIND[kind]
    C.write_json(IO.track_dir(seed_set, frame_set, ROOT)/'TRACK_INDEX.json',
                 dict(tracker=f'stub_{kind}', captures=dict(done), seconds=time.monotonic()-t0))
    print(json.dumps(dict(kind=kind, captures=len(done), seconds=time.monotonic()-t0)), flush=True)


if __name__ == '__main__':
    main()
