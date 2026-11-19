"""Reviewer's own 64-frame DA3 CPU forward on one K1 train capture (sealed backend, own driver)."""
import hashlib, json, os, resource, sys, time
from pathlib import Path
import numpy as np
os.environ['CUDA_VISIBLE_DEVICES'] = ''
cap = sys.argv[1]
out = Path(__file__).resolve().parent / 'out/forward' / cap.replace('/', '__'); out.mkdir(parents=True, exist_ok=True)
m = json.load(open('/scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json'))
c = next(c for c in m['captures'] if c['canonical'] == cap)
assert c['k1_split'] == 'train'
for f in c['dense_frames']:
    assert hashlib.sha256(Path(f['path']).read_bytes()).hexdigest() == f['sha256'], f['path']
from geo_bakeoff.backends import Backend
from geo_bakeoff.contract import sample_grid
t = time.monotonic()
b = Backend('da3', 'cpu', 8, None)
pred = b.predict([f['path'] for f in c['dense_frames']])
frames = [int(f['index']) for f in c['dense_frames']]
np.savez_compressed(out / 'pred.npz', frame_indices=np.asarray(frames), anchor_slots=np.asarray([frames.index(i) for i in c['anchor_indices']]),
                    depth_grid64=sample_grid(pred.depth).astype(np.float32), intrinsics=pred.intrinsics.astype(np.float64),
                    c2w=pred.c2w.astype(np.float64), source_hw=np.asarray(pred.source_hw))
json.dump(dict(capture=cap, seconds=time.monotonic() - t, peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
               metadata=json.loads(json.dumps(pred.metadata, default=str))), open(out / 'DONE.json', 'w'), indent=1)
print('DONE', cap, time.monotonic() - t, flush=True)
