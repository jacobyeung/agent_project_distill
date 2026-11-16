import json,sys,collections
import numpy as np
sys.path.insert(0,'/scratch/jjyeung/orch_n30/native_r4/builds/04_vsti_d/code')
import report as R
from scorer import TYPES,GROUPS,collapse
L='/scratch/jjyeung/orch_n30/native_r4'
d=json.load(open(L+'/work/ret4/report_v1d/report/REPORT.json'))
p=d['primary'];print('primary',p['score'],p['scene_interval'],p['room_interval'] if 'room_interval' in p else '')
print('subtasks',{k:(round(v['score']*100,2) if v.get('score') is not None else None) for k,v in d['subtasks'].items()})
import tarfile
t=tarfile.open(L+'/work/ret4/result.tar.gz')
truth=json.load(t.extractfile('i/SCORES.json'))
rows=[json.loads(l) for l in t.extractfile('j0/items.jsonl').read().decode().splitlines()]
nat={r['key']:r for r in rows if r['arm']=='native'}
print('native items',len(nat))
for name in ('f17','p1m200'):
    c={'q'+str(json.loads(l)['example_id']):json.loads(l) for l in open(f'{L}/in/comparators/{name}.per_question_scores.jsonl')}
    keys=[k for k in nat if k in c]
    per={t_:100*np.mean([c[k]['official_fuzzy_score'] for k in keys if nat[k]['question_type']==t_]) for t_ in TYPES}
    prim=collapse({t_:per[t_]/100 for t_ in TYPES})['primary']*100
    vals=[dict(score=nat[k]['score']-c[k]['official_fuzzy_score'],question_type=nat[k]['question_type'],scene=truth[k]['scene']) for k in keys]
    # paired primary diff bootstrap over scenes
    scenes=sorted({v['scene'] for v in vals});idx={s:i for i,s in enumerate(scenes)}
    S=np.zeros((len(scenes),len(TYPES)));N=np.zeros_like(S)
    for v in vals:S[idx[v['scene']],TYPES.index(v['question_type'])]+=v['score'];N[idx[v['scene']],TYPES.index(v['question_type'])]+=1
    rng=np.random.default_rng(544);w=rng.multinomial(len(scenes),[1/len(scenes)]*len(scenes),size=2000)
    num=w@S;den=w@N;ok=np.all(den>0,axis=1);m=num[ok]/den[ok]
    boot=np.mean([np.mean(m[:,[TYPES.index(x) for x in ts]],axis=1) for ts in GROUPS.values()],axis=0)*100
    print(name,len(keys),'primary',round(prim,2),'per type',{k:round(v,1) for k,v in per.items()},'diff CI',np.quantile(boot,[.025,.975]).round(2),'valid',int(ok.sum()))
