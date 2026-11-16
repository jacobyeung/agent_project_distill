import json, os, numpy as np
G='/scratch/jjyeung/orch_n30/gt_build'
P={r['canonical']:r for r in json.load(open(G+'/work/cr/PILOT300_INPUTS.json'))}
bad=set(open('/tmp/gb2_bad.txt').read().split())
def ts(s): return float(os.path.basename(s).split('_')[1].rsplit('.',1)[0])
res=[]
for k,r in P.items():
    if not k.startswith('arkit'): continue
    c=k.split('/')[1]; st=f'{G}/stage/arkit/{c}/{c}_frames'
    names=sorted(open(f'{G}/work/arkit_lists/{c}/depth_list.txt').read().split(), key=ts)
    rows=np.loadtxt(st+'/lowres_wide.traj')
    for f,i in enumerate(r['grid']):
        if i>=len(names): continue
        t=ts(names[i]); dt=np.abs(rows[:,0]-t).min()
        res.append((dt, c in bad, c, f))
res.sort()
print('frames between 0.45 and 1.0 ms (dt, bad?, cap, frame):')
for x in res:
    if 0.000495<=x[0]<=0.003: print('%.6f'%(x[0]*1000), x[1:])
print('n >1ms', sum(x[0]>0.001 for x in res), 'good caps with frames >1ms', len({x[2] for x in res if x[0]>0.001 and not x[1]}))
