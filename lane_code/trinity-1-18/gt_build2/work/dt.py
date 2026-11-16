import json, os, sys, numpy as np
G='/scratch/jjyeung/orch_n30/gt_build'
P={r['canonical']:r for r in json.load(open(G+'/work/cr/PILOT300_INPUTS.json'))}
def ts(s): return float(os.path.basename(s).split('_')[1].rsplit('.',1)[0])
lo,hi=float(sys.argv[1]),float(sys.argv[2])
for c in sys.argv[3:]:
    st=f'{G}/stage/arkit/{c}/{c}_frames'
    names=sorted(open(f'{G}/work/arkit_lists/{c}/depth_list.txt').read().split(), key=ts)
    raw=[l.split()[0] for l in open(st+'/lowres_wide.traj')]
    rows=np.loadtxt(st+'/lowres_wide.traj'); grid=P['arkitscenes/'+c]['grid']
    for f,i in enumerate(grid):
        t=ts(names[i]); dt=np.abs(rows[:,0]-t); j=dt.argmin()
        if lo<=dt[j]*1000<=hi: print(c,f,names[i],raw[j],repr(dt[j]), dt[j]<=0.0005)
