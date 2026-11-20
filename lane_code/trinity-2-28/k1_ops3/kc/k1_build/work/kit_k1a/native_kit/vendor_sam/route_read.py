"""Routed official VSI-Bench read: replace the direct answer of each routed item (abs distance, room size) by the kit's
program answer (price_masks PER_ITEM.jsonl, arm 'predicted'), score it with the official MRA, and aggregate in the
official 8-task form (three direction sub-types averaged first). Arms: routed+fb (no program answer -> direct score)
and routed_strict (no program answer -> 0). Paired scene-clustered bootstrap against the direct read (10,000, seed 17)."""
import argparse,collections,json,hashlib,random,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'vendor'))
from score_and_aggregate_orchard import official_mra
ROUTED=('object_abs_distance','room_size_estimation')
DIRS=('object_rel_direction_easy','object_rel_direction_medium','object_rel_direction_hard')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rows(p):return [json.loads(l) for l in Path(p).read_text().splitlines() if l.strip()]
def primary(recs):
    by=collections.defaultdict(list)
    for r in recs:by[r['question_type']].append(r['score'])
    task={t:sum(v)/len(v) for t,v in by.items() if t not in DIRS}
    task['object_rel_direction']=sum(sum(by[t])/len(by[t]) for t in DIRS)/3
    return sum(task.values())/len(task),{k:round(100*v,2) for k,v in sorted(task.items())}
def boot(pairs,seed=17,draws=10000):
    by=collections.defaultdict(list)
    for s,a,b in pairs:by[s].append(b-a)
    keys=sorted(by);rng=random.Random(seed);n=sum(len(v) for v in by.values())
    point=100*sum(sum(v) for v in by.values())/n;vals=[]
    for _ in range(draws):
        pick=[keys[rng.randrange(len(keys))] for _ in keys];d=[x for k in pick for x in by[k]];vals.append(100*sum(d)/len(d))
    vals.sort();return dict(diff_pp=round(point,2),low_pp=round(vals[int(.025*draws)],2),high_pp=round(vals[int(.975*draws)-1],2),n=n,scenes=len(keys))
def main(a):
    items={q['qid']:q for q in rows(a.items)};direct=rows(a.direct)
    if len(direct)!=5130 or len({r['example_id'] for r in direct})!=5130:raise ValueError('Direct read must hold 5,130 distinct items')
    prog={}
    for r in rows(a.per_item):
        if r['arm']!='predicted':continue
        if r['qid'] in prog:raise ValueError('Duplicate program row '+r['qid'])
        prog[r['qid']]=r
    stub=any(r.get('stub') for r in prog.values())
    if stub and not a.allow_stub:raise ValueError('Stub program rows cannot produce a routed score')
    out={'routed_fb':[],'routed_strict':[]};missing=[];noans=collections.Counter();cnt=collections.Counter()
    for d in direct:
        t=d['question_type']
        if t not in ROUTED:
            for k in out:out[k].append(d)
            continue
        q=items[d['example_id']]
        if (q['dataset'],q['scene'].split('/')[1],str(q['released_answer']))!=(d['dataset'],d['scene_name'],str(float(d['ground_truth']))):raise ValueError('Item/direct mismatch '+d['example_id'])
        p=prog.get(d['example_id'])
        if p is None:
            missing.append(d['example_id'])
            if not a.partial:raise ValueError('No program row for routed item '+d['example_id'])
            for k in out:out[k].append(d)
            continue
        cnt[q['dataset'],t]+=1
        if p['pred'] is None:
            noans[q['dataset'],t]+=1;s_fb,s_st=d['score'],0.
        else:s_fb=s_st=official_mra(float(p['pred']),float(d['ground_truth']))
        base=dict(d,route='program',program_pred=p['pred'],program_error=p['error'],direct_score=d['score'])
        out['routed_fb'].append(dict(base,score=s_fb));out['routed_strict'].append(dict(base,score=s_st))
    dp,dtask=primary(direct);summ=dict(direct=dict(sha256=sha(a.direct),primary_pct=round(100*dp,2),per_task_score_pct=dtask),items_sha256=sha(a.items),per_item_sha256=sha(a.per_item),stub=stub,partial=bool(missing),missing_program_items=len(missing),program_items={'/'.join(k):v for k,v in sorted(cnt.items())},program_no_answer={'/'.join(k):v for k,v in sorted(noans.items())},arms={})
    Path(a.out).mkdir(parents=True,exist_ok=True)
    for k,recs in out.items():
        pp,task=primary(recs);dd={r['example_id']:r['score'] for r in direct}
        pairs=[(r['dataset']+'/'+r['scene_name'],dd[r['example_id']],r['score']) for r in recs]
        per={}
        for t in ROUTED:
            for ds in ('All','arkitscenes','scannet','scannetpp'):
                sel=[x for x,r in zip(pairs,recs) if r['question_type']==t and (ds=='All' or r['dataset']==ds)]
                if sel:per[t+'/'+ds]=dict(program_pct=round(100*sum(x[2] for x in sel)/len(sel),2),direct_pct=round(100*sum(x[1] for x in sel)/len(sel),2),**boot(sel,draws=a.boot))
        # Primary-score difference: the 8-task mean moves by (type-mean change)/8 per routed task.
        summ['arms'][k]=dict(primary_pct=round(100*pp,2),primary_minus_direct_pp=round(100*(pp-dp),2),per_task_score_pct=task,routed_types=per)
        with open(Path(a.out)/(k+'.per_question_scores.jsonl'),'w') as f:
            for r in recs:f.write(json.dumps(r)+'\n')
    (Path(a.out)/'ROUTED_READ.json').write_text(json.dumps(summ,indent=1)+'\n');print(json.dumps({k:(v['primary_pct'],v['primary_minus_direct_pp']) for k,v in summ['arms'].items()}|dict(direct=summ['direct']['primary_pct'],stub=stub,missing=len(missing))))
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('items','per-item','direct','out'):p.add_argument('--'+n,required=True)
    p.add_argument('--allow-stub',action='store_true',help='dry runs only');p.add_argument('--partial',action='store_true',help='dry runs only: routed items without a program row keep the direct answer');p.add_argument('--boot',type=int,default=10000)
    main(p.parse_args())
