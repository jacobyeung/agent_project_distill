import json,sys
sys.path.insert(0,'/scratch/jjyeung/orch_n30/review_d0r2/cur')
import f1f2 as F
A=[json.loads(l) for l in open('/scratch/jjyeung/orch_n30/review_d0r2/cur/evidence/A544.jsonl')]
def mk(step, away=None, alike=None, drop=None, fwd_drop=0, raise_t=None):
    B=[dict(r,step=step) for r in A]
    if away:
        for lev,k in away.items():
            rows=[r for r in B if r['family']=='away' and r['level']==lev]
            for i,r in enumerate(rows): r['score']=1.0 if i<k else 0.0
    for t,n in (drop or []):
        rows=[r for r in B if r['family']=='main' and r['task_type']==t and r['score']>0]
        for r in rows[:n]: r['score']=0.0
    if fwd_drop:
        rows=[r for r in B if r['family']=='forward' and r['score']==1.0]
        for r in rows[:fwd_drop]: r['score']=0.0
    if alike is not None:
        aw={r['pair_id']:r for r in B if r['family']=='away'}; fw={r['pair_id']:r for r in B if r['family']=='forward'}
        for i,k in enumerate(sorted(aw)):
            aw[k]['answer_content']=fw[k]['answer_content'] if i<alike else (fw[k]['answer_content'] or '')+'_x'
    return B
def run(name,b,step,prev=None,expect=None):
    try:
        r=F.evaluate(A,b,step,prev)
    except Exception as e:
        out='RAISE '+type(e).__name__+': '+str(e)
        print(('OK ' if expect=='RAISE' else 'BAD')+' | '+name+' | '+out); return
    aw={k:v['accuracy_pct'] for k,v in r['f2']['away'].items()}
    v=r.get('verdict')
    ok = (v==expect)
    print(('OK ' if ok else 'BAD')+' | '+name+' | verdict',v,'| f1fail',[t for t,x in r['f1'].items() if x['fail']],'| f2_fail',r['f2_fail'],'point_fail',r['f2_point_estimate_information_only']['fail'],'| away',aw,'alike',r['f2']['pairs']['alike_pct'],'| reasons',r['reasons'])
HI=dict(easy=48,medium=45,hard=45)
# step 100
run('100 F1 route fails, away tie',mk(100,drop=[('route_planning',40)]),100,expect=None)
# step 200 facing boundaries
run('200 identical (ties all)',mk(200),200,expect='STOP')
run('200 just above all 40/22/8',mk(200,away=dict(easy=20,medium=11,hard=4)),200,expect='CONTINUE')
run('200 hard tie 40/22/6',mk(200,away=dict(easy=20,medium=11,hard=3)),200,expect='STOP')
run('200 easy below 36/22/8',mk(200,away=dict(easy=18,medium=11,hard=4)),200,expect='STOP')
run('200 F2 fails, above all, alike 49%',mk(200,away=dict(easy=20,medium=11,hard=4)),200,expect='CONTINUE')
run('200 point-pass bound-fail 60/46/42',mk(200,away=dict(easy=30,medium=23,hard=21),alike=10),200,expect='CONTINUE')
run('200 F2 pass HI alike 20%',mk(200,away=HI,alike=30),200,expect='CONTINUE')
# F1 at 200: each registered type; info types
for t in F.F1_TYPES:
    run('200 F1 drop '+t,mk(200,away=dict(easy=20,medium=11,hard=4),drop=[(t,40)]),200,expect='STOP')
for t in F.F1_INFORMATION_TYPES:
    run('200 info drop '+t,mk(200,away=dict(easy=20,medium=11,hard=4),drop=[(t,40)]),200,expect='CONTINUE')
run('200 abs_distance drop (unregistered)',mk(200,away=dict(easy=20,medium=11,hard=4),drop=[('object_abs_distance',60)]),200,expect='CONTINUE')
run('200 toward drop 20 (F2 only)',mk(200,away=dict(easy=20,medium=11,hard=4),fwd_drop=20),200,expect='CONTINUE')
# later reads
for s,p in ((400,200),(600,400),(800,600)):
    prev=mk(p,away=dict(easy=24,medium=14,hard=6))
    run(f'{s} two below F2 fail',mk(s,away=dict(easy=23,medium=13,hard=6)),s,prev,expect='STOP')
    run(f'{s} three below F2 fail',mk(s,away=dict(easy=23,medium=13,hard=5)),s,prev,expect='STOP')
    run(f'{s} one below F2 fail',mk(s,away=dict(easy=23,medium=14,hard=6)),s,prev,expect='CONTINUE')
    run(f'{s} two equal one below',mk(s,away=dict(easy=24,medium=14,hard=5)),s,prev,expect='CONTINUE')
    run(f'{s} below 544 but not below prev',mk(s,away=dict(easy=24,medium=14,hard=6)),s,prev,expect='CONTINUE')
    prevhi=mk(p,away=dict(easy=49,medium=46,hard=46),alike=10)
    run(f'{s} two below F2 PASS',mk(s,away=HI,alike=10),s,prevhi,expect='CONTINUE')
    run(f'{s} two below F2 pass bound but alike 21%',mk(s,away=HI,alike=31),s,prevhi,expect='STOP')
    run(f'{s} F1 counting drop, away up',mk(s,away=dict(easy=25,medium=15,hard=7),drop=[('object_counting',60)]),s,prev,expect='STOP')
    run(f'{s} missing prev',mk(s),s,None,expect='RAISE')
    run(f'{s} prev wrong step',mk(s),s,mk(100),expect='RAISE')
run('200 with prev given',mk(200),200,mk(100),expect='RAISE')
run('100 with prev given',mk(100),100,mk(100),expect='RAISE')
run('1000 final F2 fail, F1 fail',mk(1000,drop=[('route_planning',40)]),1000,mk(800),expect='FINAL')
run('1000 final F2 pass',mk(1000,away=HI,alike=10),1000,mk(800),expect='FINAL')
run('300 bad step',mk(300),300,None,expect='RAISE')
run('200 b rows claim step 100',mk(100),200,None,expect='RAISE')
