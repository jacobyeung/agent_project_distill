"""Aggregate stored kit scores; bootstrap scenes jointly across the five categories."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import sys
import math
sys.path.insert(0,str(Path(__file__).resolve().parent/'evaluator'))
EXCLUDED={'object_abs_distance':283,'room_size_estimation':37}
GROUPS={
 'object_counting':('object_counting_single','object_counting_multiple'),
 'object_rel_direction':('object_rel_direction_forward_easy','object_rel_direction_backward_easy','object_rel_direction_forward_hard','object_rel_direction_backward_hard'),
 'object_rel_distance':('object_rel_distance_closest','object_rel_distance_farthest'),
 'object_size_estimation':('object_size_estimation',),
 'route_planning':('route_planning',)}


def facing(question):
    text=' '.join(question.lower().split())
    if 'facing in the opposite direction of ' in text:return 'away'
    if ' and facing the ' in text:return 'toward'
    raise ValueError('Unrecognized direction question wording')


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


def aggregate(tasks,rows,sources,*,repetitions=10000,seed=544,allow_partial=False,return_draws=False):
    import numpy as np
    expected=index(tasks);observed=index(rows);source=index(sources)
    if set(observed)-set(expected) or set(source)-set(expected):raise ValueError('Foreign score membership')
    if not allow_partial and (len(expected)!=679 or len({(r['dataset'],r['scene_name']) for r in tasks})!=261):
        raise ValueError('Require all 679 items and 261 scenes')
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
        slots=[type_index[t] for t in ts if counts[:,type_index[t]].sum()>0]
        val=float(np.mean(scores[slots])) if slots else float('nan');draw=np.mean(sub[:,slots],axis=1) if slots else np.full(repetitions,np.nan);replicas.append(draw)
        selected=[r for r in detail if r['question_type'] in ts]
        groups[name]=dict(score=val if math.isfinite(val) else None,items=len(selected),
            errors=[dict(id=r['id'],error=r['error']) for r in selected if r['error'] is not None],
            source_capped=sum(r['source_capped'] for r in selected),continuation_capped=sum(r['continuation_capped'] for r in selected),
            unparsed=sum(r['unparsed'] for r in selected),error_count=sum(r['error'] is not None for r in selected),**ci(draw))
    mean=None if any(v['score'] is None for v in groups.values()) else sum(v['score'] for v in groups.values())/5
    result=dict(items=len(tasks),scenes=len(scenes),groups=groups,five_category_mean=dict(score=mean,**ci(np.mean(replicas,axis=0))),
        excluded={k:dict(status='not read here: native reader required',items=n) for k,n in EXCLUDED.items()},
        bootstrap=dict(unit='dataset/scene_name',repetitions=repetitions,seed=seed,interval='percentile 2.5,97.5',
                       grouping='equal subtype means, then equal task means',zero_denominator='replicate is undefined; excluded from that interval and counted'),
        per_type=per_type([dict(r,status='complete' if r['error'] is None else 'error') for r in detail]),rows=detail)

    splits={};split_draws={}
    for label in ('toward','away'):
        chosen=[k for k,t in expected.items() if t['question_type'] in GROUPS['object_rel_direction'] and facing(t['question'])==label]
        # The text determines facing; equal difficulty/subtype weighting matches the native metric.
        subset_types=sorted({expected[k]['question_type'] for k in chosen})
        columns=[];values=[]
        for typ in subset_types:
            nums=np.zeros(len(scenes));dens=np.zeros(len(scenes))
            for d in detail:
                if d['id'] in chosen and d['question_type']==typ:
                    i=scene_index[(d['dataset'],d['scene_name'])];nums[i]+=d['score'];dens[i]+=1
            den=weights@dens;num=weights@nums
            columns.append(np.divide(num,den,out=np.full(repetitions,np.nan),where=den>0));values.append(nums.sum()/dens.sum())
        draw=np.mean(columns,axis=0) if columns else np.full(repetitions,np.nan)
        selected=[d for d in detail if d['id'] in chosen]
        splits[label]=dict(items=len(chosen),score=float(np.mean(values)) if values else None,
            error_count=sum(d['error'] is not None for d in selected),
            errors=[dict(id=d['id'],error=d['error']) for d in selected if d['error'] is not None],
            source_capped=sum(d['source_capped'] for d in selected),continuation_capped=sum(d['continuation_capped'] for d in selected),
            unparsed=sum(d['unparsed'] for d in selected),**ci(draw))
        split_draws[label]=draw
    result['direction_by_question_text']=splits
    result['bootstrap']['grouping']='equal subtype means, then equal five-category mean; proof uses present subtypes only'
    if return_draws:return result,{**dict(zip(GROUPS,replicas)),'five_category_mean':np.mean(replicas,axis=0),**{'facing_'+k:v for k,v in split_draws.items()}}
    return result


def paired(tasks,rows,parent,*,repetitions=10000,seed=544,allow_partial=False):
    import numpy as np
    ids=set(index(tasks));own=index(rows);ref=index(parent)
    if not ids<=set(own) or not ids<=set(ref):raise ValueError('Paired comparison requires every cohort ID in both arms')
    own=[own[k] for k in sorted(ids)];ref=[ref[k] for k in sorted(ids)]
    for task in tasks:
        r=index(ref)[key(task)]
        for field in ('question_type','scene','scene_name','dataset','ground_truth'):
            if field in r and field in task and str(r[field])!=str(task[field]):raise ValueError('Parent metadata differs: '+field)
    current,draw=aggregate(tasks,own,own,repetitions=repetitions,seed=seed,allow_partial=allow_partial,return_draws=True)
    previous,base=aggregate(tasks,ref,ref,repetitions=repetitions,seed=seed,allow_partial=allow_partial,return_draws=True)
    results={}
    for name in draw:
        delta=draw[name]-base[name];valid=delta[np.isfinite(delta)]
        def point(report):
            if name=='five_category_mean':return report[name]['score']
            if name.startswith('facing_'):return report['direction_by_question_text'][name[7:]]['score']
            return report['groups'][name]['score']
        x,y=point(current),point(previous)
        results[name]=dict(current=x,parent=y,delta=None if x is None or y is None else x-y,
            percentile_95=np.percentile(valid,[2.5,97.5]).tolist() if len(valid) else None,valid_replicates=len(valid))
    return dict(items=len(tasks),bootstrap=dict(unit='scene',paired=True,repetitions=repetitions,seed=seed),comparisons=results)


def score_run(dest,cohort,output,allow_partial=False,parent_answers=None):
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
    if parent_answers:
        comparison=paired(tasks,arms['B2048'],read_rows(parent_answers),allow_partial=allow_partial)
        import hashlib
        comparison['parent_answers_sha256']=hashlib.sha256(Path(parent_answers).read_bytes()).hexdigest()
        (out/'PAIRED_B2048.json').write_text(json.dumps(comparison,indent=2,allow_nan=False)+'\n')
    (out/'SUMMARY.txt').write_text(render(reports))
    return {a:dict(items=r['items'],five_category_mean=r['five_category_mean']) for a,r in reports.items()}


def render(reports):
    lines=[]
    for arm in ('B2048','ON16k','B4096'):
        report=reports[arm];lines.append(arm+' ('+report['role']+', '+report['mode']+')')
        groups={**report['groups'],**{'facing_'+k:v for k,v in report['direction_by_question_text'].items()}}
        for name,r in groups.items():
            score='undefined' if r['score'] is None else f"{100*r['score']:.2f}%"
            ci=r['percentile_95'];interval='undefined' if ci is None else f"[{100*ci[0]:.2f}, {100*ci[1]:.2f}]"
            lines.append(f"{name}: {score}; 95% CI {interval}; n={r['items']}; errors={r['error_count']}; source capped={r['source_capped']}; continuation capped={r['continuation_capped']}; unparsed={r['unparsed']}")
        r=report['five_category_mean'];score='undefined' if r['score'] is None else f"{100*r['score']:.2f}%"
        ci=r['percentile_95'];interval='undefined' if ci is None else f"[{100*ci[0]:.2f}, {100*ci[1]:.2f}]"
        lines.append(f"Five-category mean: {score}; 95% CI {interval}")
    lines.extend(f"{k} ({v}): not read here: native reader required" for k,v in EXCLUDED.items())
    return '\n'.join(lines)+'\n'


def main():
    p=argparse.ArgumentParser();p.add_argument('--dest',required=True);p.add_argument('--cohort',default=str(Path(__file__).resolve().parents[1]/'cohort/COHORT_REVSI5.jsonl'));p.add_argument('--output',required=True);p.add_argument('--parent-answers')
    a=p.parse_args();score_run(a.dest,a.cohort,a.output,parent_answers=a.parent_answers);print((Path(a.output)/'SUMMARY.txt').read_text(),end='')
if __name__=='__main__':main()
