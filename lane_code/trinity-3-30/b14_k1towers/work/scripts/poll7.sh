G=/scratch/jjyeung/orch_n30/geo_k1; cd $G; date -u
cat > $G/k1towers/pose_check.py <<'PYEOF'
"""Diagnostic: relative anchor rotation error of G3T and each joint tower against K1 GT, with and without an
OpenCV/OpenGL flip, to rule out a convention error. Usage: python pose_check.py MANIFEST TOWERS ROOT... CAPTURE"""
import hashlib, json, sys
from pathlib import Path
import numpy as np
man, towers, *roots, cap = sys.argv[1:]
c = next(c for c in json.loads(Path(man).read_text())['captures'] if c['canonical'] == cap)
key = hashlib.sha256(json.dumps(c, sort_keys=True, allow_nan=False).encode()).hexdigest()
g = np.load(c['gt']['path']); valid = g['valid'].astype(bool)
def q2R(q):
    x, y, z, w = np.asarray(q, float) / np.linalg.norm(q)
    return np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)], [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)], [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])
def err(Rp, Rg, F=np.eye(3)):
    i0 = 0
    rp = np.einsum('ji,njk->nik', Rp[i0], Rp); rg = np.einsum('ji,njk->nik', Rg[i0], Rg); rg = F @ rg @ F
    return float(np.median(np.degrees(np.arccos(np.clip((np.einsum('nij,nij->n', rp, rg) - 1) / 2, -1, 1)))[1:]))
F = np.diag([1., -1., -1.])
for p in Path(towers).glob('*/PHASE_COMPLETE.json'):
    if json.loads(p.read_text())['capture_sha256'] == key:
        t = np.load(p.parent / 'tower.npz'); raw = t['raw_pose'][t['anchor_slots']]
        Rg3 = np.array([q2R(r[3:7]).T for r in raw])
        print('g3t', err(Rg3[valid], g['c2w'][valid, :3, :3]), 'flip', err(Rg3[valid], g['c2w'][valid, :3, :3], F))
for root in roots:
    for d in sorted(Path(root).glob('*/' + key[:16])):
        if not (d / 'pred.npz').is_file(): continue
        z = np.load(d / 'pred.npz')
        if 'c2w' not in z.files: continue
        pos = z['smoke_anchor_pos'].astype(int) if 'smoke_anchor_pos' in z.files else np.arange(32)
        v = valid[pos]; Rp = z['c2w'][z['anchor_slots'].astype(int)][:, :3, :3][v]; Rg = g['c2w'][pos][v][:, :3, :3]
        print(d.parent.name, err(Rp, Rg), 'flip', err(Rp, Rg, F), 'det', float(np.linalg.det(Rp[0])))
PYEOF
M=/scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json; T=/scratch/jjyeung/k1/run_tower_sam_2
/scratch/jjyeung/envs/planner_local_v1/bin/python -B k1towers/pose_check.py $M $T pred_cpu smoke scannet/scene0201_02
for f in logs/ref_*.log; do tail -n1 $f; done; ls harness/out_ref/captures | wc -l
