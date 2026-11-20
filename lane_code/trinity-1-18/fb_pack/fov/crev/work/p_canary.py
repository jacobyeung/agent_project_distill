"""Check the scorer's P1 served-depth hash and P3 grid hash formulas against the producer's canary receipt and fov_check 762093b8."""
import hashlib, json
from array import array
import numpy as np
W = '/scratch/jjyeung/orch_n30/fb_pack/fov/crev/work/producer/'
rec = json.load(open(W + 'k1fwd2_example_FOV_RECEIPT.json'))
bars = json.load(open('/scratch/jjyeung/orch_n30/sb_own400/out/BARS_FROZEN.json'))
cap = next(c for c in bars['captures'] if c['canonical'] == rec['canonical'])
print('capture_sha256 equal', cap['capture_sha256'] == rec['capture_sha256'], 'key', cap['key'])
with np.load(cap['own544']['path'], allow_pickle=False) as z:
    depth = z['depth']
print('own_170235 depth dtype', depth.dtype, depth.shape, 'C', depth.flags['C_CONTIGUOUS'])
scorer = hashlib.sha256(np.ascontiguousarray(depth, dtype=np.float64).tobytes()).hexdigest()
print('scorer served sha', scorer, 'receipt', rec['served_depth_sha256'], 'equal', scorer == rec['served_depth_sha256'])
g_scorer = hashlib.sha256(np.linspace(0, 1000, 51, dtype=np.float32).tobytes()).hexdigest()
g_prod = hashlib.sha256(array('f', [1000 * i / 50 for i in range(51)]).tobytes()).hexdigest()
print('grid scorer', g_scorer, 'producer', g_prod, 'equal', g_scorer == g_prod)
ref = json.load(open('/scratch/jjyeung/orch_n30/sb_own400/kit/inputs/G3T_FOV.json'))['captures']
r = ref[rec['canonical']]
a = np.asarray(r['fov_hw_rad'], dtype=np.float64).astype(np.float32)
b = array('f', [x for pair in r['fov_hw_rad'] for x in pair])
print('fov_V2 float32 cast equal (scorer vs producer fov_check)', a.tobytes() == b.tobytes(), 'G3T captures', len(ref))
print('train keys', len(bars['captures']), 'all train', all(c['k1_split'] == 'train' for c in bars['captures']),
      'gt_present', sum(c['gt_present'] for c in bars['captures']))
