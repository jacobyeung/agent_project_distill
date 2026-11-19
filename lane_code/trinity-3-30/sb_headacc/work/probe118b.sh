cd /scratch/jjyeung/k1
PY=/scratch/jjyeung/envs/planner_local_v1/bin/python; [ -x $PY ] || PY=python3
$PY - <<'PYEOF'
import json, os, glob, sys
c='/scratch/jjyeung/k1/run_convert_2/01949c4249271126'
d=json.load(open(c+'/candidates.json'))
print('candidates.json keys', list(d.keys())[:12])
ph=d.get('phrases'); print('phrases', len(ph) if ph else None, (ph[:40] if isinstance(ph,list) else list(ph)[:40]))
fr=d.get('frames'); 
if fr:
    k0=sorted(fr.keys())[0]; print('frames', len(fr), 'frame0 keys', list(fr[k0].keys())[:8])
    p0=fr[k0].get('phrases',{}); kk=list(p0.keys())[:2]
    for k in kk: print('  ', k, {a:(b if not isinstance(b,list) else len(b)) for a,b in p0[k].items()})
for k in d:
    if k not in ('frames','phrases'): print(' ', k, str(d[k])[:200])
try:
    import numpy as np
    for f in ('/scratch/jjyeung/k1/run_tower_sam_2/01949c4249271126/tower.npz', c+'/geometry.npz'):
        z=np.load(f, allow_pickle=True); print(f.split('/')[-1], {k: z[k].shape for k in z.files})
except Exception as e: print('np', e)
m=json.load(open('/scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json'))
print('manifest type', type(m).__name__, list(m.keys())[:10] if isinstance(m,dict) else len(m))
caps=m.get('captures') if isinstance(m,dict) else m
one=caps[0] if isinstance(caps,list) else list(caps.values())[0]
print('capture keys', list(one.keys())[:30]); 
for k,v in one.items():
    if isinstance(v,list): print('   ',k,'list',len(v), str(v[:2])[:160])
    elif not isinstance(v,dict): print('   ',k,str(v)[:120])
    else: print('   ',k,'dict',list(v.keys())[:12])
PYEOF
echo "## b11 code/out"; ls /scratch/jjyeung/orch_n30/b11_presence/code /scratch/jjyeung/orch_n30/b11_presence/out/prep /scratch/jjyeung/orch_n30/b11_presence/out/analysis 2>&1 | head -50
echo "## selector data/work"; ls /scratch/jjyeung/orch_n30/b04host3/b04_e2ehook/heads/selector/data /scratch/jjyeung/orch_n30/b04host3/b04_e2ehook/heads/selector/work 2>&1 | head -40
echo "## lift_price variants"; grep -n "^def \|VARIANTS\|variants *=" /scratch/jjyeung/orch_n30/b04host3/lift_price/harness/lift_price.py | head -40
echo "## AGG_TRAIN_v2"; head -30 /scratch/jjyeung/orch_n30/b04host3/lift_price/harness/AGG_TRAIN_v2.txt
echo "## gt rasters"; ls /scratch/jjyeung/orch_n30/gt_rasters 2>&1 | head; ls /scratch/jjyeung/orch_n30/gt_build2 2>&1 | head
echo "## sb_f64"; ls /scratch/jjyeung/orch_n30/sb_f64 /scratch/jjyeung/orch_n30/sb_roomkit 2>&1 | head -30
