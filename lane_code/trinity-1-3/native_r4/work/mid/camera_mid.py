import json,sys
import numpy as np
sys.path.insert(0,'/scratch/jjyeung/orch_n30/native_r4/builds/04_vsti_d/code')
import report as R
L='/scratch/jjyeung/orch_n30/native_r4'
truth=json.load(open(L+'/work/mid/i/SCORES.json'))
allrows=[json.loads(l) for l in open(L+'/work/mid/j0/items.jsonl')]
rows=[r for r in (json.loads(l) for l in open(L+'/work/mid/j0/items.jsonl')) if r['arm']=='native']
rows=[dict(r,scene=truth[r['key']]['scene'],room=truth[r['key']]['room']) for r in rows]
comp={}
for name in ('f17','p1m200'):
    comp[name]={'q'+str(json.loads(l)['example_id']):json.loads(l) for l in open(f'{L}/in/comparators/{name}.per_question_scores.jsonl')}
out={'items_total':len(rows)}
for t in ('camera_displacement','camera_movement_direction'):
    v=[r for r in rows if r['question_type']==t]
    m=R.metrics(v,[t]);m.pop('refusal_cost',None) if False else None
    entry=dict(items=m['items'],any_call=m['items_with_any_call'],served=m['camera_calls_served'],refused=m['calls_refused'],camera_call_errors=m['camera_call_errors'],
               score=100*m['score'] if m['score'] is not None else None,
               scene_ci=[100*m['scene_interval']['low'],100*m['scene_interval']['high']] if m['scene_interval'] else None,
               clusters=m['scene_interval']['clusters'] if m['scene_interval'] else None,
               forced_closes=m['forced_closes'],no_final=m['no_final_answers'],auto_zero=m['geometry_auto_zero'],gravity_refusals=m['gravity_refusals'],
               refusal_items=m['refusal_cost']['items'],refusal_score=m['refusal_cost']['score'],refusal_answers=m['refusal_cost']['answers'])
    for name,c in comp.items():
        keys=[r['key'] for r in v if r['key'] in c]
        other=np.mean([c[k]['official_fuzzy_score'] for k in keys])*100
        mine=np.mean([r['score'] for r in v if r['key'] in c])*100
        scenes=sorted({r['scene'] for r in v});idx={s:i for i,s in enumerate(scenes)}
        d=np.zeros(len(scenes));n=np.zeros(len(scenes))
        for r in v:
            if r['key'] in c:d[idx[r['scene']]]+=r['score']-c[r['key']]['official_fuzzy_score'];n[idx[r['scene']]]+=1
        rng=np.random.default_rng(544);w=rng.multinomial(len(scenes),[1/len(scenes)]*len(scenes),size=2000)
        boot=(w@d)/(w@n)*100
        entry[name]=dict(same_items=len(keys),other=other,native=mine,diff=mine-other,diff_ci=[float(np.quantile(boot,.025)),float(np.quantile(boot,.975))])
    sc=[r for r in allrows if r['arm']=='scripted' and r['question_type']==t]
    entry['scripted']=dict(items=len(sc),score=100*float(np.mean([r['score'] for r in sc])) if sc else None)
    out[t]=entry
print(json.dumps(out,indent=1,default=float))
