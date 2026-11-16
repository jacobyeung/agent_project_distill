import json,random,sys,math
from pathlib import Path
K=Path('/scratch/jjyeung/orch_n30/review_rv/work/fresh')
sys.path.insert(0,str(K/'reader'));sys.path.insert(0,str(K/'reader/evaluator'))
import scoring, official_score as O
rows=[json.loads(l) for l in open(K/'cohort/COHORT_REVSI5.jsonl')]
rng=random.Random(7)
def answer(r):
    u=rng.random();gt=r['ground_truth']
    if r['options']:
        letters=[o.split('.')[0] for o in r['options']]
        if u<0.5:return gt
        if u<0.9:return rng.choice(letters)
        return ''
    g=float(gt)
    if u<0.8:return str(round(g*rng.uniform(0.4,1.6),2))
    if u<0.9:return 'abc'
    return ''
ans={r['qid']:answer(r) for r in rows}
err={r['qid'] for r in rows if rng.random()<0.05}
out=[]
for r in rows:
    m=scoring.metric_for([dict(r,example_id=r['qid'])]);m.update({int(r['qid']):ans[r['qid']]})
    s=float(m.__dict__[r['question_type']+'_acc'])
    out.append(dict(example_id=r['qid'],question_type=r['question_type'],status='error' if r['qid'] in err else 'complete',score=s,output_tokens=10))
tasks=[dict(r,example_id=r['qid']) for r in rows]
rep=O.aggregate(rows,out,out,repetitions=200)
m=scoring.metric_for(tasks);m.update({int(r['qid']):('' if r['qid'] in err else ans[r['qid']]) for r in rows})
off={k:float(v) for k,v in m.compute().items()}
cats=['object_counting','object_rel_direction','object_rel_distance','object_size_estimation','route_planning']
mx=0
for c in cats:
    a=rep['groups'][c]['score']*100;b=off[c+'_acc'];mx=max(mx,abs(a-b));print(c,round(a,6),round(b,6),rep['groups'][c]['items'],len(rep['groups'][c]['errors']))
five=rep['five_category_mean']['score']*100;print('five',five,'official overall(nanmean of present 5)',off['overall_acc'],'abs/room',off['object_abs_distance_acc'],off['room_size_estimation_acc'])
print('max cat diff',mx,'five diff',abs(five-off['overall_acc']))
print('denominator items',rep['items'],'errors',sum(len(g['errors']) for g in rep['groups'].values()),'injected',len(err))
print('excluded',rep['excluded'])
