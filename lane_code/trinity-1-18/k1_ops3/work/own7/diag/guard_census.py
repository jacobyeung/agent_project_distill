"""Analysis only: per-capture sealed vs reviewed (C8r validate_up_convention) gravity guard on own gravity. usage: guard_census.py OWN_ROOT OUT.json"""
import json, sys, importlib.util
from pathlib import Path
import numpy as np
KIT = Path('/scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a')
sys.path[:0] = [str(KIT / 'work'), str(KIT / 'native_kit')]
import bindings as B
B.geometry.install_tree()
from student_pilot.tower_read import TowerState
from student_pilot.camera_targets import to_gravity_reference_frame
from student_pilot.geometry_profiles import GeometryError
spec = importlib.util.spec_from_file_location('gg', '/scratch/jjyeung/orch_n30/k1_ops3/work/partb/build7/reference/sj/orch_cd/evalx/work/milestone/native/out2/gravity_guard.py')
gg = importlib.util.module_from_spec(spec); spec.loader.exec_module(gg)
m = json.load(open('/scratch/jjyeung/orch_n30/k1_ops3/work/manifest_v2/a40fbc19.json'))
own, tower = Path(sys.argv[1]), Path('/scratch/jjyeung/k1/run_tower_sam_2')
rows = {}
for c in m['captures']:
    d = B.digest(c['canonical'])[:16]
    if not (own / d / 'own.npz').exists(): continue
    st = TowerState.from_npz(tower / d / 'tower.npz')
    with np.load(own / d / 'own.npz', allow_pickle=False) as z: g = z['gravity']
    R, t, fov = to_gravity_reference_frame(st.raw_pose9[st.anchor_slots], g)
    try: gg.validate_up_convention(R); rev = False
    except GeometryError: rev = True
    plane = np.linalg.norm(R[:, 2, :2], axis=1); margin = -R[:, 2, 1]
    rows[c['canonical']] = dict(reviewed_refused=rev, ref_plane=float(plane[0]), ref_margin=float(margin[0]), neg_margin_frames=int((margin <= 0).sum()))
json.dump(rows, open(sys.argv[2], 'w'), indent=1, sort_keys=True)
print(len(rows), 'captures; reviewed refused', sum(r['reviewed_refused'] for r in rows.values()), '; ref_margin<=0', sum(r['ref_margin'] <= 0 for r in rows.values()))
for k, r in rows.items(): print(k, r)
