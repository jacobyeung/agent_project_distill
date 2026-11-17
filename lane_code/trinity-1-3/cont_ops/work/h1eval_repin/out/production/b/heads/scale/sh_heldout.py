"""Exact path: E3 harness (copy) on held-out captures with an added scale arm SH from ScaleHead.

Runs arms S4+G1, SO+G1 and SH+G1 (plus GT unless --no-gt) with E3's train-only FITS.json.
Usage (inside the harness copy, via run.sh's environment): python -B sh_heldout.py SH_SCALES.json [k n]
"""
import hashlib, json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import importlib.util as iu
sp = iu.spec_from_file_location('e3h', str(HERE / 'harness.py'))
H = iu.module_from_spec(sp)
sp.loader.exec_module(H)

sh = json.load(open(sys.argv[1]))
k, n = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (0, 1)
H.SCALES = ('S4', 'SO', 'SH')
H.GRAVITIES = ('G1',)
_scales = H.scales


def scales(f, fits):
    out = _scales(f, fits)
    out['SH'] = float(sh['captures'][f['capture']]['SH'])
    return out


H.scales = scales
fits = json.load(open(H.OUT / 'FITS.json'))
cs, cache, inv = H.inventory()
ho = [c for c in cs if c['k1_split'] == 'heldout'][k::n]
assert {c['canonical'] for c in [c for c in cs if c['k1_split'] == 'heldout']} == set(sh['captures'])
dest = HERE / 'out_sh'
dest.mkdir(exist_ok=True)
for c in ho:
    tower = cache[H.digest(c)][0] / 'tower.npz'
    assert hashlib.sha256(tower.read_bytes()).hexdigest() == sh['captures'][c['canonical']]['tower_sha256'], 'tower mismatch'
    gt, tw, hw = H.load_capture(c, cache[H.digest(c)], True)
    f = H.features(c, tw, gt, hw, 'specified')
    rows = H.evaluate_capture(c, gt, tw, hw, f, fits, None, False)
    H.dump(dest / (c['canonical'].replace('/', '__') + '.json'), dict(diagnostics=f, items=rows))
    print(c['canonical'], flush=True)
print('SHARD_DONE', flush=True)
