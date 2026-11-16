"""Aggregate stored kit scores; bootstrap scenes jointly across the six tasks."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import sys
import math
sys.path.insert(0,str(Path(__file__).resolve().parent/'evaluator'))
from evalpath.official import VSI_PRIMARY_GROUPS
EXCLUDED={'object_abs_distance':834,'room_size_estimation':288}
GROUPS={k:v for k,v in VSI_PRIMARY_GROUPS.items() if k not in EXCLUDED}


def read_rows(path):
    with Path(path).open() as stream:
        return [json.loads(line) for line in stream if line.strip()]


def key(row):return str(row.get('example_id',row.get('id')))


def index(rows):
    result={}
    for r in rows:
        k=key(r)
        if k in result:raise ValueError('Duplicate item: '+k)
        result[k]=r
    return result


def per_type(rows):
    groups=defaultdict(list)
    for r in rows:
        error=r.get('status')!='complete' or r.get('derivation_error',False)
        value=0.0 if error else r['score']
        if not isinstance(value,(float,int)) or not math.isfinite(value) or not 0<=value<=1:
            raise ValueError('Invalid stored score')
        groups[r['question_type']].append(value)
    return {k:dict(items=len(v),score=sum(v)/len(v)) for k,v in sorted(groups.items())}


def aggregate(tasks,rows,sources,*,repetitions=10000,seed=544,allow_partial=False):
    import numpy as np
    expected=index(tasks);observed=index(rows);source=index(sources)
    if set(observed)-set(expected) or set(source)-set(expected):raise ValueError('Foreign score membership')
    if not allow_partial and (len(expected)!=4008 or len({(r['dataset'],r['scene_name']) for r in tasks})!=288):
        raise ValueError('Require all 4008 items and 288 scenes')
    scenes=sorted({(r['dataset'],r['scene_name']) for r in tasks});scene_index={s:i for i,s in enumerate(scenes)}
    types=sorted({t for ts in GROUPS.values() for t in ts});type_index={t:i for i,t in enumerate(types)}
    totals=np.zeros((len(scenes),len(types)));counts=np.zeros_like(totals)
    detail=[]
    for k,t in expected.items():
        if t['question_type'] not in type_index:raise ValueError('Excluded task entered score denominator')
        r=observed.get(k,{})
        if r and r['question_type']!=t['question_type']:raise ValueError('Score task differs')
        error=not r or r.get('status')!='complete' or bool(r.get('derivation_error'))
        score=0.0 if error else r['score']
        if not isinstance(score,(float,int)) or not math.isfinite(score) or not 0<=score<=1:raise ValueError('Invalid stored score')
        s=source.get(k,{})
        i,j=scene_index[(t['dataset'],t['scene_name'])],type_index[t['question_type']]
        totals[i,j]+=score;counts[i,j]+=1
        detail.append(dict(id=k,question_type=t['question_type'],dataset=t['dataset'],scene_name=t['scene_name'],score=score,
            error=(r.get('error','missing record') if error else None),
            source_capped=s.get('output_tokens',0)>=16384 or (s.get('max_new_tokens')==16384 and s.get('finish_reason')=='length'),
            continuation_capped=r.get('max_new_tokens')==64 and (r.get('output_tokens',0)>=64 or r.get('finish_reason')=='length'),
            unparsed=error or bool(r.get('parse_failed',False))))
    # Resample scenes once per replicate, preserving cross-task correlation.
    rng=np.random.default_rng(seed)
    weights=rng.multinomial(len(scenes),np.full(len(scenes),1/len(scenes)),size=repetitions)
    den=weights@counts;num=weights@totals
    sub=np.divide(num,den,out=np.full_like(num,np.nan),where=den>0)
    scores=np.divide(totals.sum(0),counts.sum(0),out=np.full(len(types),np.nan),where=counts.sum(0)>0)
    groups={};replicas=[]
    def ci(values):
        valid=values[np.isfinite(values)]
        return dict(percentile_95=(np.percentile(valid,[2.5,97.5]).tolist() if len(valid) else None),valid_replicates=len(valid))
    for name,ts in GROUPS.items():
        slots=[type_index[t] for t in ts]
        val=float(np.mean(scores[slots]));draw=np.mean(sub[:,slots],axis=1);replicas.append(draw)
        selected=[r for r in detail if r['question_type'] in ts]
        groups[name]=dict(score=val if math.isfinite(val) else None,items=len(selected),
            errors=[dict(id=r['id'],error=r['error']) for r in selected if r['error'] is not None],
            source_capped=sum(r['source_capped'] for r in selected),continuation_capped=sum(r['continuation_capped'] for r in selected),
            unparsed=sum(r['unparsed'] for r in selected),**ci(draw))
    mean=None if any(v['score'] is None for v in groups.values()) else sum(v['score'] for v in groups.values())/6
    return dict(items=len(tasks),scenes=len(scenes),groups=groups,six_task_mean=dict(score=mean,**ci(np.mean(replicas,axis=0))),
        excluded={k:dict(status='not read',items=n) for k,n in EXCLUDED.items()},
        bootstrap=dict(unit='dataset/scene_name',repetitions=repetitions,seed=seed,interval='percentile 2.5,97.5',
                       grouping='equal subtype means, then equal task means',zero_denominator='replicate is undefined; excluded from that interval and counted'),
        per_type=per_type([dict(r,status='complete' if r['error'] is None else 'error') for r in detail]),rows=detail)


def score_run(dest,cohort,output,allow_partial=False):
    dest=Path(dest);tasks=read_rows(cohort)
    request=json.loads((dest/'request.json').read_text())
    proof=request.get('mode')=='proof'
    source=read_rows(dest/'results/0/items_a0.jsonl')
    arms={'ON16k':source,**{f'B{b}':read_rows(dest/f'results/0/budget_{b}.jsonl') for b in (2048,4096)}}
    out=Path(output);out.mkdir(parents=True,exist_ok=True)
    reports={}
    for arm,rows in arms.items():
        reports[arm]=aggregate(tasks,rows,source,allow_partial=allow_partial)
        reports[arm].update(arm=arm,role='primary' if arm=='B2048' else 'secondary',
                            mode='proof' if proof else 'production',generation_synthetic=proof)
        (out/(arm+'.json')).write_text(json.dumps(reports[arm],indent=2,allow_nan=False)+'\n')
    return {a:dict(items=r['items'],six_task_mean=r['six_task_mean']) for a,r in reports.items()}


def self_check(packet):
    packet=Path(packet);rows=read_rows(packet/'direct/main/results/0/budget_2048.jsonl')
    report=json.loads((packet/'merged/main/report/B2048.json').read_text())
    actual=per_type(rows);comparisons={}
    for typ,got in actual.items():
        primary=report['summary']['primary']['released_answer']['per_type'][typ]
        ref=primary if primary['items'] else report['summary']['unavailable']['answer']['per_type'][typ]
        delta=got['score']*100-ref['score_pct']
        if got['items']!=ref['items'] or abs(delta)>1e-10:raise ValueError('Accepted per-type score differs: '+typ)
        comparisons[typ]=dict(items=got['items'],score_pct=got['score']*100,accepted_score_pct=ref['score_pct'],delta=delta)
    return dict(passed=True,items=len(rows),types=len(comparisons),per_type=comparisons,
        field_difference='Stored kit scores use released_answer on primary items and answer when released labels are unavailable. own_gt_by_stratum.primary instead uses answer; distance and room-size means differ there. This check compares the matching summary fields. Official six-task aggregation does not use the dev report item-weighted overall.')


def main():
    p=argparse.ArgumentParser();p.add_argument('--self-check');p.add_argument('--dest');p.add_argument('--cohort');p.add_argument('--output',required=True)
    a=p.parse_args()
    if a.self_check:Path(a.output).write_text(json.dumps(self_check(a.self_check),indent=2)+'\n')
    else:score_run(a.dest,a.cohort,a.output)
if __name__=='__main__':main()
