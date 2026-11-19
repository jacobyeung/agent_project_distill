R=/scratch/jjyeung/orch_n30
for L in sb_kbox3 sb_kbox2 sb_kbox; do [ -d $R/$L ] && { echo "--- $L"; cat $R/$L/STATUS.md 2>/dev/null | head -c 1500; echo; ls $R/$L/out 2>/dev/null | head -20; }; done
[ -f $R/sb_kbox3/out/REPORT.md ] && head -c 5000 $R/sb_kbox3/out/REPORT.md
/usr/bin/python3 - <<'PYEOF'
import json, os, hashlib, gzip, collections, glob
import numpy as np
R='/scratch/jjyeung/orch_n30'
cr=R+'/b04host3/b04_e2ehook/heads/selector/data/caps_raw'
def sha(p): return hashlib.sha256(open(p,'rb').read()).hexdigest()
# index geometry files by sha
idx={}
for root in ('/scratch/jjyeung/k1/run_convert_2','/scratch/jjyeung/k1/run_convert_1'):
    for d in sorted(os.listdir(root)):
        p=root+'/'+d+'/geometry.npz'
        if os.path.exists(p): idx[sha(p)]=p
print('geometry files indexed', len(idx))
def median_ratio(depth, confidence, own):
    d,c,v=(np.asarray(x,float) for x in (depth,confidence,own))
    f=c[np.isfinite(c)]
    sel=np.isfinite(c)&(c>np.percentile(f,50))&np.isfinite(d)&(d>0)&np.isfinite(v)&(v>0)
    return float(np.median(v[sel]/d[sel]))
rows=[]; where=collections.Counter()
for f in sorted(os.listdir(cr)):
    z=json.load(gzip.open(cr+'/'+f)); g=z['geometry_sha256']; p=idx.get(g)
    where[(os.path.basename(os.path.dirname(os.path.dirname(p))) if p else 'not in run_convert_1/2')]+=1
    # the run_convert_2 geometry of the same capture: via tower_sha256
    rows.append((z['capture'], z['scale'], g, z['tower_sha256'], z['candidates_sha256']))
print('table geometry found in', dict(where))
# map tower sha -> digest dir in run_tower_sam_2
tidx={}
for d in sorted(os.listdir('/scratch/jjyeung/k1/run_tower_sam_2')):
    p='/scratch/jjyeung/k1/run_tower_sam_2/'+d+'/tower.npz'
    if os.path.exists(p): tidx[sha(p)]=d
cidx={}
for d in sorted(os.listdir('/scratch/jjyeung/k1/run_convert_2')):
    p='/scratch/jjyeung/k1/run_convert_2/'+d+'/candidates.json'
    if os.path.exists(p): cidx[sha(p)]=d
out=[]; n_t=0; n_c=0
for cap, ts, g, tw, cs in rows:
    d=tidx.get(tw); n_t+= d is not None; dc=cidx.get(cs); n_c+= dc is not None
    if d is None: continue
    gp='/scratch/jjyeung/k1/run_convert_2/'+d+'/geometry.npz'; op='/scratch/jjyeung/k1/own_170235/native/probe/'+d+'/own.npz'
    if not (os.path.exists(gp) and os.path.exists(op)): continue
    gs=float(np.load(gp, allow_pickle=True)['scale']); t=np.load('/scratch/jjyeung/k1/run_tower_sam_2/'+d+'/tower.npz'); o=np.load(op)
    mr=median_ratio(t['depth_grid'], t['depth_conf_grid'], o['depth'])
    out.append((cap, ts, gs, mr, sha(gp)==g))
print('tables', len(rows), 'tower sha matched', n_t, 'candidates sha matched', n_c, 'with geometry+own', len(out))
a=np.array([(x[1],x[2],x[3]) for x in out])
print('table scale / convert_2 scale: median %.4f, share within 1e-4: %.3f' % (np.median(a[:,0]/a[:,1]), np.mean(np.abs(a[:,0]/a[:,1]-1)<1e-4)))
print('median_ratio(own_170235) / convert_2 scale: median %.4f, share within 1e-4: %.3f' % (np.median(a[:,2]/a[:,1]), np.mean(np.abs(a[:,2]/a[:,1]-1)<1e-4)))
print('median_ratio(own_170235) / table scale: median %.4f, share within 1e-4: %.3f' % (np.median(a[:,2]/a[:,0]), np.mean(np.abs(a[:,2]/a[:,0]-1)<1e-4)))
print('table geometry sha == convert_2 geometry sha:', sum(x[4] for x in out), 'of', len(out))
for x in out[:4]: print('  ', x[0], 'table %.4f convert_2 %.4f median_ratio %.4f' % x[1:4])
# what do run_convert_1 geometry scales look like for the same digests
r1=[]
for cap, ts, g, tw, cs in rows[:40]:
    d=tidx.get(tw)
    p='/scratch/jjyeung/k1/run_convert_1/'+str(d)+'/geometry.npz'
    if d and os.path.exists(p): r1.append((ts, float(np.load(p, allow_pickle=True)['scale'])))
if r1:
    b=np.array(r1); print('table scale / convert_1 scale (first 40): median %.4f share within 1e-4 %.3f' % (np.median(b[:,0]/b[:,1]), np.mean(np.abs(b[:,0]/b[:,1]-1)<1e-4)))
for f in ('/scratch/jjyeung/k1/run_convert_2.preflight.json','/scratch/jjyeung/k1/run_convert_1.preflight.json'):
    try: print(f, open(f).read()[:700])
    except Exception as e: print(f, e)
print(open('/scratch/jjyeung/k1/CONVERT2.log').read()[:600])
# e3gd: which geometry does GD_reviewed use
import re
h=open(R+'/k1_ops3/work/e3gd/harness.py').read()
for m in re.finditer(r'.{0,120}(run_convert|own_170235|geometry\.npz|GD_reviewed).{0,160}', h): print('e3gd harness:', m.group(0).replace('\n',' ')[:300])
PYEOF
