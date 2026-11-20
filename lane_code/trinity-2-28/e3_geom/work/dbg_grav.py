import sys,json,numpy as np
sys_path_fix=__import__('sys').path.insert(0,'/scratch/jjyeung/orch_n30/e3_geom/work/harness')
sys.path.insert(0,'/scratch/jjyeung/orch_cd/leg_s1_tree/work/tree_s1_admissionfix_168872')
from student_pilot import camera_targets as ct
m=json.load(open('/scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json'))
import importlib.util as iu; sp=iu.spec_from_file_location('e3h','/scratch/jjyeung/orch_n30/e3_geom/work/harness/harness.py'); H=iu.module_from_spec(sp); sp.loader.exec_module(H)
cs,cache,inv=H.inventory()
for c in [x for x in cs][:8]:
    try: gt,tower,hw=H.load_capture(c,cache[H.digest(c)],False)
    except Exception as e: print('load',e); continue
    raw=tower['raw_pose'][tower['anchor_slots']]
    Rt=np.array([ct.rotation_from_xyzw(p[3:7]).T for p in raw]); Rn=np.array([ct.rotation_from_xyzw(p[3:7]) for p in raw])
    g=H.gravities(tower,gt)
    v=gt['valid'].astype(bool); up_gt_cam=gt['c2w'][v,:3,:3].transpose(0,2,1)@np.array([0,0,1.])
    print(c['canonical'],hw,'G1',np.round(g['G1'],2),'GO',np.round(g['GO'],2),'cam0 up(gt, cam coords)',np.round(up_gt_cam[0],2),'up.(-y) mean',np.round(np.mean(-up_gt_cam[:,1]),2),'x',np.round(np.mean(up_gt_cam[:,0]),2))
