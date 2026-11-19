"""Index every local GT raster named by the task and authenticate it against its pin.

Sources (bounded listings only): K1 rasters gt_build/out/dose_pool/out/{t1_gt,arkit_gt}/gt and
gt_build2/out/dose_pool/out/arkit_gt/gt (pins: gt_build2/out/PIN_CHECK.tsv), and the store-side
raster directory n30_mirror/rows_r1/work/codeB/rasters (pins: each file's sidecar JSON).
"""
import hashlib, json, sys
from pathlib import Path

OUT = Path(__file__).resolve().parent / 'out'
N30 = Path('/scratch/jjyeung/orch_n30')
K1_DIRS = [N30 / 'gt_build/out/dose_pool/out/t1_gt/gt', N30 / 'gt_build/out/dose_pool/out/arkit_gt/gt',
           N30 / 'gt_build2/out/dose_pool/out/arkit_gt/gt']
K1_PINS = N30 / 'gt_build2/out/PIN_CHECK.tsv'
CODEB = Path('/scratch/jjyeung/n30_mirror/rows_r1/work/codeB/rasters')
V3_PINS = Path('/scratch/jjyeung/n30_mirror/rows_a2/a2_vqa_v3/RASTERS_v3.json')


def fsha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''):
            h.update(b)
    return h.hexdigest()


def capture_of(name):
    stem = name[:-4]
    if '__' in stem:
        ds, sid = stem.split('__', 1)
        return {'scannet': 'scannet', 'scannetpp': 'scannetpp', 'scannetppv2': 'scannetpp'}[ds] + '/' + sid
    return 'arkitscenes/' + stem


def main():
    pins = {}
    for line in K1_PINS.read_text().splitlines()[1:]:
        cap, pin, built, verdict = line.split('\t')
        pins[cap] = pin
    v3 = json.loads(V3_PINS.read_text())
    index, refused = {}, []
    for d in K1_DIRS:
        for p in sorted(d.iterdir()):
            if p.suffix != '.npz':
                continue
            cap = capture_of(p.name); s = fsha(p)
            if pins.get(cap) != s:
                refused.append(dict(path=str(p), capture=cap, sha256=s, reason='sha256 differs from K1 PIN_CHECK pin'))
                continue
            assert cap not in index, cap
            index[cap] = dict(path=str(p), sha256=s, source='K1', pin=str(K1_PINS))
    for p in sorted(CODEB.iterdir()):
        if p.suffix != '.npz':
            continue
        cap = 'scannetpp/' + p.stem; s = fsha(p)
        side = p.with_suffix('.json')
        side_sha = json.loads(side.read_text()).get('sha256') if side.exists() else None
        v3pin = v3.get('scannetppv2__' + p.stem)
        if s != side_sha:
            refused.append(dict(path=str(p), capture=cap, sha256=s, reason='sha256 differs from sidecar JSON'))
            continue
        if cap in index:
            refused.append(dict(path=str(p), capture=cap, sha256=s, reason='capture already indexed from K1'))
            continue
        index[cap] = dict(path=str(p), sha256=s, source='codeB', pin=str(side), v3_pin_equal=(v3pin == s))
    value = dict(command='nice -n 10 python raster_index.py',
                 input_sha256={str(K1_PINS): fsha(K1_PINS), str(V3_PINS): fsha(V3_PINS)},
                 sources=[str(d) for d in K1_DIRS] + [str(CODEB)], rasters=index, refused=refused,
                 counts=dict(indexed=len(index), refused=len(refused),
                             by_source={s: sum(v['source'] == s for v in index.values()) for s in ('K1', 'codeB')}))
    OUT.mkdir(exist_ok=True)
    (OUT / 'RASTER_INDEX.json').write_text(json.dumps(value, indent=1, sort_keys=True) + '\n')
    print(json.dumps(value['counts']), [r['reason'] for r in refused][:5])


if __name__ == '__main__':
    main()
