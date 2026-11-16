import json,sys,copy,random
sys.path.insert(0,'.')
import f1f2 as F
A=[json.loads(l) for l in open('evidence/A544.jsonl')]
def mk(step, away_k=None, alike_force=None, main_shift=None, fwd_drop=0):
    B=[dict(r,step=step) for r in A]
    if away_k:
        for lev,k in away_k.items():
            rows=[r for r in B if r['family']=='away' and r['level']==lev]
            for i,r in enumerate(rows): r['score']=1.0 if i<k else 0.0
    if main_shift:
        t,n=main_shift
        rows=[r for r in B if r['family']=='main' and r['task_type']==t and r['score']==1.0]
        for r in rows[:n]: r['score']=0.0
    if fwd_drop:
        rows=[r for r in B if r['family']=='forward' and r['score']==1.0]
        for r in rows[:fwd_drop]: r['score']=0.0
    if alike_force is not None:
        aw={r['pair_id']:r for r in B if r['family']=='away'}; fw={r['pair_id']:r for r in B if r['family']=='forward'}
        keys=sorted(aw)
        for i,k in enumerate(keys):
            if i<alike_force: aw[k]['answer_content']=fw[k]['answer_content']
            else: aw[k]['answer_content']=(fw[k]['answer_content'] or '')+'_x'
    return B
def run(name,b,step,m100=None):
    r=F.evaluate(A,b,step,m100)
    aw={k:(v['accuracy_pct'],[round(x,1) for x in v['ci95_pct']],v['fail']) for k,v in r['f2']['away'].items()}
    print(name,'| f1_fail',r['f1_fail'],[t for t,v in r['f1'].items() if v['fail']],'| f2_fail',r['f2_fail'],aw,'alike',r['f2']['pairs']['alike_pct'],'toward',[round(x,1) for x in r['f2']['toward_delta']['ci95_pp']], '| verdict',r.get('verdict','<none>'))
run('S100 identical',mk(100),100)
m100=mk(100,away_k={'easy':20,'medium':12,'hard':5})
run('S200 identical, m100 higher',mk(200),200,m100)
run('S200 rising 2/3 above 544 all, alike 49',mk(200,away_k={'easy':21,'medium':13,'hard':4}),200,m100)
run('S200 rising 3/3 but hard == 544',mk(200,away_k={'easy':21,'medium':13,'hard':6}),200,mk(100,away_k={'easy':20,'medium':12,'hard':2}))
run('S200 away passes bound, alike 30 (20%)',mk(200,away_k={'easy':36,'medium':30,'hard':28},alike_force=30),200,m100)
run('S200 away passes bound, alike 31',mk(200,away_k={'easy':36,'medium':30,'hard':28},alike_force=31),200,m100)
run('S200 point-pass bound-fail 60/46/42',mk(200,away_k={'easy':30,'medium':23,'hard':21},alike_force=10),200,mk(100,away_k={'easy':31,'medium':24,'hard':22}))
run('S200 relative_count drop 25',mk(200,away_k={'easy':36,'medium':30,'hard':28},alike_force=10,main_shift=('relative_count',25)),200,m100)
run('S200 route drop 20',mk(200,away_k={'easy':36,'medium':30,'hard':28},alike_force=10,main_shift=('route_planning',20)),200,m100)
run('S200 toward drop 12',mk(200,away_k={'easy':36,'medium':30,'hard':28},alike_force=10,fwd_drop=12),200,m100)
try: run('S200 F2 fail no m100',mk(200),200,None)
except Exception as e: print('no m100 ->',type(e).__name__,e)
try: run('step 400',mk(400),400,m100)
except Exception as e: print('step 400 ->',type(e).__name__,e)
