"""Measure the production FrozenG3TTower on CPU with the pinned weights and the
first capture's 64 served PNGs (dense/anchor indices synthetic; timing only)."""
import io, json, os, resource, sys, tarfile, time
p = '/scratch/jjyeung/b01ec87a6f29b/p'
sys.path[:0] = [p+'/b', p+'/tree', p]
import l
l.install(p)
import torch
threads = int(sys.argv[1]); torch.set_num_threads(threads)
from PIL import Image
caps = json.load(open(p+'/g/2.json'))
if 'a0' in caps: caps = json.loads(bytes.fromhex(caps['a0']))
name = caps['first']
if len(sys.argv) > 2:
    def L(path):
        v = json.load(open(path)); return json.loads(bytes.fromhex(v['a0'])) if 'a0' in v else v
    rows = {r['item_id']: r for r in L(p+'/g/0.json')['items']}
    reps = [rows[i] for i in L(p+'/g/8.json')['representatives']]
    pick = [r for r in reps if r['mapping']['dense_count'] == int(sys.argv[2])][0]
    name = pick['capture']; print(json.dumps(dict(capture_index=reps.index(pick))), flush=True)
members = caps['captures'][name]
t0 = time.monotonic()
with tarfile.open('/x/a2.tar') as tar:
    images = [Image.open(io.BytesIO(tar.extractfile(m['path']).read())).convert('RGB') for m in members]
read_s = time.monotonic()-t0
from student_pilot.tower_read import FrozenG3TTower
tower = FrozenG3TTower(dict(weights_path='/x/g/model.safetensors', config_path='/x/g/config.json',
                            device='cpu', dense_frames=len(images), depth_chunk_size=8, dtype='bf16'))
indices = list(range(0, 37*len(images), 37)); slots = list(range(0, len(images), len(images)//32))[:32]
batch = dict(tower_native_frames=images, tower_frame_indices=indices, tower_anchor_slots=slots,
             frame_indices=[indices[s] for s in slots])
t0 = time.monotonic(); tower._load(); load_s = time.monotonic()-t0
print(json.dumps(dict(read_s=read_s, load_s=load_s, loadavg=os.getloadavg())), flush=True)
from student_pilot import _tower_native as N
orig = N.selected_layers
def timed(*a, **k):
    t = time.monotonic(); r = orig(*a, **k)
    print(json.dumps(dict(aggregator_s=time.monotonic()-t, loadavg=os.getloadavg())), flush=True); return r
N.selected_layers = timed
head = tower.module.depth_head.forward
def timed_head(*a, **k):
    t = time.monotonic(); r = head(*a, **k)
    print(json.dumps(dict(head_chunk_s=time.monotonic()-t)), flush=True); return r
tower.module.depth_head.forward = timed_head
t0 = time.monotonic(); state = tower.run(batch); run_s = time.monotonic()-t0
import numpy as np
print(json.dumps(dict(threads=threads, frames=len(images), hw=[images[0].height, images[0].width], read_s=read_s,
    load_s=load_s, run_s=run_s, depth=list(np.asarray(state.depth_grid).shape),
    finite=bool(np.isfinite(state.depth_grid).all()), torch=torch.__version__,
    loadavg=os.getloadavg(), peak_rss_gb=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024**2)))
