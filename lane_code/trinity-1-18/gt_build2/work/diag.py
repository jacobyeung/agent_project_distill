import json, os, sys, glob, numpy as np
G='/scratch/jjyeung/orch_n30/gt_build'
P={r['canonical']:r for r in json.load(open(G+'/work/cr/PILOT300_INPUTS.json'))}
def ts(s): return float(os.path.basename(s).split('_')[1].rsplit('.',1)[0])
for c in sys.argv[1:]:
    st=f'{G}/stage/arkit/{c}/{c}_frames'
    names=sorted(open(f'{G}/work/arkit_lists/{c}/depth_list.txt').read().split(), key=ts)
    rows=np.loadtxt(st+'/lowres_wide.traj'); grid=P['arkitscenes/'+c]['grid']
    ann=json.load(open(f'{G}/stage/arkit/{c}/{c}_3dod_annotation.json'))['data']
    out=[]
    for f,i in enumerate(grid):
        t=ts(names[i]); dt=np.abs(rows[:,0]-t); j=dt.argmin()
        out.append(f'{f}:{dt[j]*1000:.2f}')
    print(c, 'ndepth',len(names),'ntraj',len(rows),'nbox',len(ann), 'traj_dt_med',np.median(np.diff(rows[:,0])))
    print('  dt_ms', ' '.join(x for x in out if float(x.split(':')[1])>0.3))
