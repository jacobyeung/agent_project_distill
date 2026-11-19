"""CPU conversion and protocol audit; no tower forward pass or GPU access."""
import hashlib
import importlib.util
import json
import math
import os
import sys
import types
from pathlib import Path
import numpy as np

W = Path(__file__).resolve().parent
R = Path('/scratch/jjyeung')
T = R/'orch_cd/leg_s1_tree/work/tree_s1_admissionfix_168872'
K = R/'orch_n30/geo_k1'
sys.path.insert(0, str(T))
hashes = {}
def sha(p):
    p = Path(p)
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    hashes[str(p)] = h
    return h
def module(name, p):
    sha(p)
    spec = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m
kc = module('kc', K/'k1towers/k1_convert.py')
ki = module('ki', K/'k1towers/k1_infer.py')
sc = module('sc', W/'evidence/score_room_pricing.py')
from student_pilot import camera_targets as ct
from student_pilot.ground_profiles import load_geometry
from student_pilot.scene_state import FrameMap
from trace_format import room_v314 as room
for m in (ct, room, sys.modules[load_geometry.__module__], sys.modules[FrameMap.__module__]):
    sha(m.__file__)
mp = R/'orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json'
sha(mp); manifest = json.loads(mp.read_text())
index = ki.tower_index(R/'k1/run_tower_sam_2')
results = []
for c in manifest['captures']:
    if c['canonical'] not in ('scannetpp/067e2e4e61', 'scannetpp/036bce3393'):
        continue
    key = ki.digest(c)
    paths, frame_hashes, frames, bound_slots = ki.bind(c,index[key])
    sha(index[key]/'PHASE_COMPLETE.json'); sha(index[key]/'tower.npz')
    hashes.update(dict(zip(paths,frame_hashes)))
    print('S1_BIND',c['canonical'],'dense_frames',len(paths),'anchor_slots',len(bound_slots),flush=True)
    p = K/'pred_gpu/da3'/key[:16]/'pred.npz'
    sha(p)
    with np.load(p, allow_pickle=False) as z:
        pred = {k:z[k] for k in z.files}
    slots = pred['anchor_slots'].astype(int)
    anchors = [int(x) for x in pred['frame_indices'][slots]]
    C, up = kc.native_cameras(pred['c2w'][slots], ct)
    dest = W/(c['canonical'].replace('/','__')+'.npz')
    kc.write(dest, anchors, pred['intrinsics'][slots].copy(), kc.canvas_affine(pred['source_hw']), C,
             pred['depth_grid64'][slots].astype(np.float64), np.linspace(0,1000,51), 1.0, load_geometry, FrameMap)
    geo = load_geometry(dest, FrameMap(tuple(anchors)), 'tower_scaled')
    area = room.parse_response(room.format_result(room.from_points(**room.sample(geo,'predicted'))))['area_m2']
    stored = K/'geom/da3_native'/(c['canonical'].replace('/','__')+'.npz')
    sha(stored)
    sg = load_geometry(stored, FrameMap(tuple(anchors)), 'tower_scaled')
    sa = room.parse_response(room.format_result(room.from_points(**room.sample(sg,'predicted'))))['area_m2']
    print('CONVERSION',c['canonical'],'rebuilt',area,'stored',sa,'scale_counts',geo.depth_scale_count,geo.pose_scale_count,flush=True)
    results.append((dest,anchors,area))

# Test receipt validation using workspace fixtures, never modifying another lane.
fixture = W/'resume_fixture'; fixture.mkdir(exist_ok=True)
predfile = fixture/'pred.npz'; predfile.write_bytes(b'original')
h = sha(predfile)
(fixture/'DONE.json').write_text(json.dumps({'pred_sha256':h,'input_sha256':{str(predfile):h}}))
print('RESUME original',ki.done_ok(fixture),flush=True)
predfile.write_bytes(b'changed')
print('RESUME changed',ki.done_ok(fixture),'(False means the existing main loop reruns and overwrites, rather than refusing)',flush=True)

# Exercise the actual gate with a backend stub; no torch or CUDA call occurs.
pkg = types.ModuleType('geo_bakeoff'); back = types.ModuleType('geo_bakeoff.backends'); pkg.backends=back
sys.modules['geo_bakeoff']=pkg; sys.modules['geo_bakeoff.backends']=back
go = W/'gate_note.txt'; go.write_text('GO audit fixture\n')
for name, note, device, visible in [('CPU',None,'cpu','0,1'),('no_GO',None,'cuda','0'),
                                  ('multi_GPU',str(go),'cuda','0,1'),('single_GPU',str(go),'cuda','0')]:
    ki.install_device_gate(note); os.environ['CUDA_VISIBLE_DEVICES']=visible
    try:
        back.validate_device(device); answer='accepted'
    except PermissionError:
        answer='refused'
    print('GATE',name,answer,flush=True)
os.environ['CUDA_VISIBLE_DEVICES']=''

dp = W/'evidence/direct_m200_room134.json'; vp = W/'evidence/K1_RULE_VARIANTS.json'
sha(dp); sha(vp)
direct = json.loads(dp.read_text())['rows']; variants = json.loads(vp.read_text())
d = np.array([r['direct_mra'] for r in direct if r['set']=='R0-dev'])
k = np.array([sc.mra(r['R0'],r['gt']) for r in variants['rows'] if r['split']=='train' and r['dataset']=='scannetpp'])
half = 1.96*math.sqrt((float(np.var(d,ddof=1))+float(np.var(k,ddof=1)))/len(d))*100
print('STAT direct_n',len(d),'direct_mean',100*d.mean(),'direct_SD',100*d.std(ddof=1),
      'K1_train_scannetpp_n',len(k),'head_mean',100*k.mean(),'head_SD',100*k.std(ddof=1),
      'independent_fixed_variance_normal_halfwidth',half,flush=True)
print('COST nominal_forward_GPU_hours',98*(5+14)/3600,'devS1_extra',36*5/3600,flush=True)
print('K1 variant heldout nonnull',sum(any(r.get(v) is not None for v in ('T05','T10','T20','C4','C5','C6','C8'))
      for r in variants['rows'] if r['split']=='heldout'), 'reproduction', variants['summary']['rebuilt_equals_stored'],flush=True)
echo = [dict(id=r['id'],arm='echo',area_m2=r['direct']/(sc.FT2 if r['unit']=='ft2' else 1),refusal=None) for r in direct]
table = sc.score(direct, echo, 'MISSING_PRIMARY',5)
print('SCORER missing primary raises',False,'decision present','decision' in table,flush=True)
print('BASELINE per-set calls', {s:sum(r['calls'] for r in direct if r['set']==s) for s in ('R0-dev','dev-S1')},flush=True)
print('BASELINE per-set MRA', {s:100*np.mean([r['direct_mra'] for r in direct if r['set']==s]) for s in ('R0-dev','dev-S1')},flush=True)
(W/'CPU_INPUT_SHA256.txt').write_text('\n'.join(f'{h}  {p}' for p,h in sorted(hashes.items()))+'\n')

# Import harness last: its global audit hook forbids writes to this review workspace.
sys.path.insert(0,str(K/'harness'))
import harness as H
for dest, anchors, expected in results:
    geo = load_geometry(dest,FrameMap(tuple(anchors)),'tower_scaled')
    print('HARNESS',dest.name,H.areas(geo,'predicted')['R0'],'expected',expected,flush=True)
try:
    (W/'harness_write_probe.txt').write_text('probe')
except PermissionError as exc:
    print('HARNESS external lane write fails',str(exc),flush=True)
