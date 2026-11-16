"""Report only kit-merged, frame-checked rows; paired room-cluster bootstrap."""
import argparse
import collections
import importlib
import json
from pathlib import Path
import random
import subprocess
import sys
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).parent))
from adapter import dump,digest,jsonl,payload,verify_bound,kit_import,SCORERS


def check_frames(row,task,cell):
    if row.get('layout')!=cell['layout']:raise ValueError('Journal layout differs')
    if row.get('status')!='complete':raise ValueError('Incomplete journal item: '+row['key'])
    want=task['source_frame_indices']
    expanded=[i for i in want for _ in range(2)] if cell['layout']=='duplicate' else want
    media=row.get('media',{})
    if media.get('anchor_indices')!=want or media.get('metadata',{}).get('frames_indices')!=expanded:
        raise ValueError('Journal does not read exact ordered PLAN anchors')


def conflicts(path):
    seen={}
    for r in jsonl(path):
        if r.get('status')!='complete':continue
        if r['key'] in seen and seen[r['key']]!=r:raise ValueError('Conflicting complete journal rows')
        seen[r['key']]=r


def extract(args):
    dest,cfg,status=verify_bound(args.dest);data,_,official=kit_import(dest/'kit')
    tasks=data.tasks_for(cfg['datasets'][0],cfg['roots']);by_key={'devrows:'+t['example_id']:t for t in tasks}
    cell=cfg['cells'][0];model=cell['model'];out=Path(cfg['output'])
    if args.arm=='B2048' and model!='cp1m200':raise ValueError('Budget arm requires CP1')
    conflicts(out/'0/g0.jsonl')
    base=importlib.import_module('merge').merge(cfg,0,args.attempt)
    if not base['parity_pass']:raise ValueError('Kit parity gate failed')
    chosen=out/'0'
    if args.arm=='B2048':
        importlib.import_module('budget_merge').merge_budgets(cfg,0,args.attempt)
        chosen=out/'budget_2048/0'
    summary=json.loads((chosen/f'summary_{args.attempt}.json').read_text())
    if not summary['parity_pass']:raise ValueError('Arm parity gate failed')
    rows=jsonl(chosen/f'items_{args.attempt}.jsonl')
    if len(rows)!=len(by_key) or {r['key'] for r in rows}!=set(by_key):raise ValueError('Incomplete or duplicate report membership')
    scorer=importlib.import_module('scoring').score_item
    results=[]
    for r in rows:
        task=by_key[r['key']];check_frames(r,task,cell)
        # The kit merge authenticates ordinary raw text and budget continuation context.
        # Score the already-authenticated visible answer with the SAME kit cap contract.
        visible='</think>\n'+r['response_text'] if r['response_text'] else ''
        scores={}
        for field in ('released_answer','answer'):
            value=task.get(field)
            if value is None:scores[field]=None;continue
            again=scorer(dict(task,ground_truth=value,thinking=True),visible,r['output_tokens'],cap=r['max_new_tokens'],finish=r['finish_reason'])
            scores[field]=again['score']
            if field=='released_answer' and abs(again['score']-r['score'])>1e-12:
                raise ValueError('Visible-answer rescore differs from authenticated kit score')
        results.append(dict(key=r['key'],question_type=task['question_type'],room=task['room'],stratum=task['stratum'],
                            scores=scores,capped=bool(r['hit_token_cap']),unanswered=not bool(r['response_text'].strip()),
                            unparsed=bool(r['parse_failed'])))
    dump(args.output,dict(model=model,arm=args.arm,request_binding=cfg['binding'],source_sha256=cfg['source_sha256'],
                          strata_sha256=cfg['devs1']['pins']['STRATA.jsonl'],rows=results))


def aggregate(rows,field):
    values=[r['scores'][field] for r in rows if r['scores'][field] is not None]
    return dict(items=len(rows),scored=len(values),score_pct=100*sum(values)/len(values) if values else None,
                capped=sum(r['capped'] for r in rows),unanswered=sum(r['unanswered'] for r in rows),
                unparsed=sum(r['unparsed'] for r in rows))


def summarize(rows):
    result={}
    for st in ('primary','disagreement','missing_released','missing_canonical','missing_both'):
        rs=[r for r in rows if r['stratum']==st]
        fields=('released_answer',) if st=='primary' else ('released_answer','answer')
        result[st]={f:dict(overall=aggregate(rs,f),per_type={t:aggregate([r for r in rs if r['question_type']==t],f) for t in SCORERS}) for f in fields}
    result['disagreement_count_per_type']={t:sum(r['stratum']=='disagreement' and r['question_type']==t for r in rows) for t in SCORERS}
    return result


def paired(a,b,field,replicates=10000,seed=17):
    aa={r['key']:r for r in a};bb={r['key']:r for r in b}
    if set(aa)!=set(bb):raise ValueError('Paired keys differ')
    clusters=collections.defaultdict(list)
    for key,x in aa.items():
        y=bb[key]
        if (x['room'],x['stratum'],x['question_type'])!=(y['room'],y['stratum'],y['question_type']):raise ValueError('Paired metadata differs')
        v,w=x['scores'][field],y['scores'][field]
        if v is not None and w is not None:clusters[x['room']].append(v-w)
    if not clusters:return dict(items=0,rooms=0,delta_pp=None,ci95_pp=None)
    grouped=[(sum(ds),len(ds)) for _,ds in sorted(clusters.items())]
    n=sum(v[1] for v in grouped);delta=sum(v[0] for v in grouped)/n
    rng=random.Random(seed);samples=[]
    for _ in range(replicates):
        draw=rng.choices(grouped,k=len(grouped));samples.append(sum(v[0] for v in draw)/sum(v[1] for v in draw))
    samples.sort()
    def quantile(p):
        k=(len(samples)-1)*p;i=int(k);j=min(i+1,len(samples)-1)
        return 100*(samples[i]+(samples[j]-samples[i])*(k-i))
    return dict(items=n,rooms=len(grouped),delta_pp=100*delta,ci95_pp=[quantile(.025),quantile(.975)],
                replicates=replicates,seed=seed,estimator='item-weighted mean; resample whole physical rooms with replacement, retain all paired items')


def report(args):
    dest=Path(args.output);dest.mkdir(parents=True,exist_ok=False)
    exports={}
    for name,run,arm,attempt in [('CP1_ON16k',args.cp1,'ON16k',args.cp1_attempt),
                                ('CP1_B2048',args.cp1,'B2048',args.cp1_attempt),('f17',args.f17,'ON16k',args.f17_attempt)]:
        target=dest/(name+'.json')
        subprocess.run([sys.executable,'-I','-s',str(Path(__file__).resolve()),'extract','--dest',run,'--arm',arm,
                        '--attempt',attempt,'--output',str(target)],check=True)
        exports[name]=json.loads(target.read_text())
    if len({x['strata_sha256'] for x in exports.values()})!=1:raise ValueError('Strata pins differ between runs')
    result=dict(strata_sha256=exports['f17']['strata_sha256'],models={k:summarize(v['rows']) for k,v in exports.items()},
                aggregation='Item-weighted overall across all 11 types; no claim of official VSI benchmark overall',comparisons={})
    for arm in ('CP1_ON16k','CP1_B2048'):
        comparisons={}
        for st in ('primary','disagreement'):
            a=[r for r in exports[arm]['rows'] if r['stratum']==st]
            b=[r for r in exports['f17']['rows'] if r['stratum']==st]
            comparisons[st]={f:dict(overall=paired(a,b,f,args.replicates),per_type={t:paired(
                [r for r in a if r['question_type']==t],[r for r in b if r['question_type']==t],f,args.replicates)
                for t in SCORERS}) for f in (('released_answer',) if st=='primary' else ('released_answer','answer'))}
        result['comparisons'][arm+' minus f17']=comparisons
    dump(dest/'REPORT.json',result)
    dump(dest/'REPORT_RECEIPT.json',{k:{f:v[f] for f in ('model','arm','request_binding','source_sha256','strata_sha256')} for k,v in exports.items()})
    print(str(dest/'REPORT.json'))


def main():
    p=argparse.ArgumentParser(description=__doc__);sp=p.add_subparsers(dest='command',required=True)
    q=sp.add_parser('extract')
    for n in ('dest','attempt','output'):q.add_argument('--'+n,required=True)
    q.add_argument('--arm',choices=['ON16k','B2048'],required=True)
    q=sp.add_parser('report')
    for n in ('cp1','f17','cp1-attempt','f17-attempt','output'):q.add_argument('--'+n,required=True)
    q.add_argument('--replicates',type=int,default=10000)
    a=p.parse_args();(extract if a.command=='extract' else report)(a)
if __name__=='__main__':main()
