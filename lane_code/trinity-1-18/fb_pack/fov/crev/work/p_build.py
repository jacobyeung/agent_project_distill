"""Build a producer-format delivery for all 242 train keys (V1 = V2 = arm A depth) and its FOV_CHECK.json from the
producer's own fov_check 762093b8 (only its tar loader is replaced by a directory reader). Three fabricated held-out
keys (invented canonicals, no real held-out data) get rows in FOV_CHECK.json but no capture dir under native/probe."""
import copy, hashlib, io, json, sys, tarfile
from pathlib import Path
import numpy as np
W = Path('/scratch/jjyeung/orch_n30/fb_pack/fov/crev/work')
P = W / 'producer'
T = W / 'tree/in/own_544_fov'
PROBE, FAKE = T / 'native/probe', W / 'tree/fake_heldout'
BARS = Path('/scratch/jjyeung/orch_n30/sb_own400/out/BARS_FROZEN.json')
G3T = Path('/scratch/jjyeung/orch_n30/sb_own400/kit/inputs/G3T_FOV.json')
MANIFEST = Path('/scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json')


def digest(x):
    return hashlib.sha256(json.dumps(x, sort_keys=True, allow_nan=False).encode()).hexdigest()


def sha(b):
    return hashlib.sha256(b).hexdigest()


def npz(**arrays):
    buf = io.BytesIO()
    np.savez_compressed(buf, **arrays)
    return buf.getvalue()


bars = json.loads(BARS.read_text())
ref = json.loads(G3T.read_text())['captures']
rec0 = json.loads((P / 'k1fwd2_example_FOV_RECEIPT.json').read_text())
phase0 = json.loads((P / 'k1fwd2_example_PHASE_COMPLETE.json').read_text())
train = {c['canonical']: c for c in json.loads(MANIFEST.read_text())['captures'] if c['k1_split'] == 'train'}
old, new, manifest = {}, {}, []


def emit(dest, cap_sha, canonical, own_bytes, depth, fovs, depths, missing):
    arrays = {**{'depth_' + k: v for k, v in depths.items()}, **{'fov_' + k: v for k, v in fovs.items()}}
    fb = npz(**arrays)
    rec = copy.deepcopy(rec0)
    rec.update(capture_sha256=cap_sha, canonical=canonical, missing=missing, keys=sorted(arrays),
               served_depth_sha256=sha(np.ascontiguousarray(depth).tobytes()), files={'fov.npz': sha(fb)})
    phase = copy.deepcopy(phase0)
    phase.update(capture_sha256=cap_sha, files={'own.npz': sha(own_bytes)})
    dest.mkdir(parents=True, exist_ok=False)
    (dest / 'fov.npz').write_bytes(fb)
    (dest / 'FOV_RECEIPT.json').write_text(json.dumps(rec, indent=2) + '\n')
    (dest / 'PHASE_COMPLETE.json').write_text(json.dumps(phase, indent=2) + '\n')
    return {'own.npz': own_bytes, 'fov.npz': fb, 'FOV_RECEIPT.json': (dest / 'FOV_RECEIPT.json').read_bytes(),
            'PHASE_COMPLETE.json': (dest / 'PHASE_COMPLETE.json').read_bytes()}


for c in bars['captures']:
    full = train[c['canonical']]
    assert digest(full) == c['capture_sha256']
    manifest.append(full)
    own_bytes = Path(c['own544']['path']).read_bytes()
    assert sha(own_bytes) == c['own544']['sha256']
    with np.load(io.BytesIO(own_bytes), allow_pickle=False) as z:
        A = z['depth']
    f2 = np.asarray(ref[c['canonical']]['fov_hw_rad'], dtype=np.float64).astype(np.float32)
    fovs = {'B': (f2 * np.float32(1.02)).astype(np.float32), 'V1': (f2 * np.float32(0.8)).astype(np.float32), 'V2': f2}
    old[c['key']] = {'own.npz': own_bytes}
    new[c['key']] = emit(PROBE / c['key'], c['capture_sha256'], c['canonical'], own_bytes, A, fovs,
                         {'V1': A.copy(), 'V2': A.copy()}, {})
donor = bars['captures'][0]
own_bytes = Path(donor['own544']['path']).read_bytes()
with np.load(io.BytesIO(own_bytes), allow_pickle=False) as z:
    A = z['depth']
for i in range(3):
    cap = {'canonical': f'fakeheldout/{i:04d}', 'k1_split': 'heldout', 'room': 'fakeroom', 'anchor_indices': list(range(0, 64, 2))}
    key = digest(cap['canonical'])[:16]
    manifest.append(cap)
    f = np.full((32, 2), 1.0, dtype=np.float32)
    old[key] = {'own.npz': own_bytes}
    new[key] = emit(FAKE / key, digest(cap), cap['canonical'], own_bytes, A, {'B': f, 'V1': f}, {'V1': A.copy()},
                    {'V2': 'MISSING: no cached G3T FoV for this capture (outside the scored set)'})
overlay = W / 'tree/overlay.tar'
with tarfile.open(overlay, 'w') as t:
    data = json.dumps({'captures': manifest}).encode()
    info = tarfile.TarInfo('manifest.json')
    info.size = len(data)
    t.addfile(info, io.BytesIO(data))
src = (P / 'k1fwd2_example_fov_check_762093b8.py.txt').read_text()
ns = {'__name__': 'fov_check_762093b8'}
exec(compile(src, 'fov_check_762093b8.py', 'exec'), ns)
ns['load'] = lambda token: {'OLD': old, 'NEW': new}[token]
(T / 'k1fwd2').mkdir(parents=True)
sys.argv = ['fov_check.py', 'OLD', 'NEW', str(G3T), str(T / 'k1fwd2/FOV_CHECK.json'), str(overlay), 'manifest.json']
ns['main']()
