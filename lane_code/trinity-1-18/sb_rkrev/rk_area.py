"""Area of the reviewer's own CPU forward via the deployed tree and original converter."""
import importlib.util, json, sys, hashlib
from pathlib import Path
import numpy as np
T = '/scratch/jjyeung/orch_cd/leg_s1_tree/work/tree_s1_admissionfix_168872'; sys.path.insert(0, T)
from student_pilot import camera_targets as ct
from student_pilot.ground_profiles import load_geometry
from student_pilot.scene_state import FrameMap
from trace_format import room_v314 as room
s = importlib.util.spec_from_file_location('kc', '/scratch/jjyeung/orch_n30/geo_k1/k1towers/k1_convert.py'); kc = importlib.util.module_from_spec(s); s.loader.exec_module(kc)
H = Path(__file__).resolve().parent; p = H / 'out/forward/scannetpp__067e2e4e61/pred.npz'
with np.load(p) as z: d = {k: z[k] for k in z.files}
sl = d['anchor_slots'].astype(int); a = [int(x) for x in d['frame_indices'][sl]]
C, _ = kc.native_cameras(d['c2w'][sl], ct)
g = H / 'out/forward_geom.npz'
kc.write(g, a, d['intrinsics'][sl].copy(), kc.canvas_affine(d['source_hw']), C, d['depth_grid64'][sl].astype(np.float64), np.linspace(0, 1000, 51), 1.0, load_geometry, FrameMap)
geo = load_geometry(g, FrameMap(tuple(a)), 'tower_scaled')
area = float(room.parse_response(room.format_result(room.from_points(**room.sample(geo, 'predicted'))))['area_m2'])
with np.load('/scratch/jjyeung/orch_n30/sb_roomkit/out/s1/k1_64/scannetpp__067e2e4e61/pred.npz') as z: k = {x: z[x] for x in z.files}
kg = k['depth_grid'][k['item_slots'].astype(int)]; mg = d['depth_grid64'][sl]; ok = (kg > 0) & (mg > 0)
r = dict(area_m2=area, stored_gpu=14.73, rel_err=abs(area / 14.73 - 1), within_5pct=abs(area / 14.73 - 1) <= .05,
         seconds=json.load(open(p.parent / 'DONE.json'))['seconds'], pred_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
         median_abs_rel_depth_vs_kit_cpu=float(np.median(np.abs(mg[ok] / kg[ok] - 1))))
print(json.dumps(r, indent=1)); json.dump(r, open(H / 'out/RK_FORWARD.json', 'w'), indent=1)
