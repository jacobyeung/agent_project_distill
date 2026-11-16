import json, os, glob, numpy as np, sys
G='/scratch/jjyeung/orch_n30/gt_build'
P={r['canonical']:r for r in json.load(open(G+'/work/cr/PILOT300_INPUTS.json'))}
def ts(s): return float(os.path.basename(s).split('_')[1].rsplit('.',1)[0])
for c in sys.argv[1:]:
    st=f'{G}/stage/arkit/{c}/{c}_frames'
    names=open(f'{G}/work/arkit_lists/{c}/depth_list.txt').read().split()
    s1=sorted(names,key=ts); s2=sorted(names)
    t=np.array([ts(n) for n in s1]); rows=np.loadtxt(st+'/lowres_wide.traj')
    pcs=sorted(glob.glob(st+'/lowres_wide_intrinsics/*.pincam'))
    grid=P['arkitscenes/'+c]['grid']
    gaps=np.diff(t)
    print(c,'n',len(t),'dup ts',len(t)-len(set(t)),'namesort==tssort',s1==s2,'gap max %.3f min %.3f'%(gaps.max(),gaps.min()),'traj dup',len(rows)-len(set(rows[:,0])),'traj sorted',bool((np.diff(rows[:,0])>0).all()),'npincam',len(pcs),'grid max',max(grid))
    # first/last
    print('   t0 %.3f tN %.3f traj0 %.5f trajN %.5f'%(t[0],t[-1],rows[0,0],rows[-1,0]), 'expected 10Hz slots', round((t[-1]-t[0])/0.1)+1)
    big=np.nonzero(gaps>0.15)[0]; print('   gaps>0.15 at', big[:10], gaps[big][:10])
