import json, os, numpy as np
G='/scratch/jjyeung/orch_n30/gt_build'
P={r['canonical']:r for r in json.load(open(G+'/work/cr/PILOT300_INPUTS.json'))}
rows=[json.loads(l) for l in open('/scratch/jjyeung/orch_n30/gt_build2/logs/VARIANT_R1.jsonl')][1:]
def ts(s): return float(s.split('_')[1].rsplit('.',1)[0])
for r in rows:
    c=r['c']; names=sorted(open(f'{G}/work/arkit_lists/{c}/depth_list.txt').read().split(), key=ts)
    t=np.array([ts(n) for n in names]); g=P['arkitscenes/'+c]['grid']
    out=[]
    for per in (0.1, np.median(np.diff(t)), (t[-1]-t[0])/(len(t)-1)):
        sel=[int(np.argmin(np.abs(t-(t[0]+per*s)))) for s in g]
        out.append(sum(a!=b for a,b in zip(sel,g) if b<len(t)))
    if any(out) or not r['match']: print(c, r['match'], 'grid slots remapped (0.1, median, mean period):', out)
