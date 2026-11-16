"""r4 heading: rotate a near-nadir frame's basis about gravity; served fields must be invariant, refused fields must vary with checks disabled."""
import sys, json, dataclasses, re
TREE, OUT = sys.argv[1], sys.argv[2]
sys.path[:0] = [TREE, '/scratch/jjyeung/orch_n30/review_contracts2/work/rr/work/tests_r4']
import numpy as np
from pathlib import Path
from scipy.spatial.transform import Rotation as Rot
from fixtures_contracts import fixture, session, response
from trace_format.contracts import contract_epoch
from student_pilot.geometry_profiles import ProfileGeometry
from student_pilot.carrier_c1_routing import OwnGeometry
from student_pilot.carrier_c1_decode import respond
from student_pilot.p3_printed_calculator import PrintedPointRegistry
TMP=Path('/scratch/jjyeung/orch_n30/review_contracts2/work/tmp/r4head')
BASE = np.array([[1., 0, 0], [0, 0, 1], [0, -1, 0]])
def cam(pitch=0., roll=0., yaw=0.):
    return (Rot.from_euler('z', yaw, degrees=True).as_matrix() @ BASE
            @ Rot.from_euler('x', -pitch, degrees=True).as_matrix() @ Rot.from_euler('z', roll, degrees=True).as_matrix())
HEAD = ['<pose frame=1>','<pose frame=3>','<pose frame=6>','<move from=1 to=4>','<move from=2 to=5>','<move from=4 to=1>',
        '<move from=6 to=7>','<move from=7 to=6>','<move from=2 to=6>','<turn from=1 to=5>','<turn from=5 to=1>','<turn from=2 to=5>',
        '<turn from=6 to=7>','<turn from=7 to=6>','<turn from=2 to=7>',
        '<depth_at frame=1 pts=[[500,500]]>','<depth_at frame=2 pts=[[500,500],[100,900]]>','<depth_at frame=6 pts=[[500,500]]>']
GROUND = ['<ground obj="chair" mode="box">','<ground obj="table" mode="box">','<gap a="chair" b="table" rule="box_grid_5cm">',
          '<gap camera="3" b="chair" b="table" rule="box_grid_5cm">','<gap camera="6" b="chair" rule="box_grid_5cm">',
          '<ground obj="chair">','<ground obj="table">','<ground obj="chair" mode="instances">','<ground mode="room">']
JIT=np.random.default_rng(7).normal(0,0.013,(32,3))
def scenario(nadir_frame, yaw, tilt=None):
    c, make = fixture('landscape'); C = c.camera_to_world.copy()
    noise = np.eye(3) if tilt is None else (Rot.from_euler('z', tilt, degrees=True)*Rot.from_euler('x', 3, degrees=True)*Rot.from_euler('z', -tilt, degrees=True)).as_matrix()
    for i in range(32):
        R = cam(-88, 0, yaw) if i == nadir_frame-1 else cam(0, 0, 3*i)
        C[i,:3,:3] = noise @ R
        C[i,:3,3] = noise @ (C[i,:3,3] + JIT[i])
    c2 = dataclasses.replace(c, camera_to_world=C)
    geo = ProfileGeometry(c2, make().depth_grid)
    out = {}
    s = session(geo, TMP/f'{nadir_frame}_{yaw}_{tilt}_{np.random.randint(1e9)}')
    for cl in GROUND: out[cl] = response(s, cl)
    p = np.zeros((32,9)); p[:,6]=1; p[:,7:9]=[.9,1.1]
    R1, c1 = C[0,:3,:3], C[0,:3,3]
    for k in range(1,32):
        Rk1 = R1.T @ C[k,:3,:3]; ck = R1.T @ (C[k,:3,3]-c1)
        p[k,:3] = -Rk1.T @ ck; p[k,3:7] = Rot.from_matrix(Rk1.T).as_quat()
    own = OwnGeometry(p, R1.T @ np.array([0,0,1.]), lambda k, pts: np.full(len(pts), 2.0))
    for cl in HEAD: out['HEAD '+cl] = respond(cl, PrintedPointRegistry(), own)[0]
    return out
HU = re.compile(r'heading unavailable(?: \(frames? [\d,]+\))?')
def toks(s):
    s = re.sub(r'\(0 = \+x; positive \+x toward -z about \+y\)', '', s)
    s = HU.sub(' H ', s)
    return re.findall(r'H|[+-]?\d+\.\d+|[+-]?\d+(?= deg)', s)
res = {}
YAWS = (0, 40, 130, 250)
for nadir_frame in (1, 6):
    runs = {}
    for thr, tag in ((0.3, 'default'), (1e-9, 'disabled')):
        with contract_epoch(True, heading_plane_min=thr):
            runs[tag] = {y: scenario(nadir_frame, y) for y in YAWS}
    rep = {}
    for k in runs['default'][0]:
        d = [runs['default'][y][k] for y in YAWS]; x = [runs['disabled'][y][k] for y in YAWS]
        td = [toks(v) for v in d]; tx = [toks(v) for v in x]
        served_same = len(set(map(tuple, [[t for t in tt if t != 'H'] for tt in td]))) == 1
        info = dict(default=d[0], served_identical=served_same, text_identical=len(set(d)) == 1)
        if not served_same:
            info['default_all'] = d
        if any('H' in t for t in td):
            # refused positions must vary when checks are disabled
            n = len(td[0])
            if all(len(t) == n for t in tx):
                pos = [i for i, t in enumerate(td[0]) if t == 'H']
                info['refused_vary'] = {i: sorted(set(t[i] for t in tx)) for i in pos}
                info['refused_all_vary'] = all(len(v) > 1 for v in info['refused_vary'].values())
                served_pos = [i for i, t in enumerate(td[0]) if t != 'H']
                info['served_match_disabled'] = all(td[j][i] == tx[j][i] for j in range(len(YAWS)) for i in served_pos)
            else:
                info['align'] = 'token counts differ'; info['disabled_all'] = x
        else:
            info['disabled_identical_to_default'] = d == x
        rep[k] = info
    res[f'nadir_frame_{nadir_frame}'] = rep
json.dump(res, open(OUT, 'w'), indent=1)
for sc, rep in res.items():
    print('=====', sc)
    for k, v in rep.items():
        flag = ('SERVED-SAME' if v['served_identical'] else 'SERVED-VARY')
        extra = '' if 'refused_vary' not in v else f" refusedVary={v['refused_all_vary']} servedEqDisabled={v['served_match_disabled']}"
        if 'align' in v: extra = ' ALIGN?'
        print(f'  {flag:12s}{extra} {k} -> {v["default"].replace(chr(10)," | ")[:170]}')
        if not v['served_identical']: print('      all:', [z.replace(chr(10),' | ')[:120] for z in v['default_all']])

TILTS=(0,90,180,270)
tilt_res={}
num=lambda t:[float(x) for x in t if x!='H']
for nadir_frame in (1,6):
    with contract_epoch(True, heading_plane_min=1e-9):
        runs={t: scenario(nadir_frame, 0, t) for t in TILTS}
    with contract_epoch(True):
        dflt=scenario(nadir_frame, 0, 0)
    rep={}
    for k in runs[0]:
        tx=[toks(runs[t][k]) for t in TILTS]; td=toks(dflt[k])
        if any(len(t)!=len(tx[0]) for t in tx) or len(td)!=len(tx[0]):
            rep[k]=dict(align=False, default=dflt[k], disabled=[runs[t][k] for t in TILTS]); continue
        spread=[max(float(t[i]) for t in tx)-min(float(t[i]) for t in tx) for i in range(len(td))]
        rep[k]=dict(default=dflt[k], refused_spread=[round(spread[i],3) for i in range(len(td)) if td[i]=='H'],
                    served_spread=[round(spread[i],3) for i in range(len(td)) if td[i]!='H'])
    tilt_res[f'nadir_frame_{nadir_frame}']=rep
json.dump(dict(yaw=res,tilt=tilt_res), open(OUT, 'w'), indent=1)
for sc, rep in tilt_res.items():
    print('===== TILT', sc)
    for k,v in rep.items():
        if 'refused_spread' in v: print(f"  refused={v['refused_spread']} servedmax={max(v['served_spread'] or [0])} {k} -> {v['default'].replace(chr(10),' | ')[:140]}")
        else: print('  ALIGN?', k, v['default'][:100], v['disabled'][0][:100])
