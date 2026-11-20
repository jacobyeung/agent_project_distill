"""Paired supplemental gap scores, with the reader's scoring and room bootstrap."""
import argparse
import ast
import json
import math
from pathlib import Path
import random
import re
import sys
from typing import Optional
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from gpkg.capture_io import Records
from gpkg.runtime.c import unrle


def function(path,name,namespace):
    tree=ast.parse(path.read_text())
    node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
    exec(compile(ast.Module([node],type_ignores=[]),str(path),'exec'),namespace)
    return namespace[name]


OFFICIAL=ROOT/'work/payload/tree/evalpath/official.py'
SCORERS=ROOT/'work/payload/h1eval/scorers.py'
official_mra=function(OFFICIAL,'official_mra',dict(math=math,Optional=Optional))
unit_factor=function(SCORERS,'unit_factor',dict(re=re))
names=function(ROOT/'kit2/kit/analyze.py','names',dict(re=re))
name_key=function(ROOT/'work/payload/b/e2e_reader/stage1.py','name_key',{})


def gap_score(calls,question,truth):
    values=[]
    for c in calls:
        if c['call'].startswith('<gap ') and c.get('served'):
            m=re.fullmatch(r'distance ([0-9]+(?:\.[0-9]+)?) m',c.get('response') or '')
            if m:values.append(float(m[1]))
    pred=values[-1]*unit_factor(question) if values else None
    return dict(score=100*official_mra(pred,float(truth)),prediction=pred,available=bool(values))


def object_frames(calls,question):
    result={n:0 for n in names(question)}
    for c in calls:
        m=re.fullmatch(r'<ground obj="([^"]+)" mode="box">',c['call'])
        if not m or not c.get('served'):continue
        exact=m[1] if m[1] in result else next((n for n in result if name_key(n)==name_key(m[1])),None)
        if exact is None:continue
        f=re.search(r': frames ([0-9,]+) \(best',c.get('response') or '')
        result[exact]=len(set(f[1].split(','))) if f else 0
    return result


def load_capture(path,receipt,refs):
    records=Records(path,receipt); primary={}; repeat={}
    for row in records:
        key=row['item_id']
        if key not in refs:raise ValueError('capture item outside manifest')
        ref=refs[key]
        if row['capture']!=ref['capture'] or row['source_indices']!=ref['source_indices']:
            raise ValueError('capture identity differs')
        if row['pass_index'] not in (0,1):raise ValueError('unknown pass')
        target=primary if row['pass_index']==0 else repeat
        if key in target:raise ValueError('duplicate item/pass')
        target[key]=row
    return primary,repeat,records.report


def size_band(row):
    # A pair takes the smaller object's mean visible selected-mask area.
    # Null/absent frames do not dilute the visible-frame size estimate.
    sizes=[]
    for obj in row.get('objects',[]):
        areas=[float(unrle(m).mean()) for m in obj['selected_masks'].values() if unrle(m).any()]
        if areas:sizes.append(float(np.mean(areas)))
    if len(sizes)!=2:return 'unknown',sizes
    size=min(sizes)
    return ('>=5%' if size>=.05 else '1-5%' if size>=.01 else '0.2-1%' if size>=.002 else '<0.2%'),sizes


def bootstrap(rows,rooms,draws=10000,seed=20261120):
    """Every contrast/group shares draws of the original physical-room population."""
    rooms=sorted(rooms); lookup={r:i for i,r in enumerate(rooms)}
    rng=random.Random(seed)
    multiplicity=np.zeros((draws,len(rooms)),dtype=np.int16)
    for d in range(draws):
        for _ in rooms:multiplicity[d,lookup[rng.choice(rooms)]]+=1
    groups={'all':rows}
    for field in ('size_band','baseline_lt3'):
        for value in sorted({str(r[field]) for r in rows}):
            groups[field+'='+value]=[r for r in rows if str(r[field])==value]
    output={}
    for group,subset in groups.items():
        metrics=['baseline','points','point_minus_baseline']
        if any('T1' in r for r in subset):metrics+=['T1','point_minus_T1']
        n=np.zeros(len(rooms));sums={k:np.zeros(len(rooms)) for k in metrics}
        for row in subset:
            i=lookup[row['room']];n[i]+=1
            for k in metrics:sums[k][i]+=row[k]
        counts=multiplicity@n;defined=counts>0
        results={}
        for k in metrics:
            sample=(multiplicity@sums[k])[defined]/counts[defined]
            results[k]=dict(mean=float(sums[k].sum()/n.sum()) if n.sum() else None,
                            ci95=np.percentile(sample,[2.5,97.5]).tolist() if len(sample) else None,
                            defined_draws=int(defined.sum()),undefined_draws=int((~defined).sum()))
        output[group]=dict(items=len(subset),rooms=int((n>0).sum()),metrics=results)
    return dict(groups=output,draws=draws,seed=seed,resampled_rooms=len(rooms),item_weighted=True)


def score(manifest,point_capture,point_receipt,t1_capture=None,t1_receipt=None,truth_file=None):
    refs=json.loads(Path(manifest).read_text())['items']
    by_id={r['item_id']:r for r in refs}
    if len(refs)!=150 or len(by_id)!=150:raise ValueError('expected 150 unique items')
    rooms={r['task']['room'] for r in refs}
    if len(rooms)!=46:raise ValueError('expected 46 physical rooms')
    supplied=json.loads(Path(truth_file).read_text()) if truth_file else None
    points,repeats,pr=load_capture(point_capture,point_receipt,by_id)
    t1,tr=({},None)
    if bool(t1_capture)!=bool(t1_receipt):raise ValueError('T1 requires capture and raw-byte receipt')
    if t1_capture:t1,_,tr=load_capture(t1_capture,t1_receipt,by_id)
    excluded={r['capture'] for r in points.values() if r.get('excluded')}
    rows=[];noise=[]
    for ref in refs:
        key=ref['item_id'];task=ref['task'];q=task['question']
        if ref['capture'] in excluded:continue
        if supplied is not None:
            truth=supplied[key]['truth']['scored']
        else:
            # All 150 pinned tasks are primary and carry the released label.
            if task['stratum']!='primary' or task['released_answer']!=task['ground_truth']:
                raise ValueError('explicit truth.scored required for non-primary or disagreeing labels')
            truth=task['released_answer']
        pc=points.get(key,{}).get('calls',[])
        base=gap_score(ref['calls'],q,truth);point=gap_score(pc,q,truth)
        band,sizes=size_band(points.get(key,{}))
        frames=dict(baseline=object_frames(ref['calls'],q),points=object_frames(pc,q))
        row=dict(item_id=key,room=task['room'],capture=ref['capture'],truth=dict(scored=truth),
                 baseline=base['score'],points=point['score'],point_minus_baseline=point['score']-base['score'],
                 baseline_lt3=any(n<3 for n in frames['baseline'].values()),size_band=band,object_sizes=sizes,
                 frames_grounded=frames,point_record_present=key in points,gap_available=dict(baseline=base['available'],points=point['available']))
        if t1_capture:
            tc=t1.get(key,{}).get('calls',[]);ts=gap_score(tc,q,truth)
            row.update(T1=ts['score'],point_minus_T1=point['score']-ts['score'],t1_record_present=key in t1)
            frames['T1']=object_frames(tc,q);row['gap_available']['T1']=ts['available']
        rows.append(row)
        if key in repeats:
            rc=repeats[key]['calls'];rs=gap_score(rc,q,truth)
            from gpkg.runtime.p import compare
            same,gaps=compare(ref['calls'],rc)
            noise.append(dict(item_id=key,text_score=rs['score'],baseline_score=base['score'],
                              difference=rs['score']-base['score'],discrete_match=same,
                              gap_differences=[{k:float(v) if hasattr(v,'as_tuple') else v for k,v in g.items()} for g in gaps]))
    return dict(schema='point-ceiling-score-v1',score='supplemental printed-gap MRA percent',
                truth_authority='supplied truth.scored' if supplied else 'pinned primary released_answer == ground_truth',
                total_manifest_items=150,denominator=len(rows),excluded_captures=sorted(excluded),
                excluded_items=150-len(rows),capture_read=dict(points=pr,T1=tr),
                statistics=bootstrap(rows,rooms),rows=rows,text_noise=noise,
                size_definition='smaller of two object mean nonempty selected-mask fractions; unknown unless both available',
                missing_gap_score=0,missing_capture_records_score=0)


def main():
    p=argparse.ArgumentParser();p.add_argument('--manifest',default=ROOT/'kit2/kit/rerun2/items544.json')
    for k in ('point-capture','point-receipt','out'):p.add_argument('--'+k,required=True)
    for k in ('t1-capture','t1-receipt','truth'):p.add_argument('--'+k)
    a=p.parse_args();result=score(a.manifest,a.point_capture,a.point_receipt,a.t1_capture,a.t1_receipt,a.truth)
    Path(a.out).write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ('denominator','excluded_items','capture_read')}))


if __name__=='__main__':main()
