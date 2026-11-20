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
from gpkg.source_pins import checked


def function(path,name,namespace):
    tree=ast.parse(checked(path))
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


def load_capture(path,receipt,refs,with_restricted=False,mode='points'):
    records=Records(path,receipt); primary={}; repeat={}; restricted={}
    for row in records:
        key=row['item_id']
        if key not in refs:raise ValueError('capture item outside manifest')
        ref=refs[key]
        if row['capture']!=ref['capture'] or row['source_indices']!=ref['source_indices']:
            raise ValueError('capture identity differs')
        if not row.get('excluded') and [(c['call'],c.get('served')) for c in row['calls']]!=[(c['call'],c.get('served')) for c in ref['calls']]:
            raise ValueError('recorded call sequence or serving contract differs')
        if row['pass_index'] not in (0,1,2):raise ValueError('unknown pass')
        if mode=='dense64':
            if row['pass_index'] not in (0,1):raise ValueError('unknown dense pass')
            expected_arm={0:'dense64',1:'dense64_noise'}[row['pass_index']]
            n=ref['mapping']['dense_count'];ground=row.get('ground_source_indices',[]);slots=row.get('anchor_slots',[])
            if (row.get('ground_frame_count')!=n or len(ground)!=n or len(slots)!=32
                or any(type(s) is not int or not 0<=s<n for s in slots)
                or any(a>=b for a,b in zip(ground,ground[1:]))
                or [ground[s] for s in slots]!=ref['source_indices']):raise ValueError('dense frame binding differs')
            if row.get('arm')!=expected_arm:raise ValueError('dense arm missing or different')
            if row.get('primary_dense64')!=(n==64) or row.get('unchanged32')!=(n==32):raise ValueError('dense population flag differs')
            for call in row['calls']:
                f=re.search(r': frames ([0-9,]+) \(best ([0-9]+)\)',call.get('response') or '')
                if f and any(not 1<=int(x)<=n for x in f[1].split(',')+[f[2]]):raise ValueError('printed dense frame outside binding')
        else:expected_arm={0:'points',1:'text_noise',2:'restricted_selector'}[row['pass_index']]
        if row.get('arm') is not None and row['arm']!=expected_arm:raise ValueError('arm/pass mismatch')
        target={0:primary,1:repeat,2:restricted}[row['pass_index']]
        if key in target:raise ValueError('duplicate item/pass')
        # Release proposal RLEs after each item. A 1.9 GB compressed capture
        # must not become a retained Python object graph for the full read.
        sizes=[]
        for obj in row.get('objects',[]):
            areas=[]
            for mask in obj['selected_masks'].values():
                area=float(unrle(mask).mean())
                if area:areas.append(area)
            sizes.append(dict(name=obj['name'],fraction=float(np.mean(areas)) if areas else None))
        target[key]={k:row[k] for k in ('item_id','capture','source_indices','calls','pass_index')}
        target[key].update(excluded=row.get('excluded',False),object_mask_sizes=sizes,
                           binding=row.get('binding'),arm=row.get('arm'))
        if mode=='dense64':
            target[key].update({k:row[k] for k in ('ground_frame_count','ground_source_indices','anchor_slots','primary_dense64','unchanged32')})
            target[key]['anchor_geometry_deltas']=(row.get('geometry') or {}).get('anchor_geometry_deltas')
            target[key]['anchor_geometry_unchanged']=(row.get('geometry') or {}).get('anchor_geometry_unchanged')
    if with_restricted:return primary,repeat,restricted,records.report
    return primary,repeat,records.report


def sparse_calls(calls):
    """The registered 93 items printed at least one explicit 1–2-frame list."""
    sparse=[];null=[]
    for call in calls:
        m=re.fullmatch(r'<ground obj="([^"]+)" mode="box">',call['call'])
        if not m or not call.get('served'):continue
        f=re.search(r': frames ([0-9,]+) \(best',call.get('response') or '')
        if f and len(set(f[1].split(',')))<3:sparse.append(m[1])
        elif not f:null.append(m[1])
    return sorted(set(sparse)),sorted(set(null))


def sparse_visibility(ref,name,gt):
    scene=gt.get(ref['capture'])
    if scene is None:return dict(group='no GT',reason='capture unavailable')
    if scene['source_indices']!=ref['source_indices']:raise ValueError('GT anchor binding differs')
    if not all(scene['valid']):return dict(group='no GT',reason='incomplete GT anchors')
    targets=scene['targets'];key=ref['item_id']+':'+name
    target=targets.get(key)
    if target is None:
        prefix=ref['item_id']+':'
        matches=[v for k,v in targets.items() if k.startswith(prefix) and name_key(k[len(prefix):])==name_key(name)]
        target=matches[0] if len(matches)==1 else None
    if not target or target.get('binding',{}).get('status')!='bound' or 'visible_pixels' not in target:
        return dict(group='no GT',reason='missing or ambiguous label binding')
    pixels=target['visible_pixels']
    if len(pixels)!=32:raise ValueError('GT visibility needs 32 anchors')
    count=sum(p>0 for p in pixels)
    return dict(group='0' if count==0 else '1-2' if count<3 else '>=3',visible_anchor_frames=count,
                instance_id=target['instance_id'],orientation=scene['orientation']['status'])


def run_receipt(path,raw_report,mode):
    """A killed worker's fallback is diagnostic, never authentication authority."""
    if not path:return None
    run=json.loads(Path(path).read_text())
    missing=[k for k in ('capture_sha256','mode') if k not in run]
    if 'capture_sha256' in run and run['capture_sha256']!=raw_report['raw_sha256']:
        raise ValueError('run receipt SHA256 differs')
    if 'mode' in run and run['mode']!=mode:raise ValueError('run receipt mode differs')
    if missing:
        if not (run.get('trusted') is False and run.get('failure')=='worker did not finish its receipt'):
            raise ValueError('unrecognized incomplete run receipt')
        return dict(run,receipt_status='incomplete',missing_fields=missing,
                    exclusions_known=False,raw_bytes_authenticated=raw_report['sha256_verified'])
    return dict(run,receipt_status='complete',exclusions_known=True)


def fraction_band(size):
    if size is None:return 'unknown'
    return '>=5%' if size>=.05 else '1-5%' if size>=.01 else '0.2-1%' if size>=.002 else '<0.2%'


def size_band(row):
    # A pair takes the smaller object's mean visible selected-mask area.
    # Null/absent frames do not dilute the visible-frame size estimate.
    sizes=[v['fraction'] for v in row.get('object_mask_sizes',[]) if v['fraction'] is not None]
    for obj in row.get('objects',[]):
        areas=[float(unrle(m).mean()) for m in obj['selected_masks'].values() if unrle(m).any()]
        if areas:sizes.append(float(np.mean(areas)))
    if len(sizes)!=2:return 'unknown',sizes
    size=min(sizes)
    return fraction_band(size),sizes


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
    if any('sparse93' in r for r in rows):
        groups['sparse93']=[r for r in rows if r['sparse93']]
        groups['null_without_printed_sparse']=[r for r in rows if r['null_ground_names'] and not r['sparse93']]
        for value in ('0','1-2','>=3','no GT'):
            groups['sparse_visibility='+value]=[r for r in rows if value in r['sparse_visibility_groups']]
        groups['sparse_lt3']=[r for r in rows if r['sparse_lt3']]
        for value in ('0','1-2','>=3','no GT'):
            groups['sparse_lt3_visibility='+value]=[r for r in rows if value in r['sparse_lt3_visibility_groups']]
    if any('primary_dense64' in r for r in rows):
        groups['dense64_primary']=[r for r in rows if r['primary_dense64']]
        groups['unchanged32']=[r for r in rows if not r['primary_dense64']]
        for group,subset in list(groups.items()):
            if group.startswith('sparse'):groups['dense64_primary/'+group]=[r for r in subset if r['primary_dense64']]
    output={}
    for group,subset in groups.items():
        metrics=['baseline','points','point_minus_baseline']
        if any('restricted_selector' in r for r in rows):metrics+=['restricted_selector','restricted_minus_baseline']
        if any('T1' in r for r in rows):metrics+=['T1','T1_minus_baseline','point_minus_T1']
        if any('dense64' in r for r in rows):
            metrics=['baseline','dense64','dense64_minus_baseline']
            if any('T1' in r for r in rows):metrics+=['T1','T1_minus_baseline','dense64_minus_T1']
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


def score(manifest,point_capture,point_receipt,t1_capture=None,t1_receipt=None,truth_file=None,point_run_receipt=None,gt_file=None,mode='points'):
    if mode not in ('points','dense64'):raise ValueError('unknown scoring arm')
    refs=json.loads(Path(manifest).read_text())['items']
    by_id={r['item_id']:r for r in refs}
    if len(refs)!=150 or len(by_id)!=150:raise ValueError('expected 150 unique items')
    rooms={r['task']['room'] for r in refs}
    if len(rooms)!=46:raise ValueError('expected 46 physical rooms')
    supplied=json.loads(Path(truth_file).read_text()) if truth_file else None
    run=None
    points,repeats,restricted,pr=load_capture(point_capture,point_receipt,by_id,with_restricted=True,mode=mode)
    gt_path=Path(gt_file) if gt_file else ROOT/'out2/GT.json'
    gt=json.loads(gt_path.read_text())
    sparse_total=sum(bool(sparse_calls(r['calls'])[0]) for r in refs)
    if sparse_total!=93:raise ValueError('registered printed-sparse population differs from 93')
    t1,tr=({},None)
    if bool(t1_capture)!=bool(t1_receipt):raise ValueError('T1 requires capture and raw-byte receipt')
    if t1_capture:t1,_,tr=load_capture(t1_capture,t1_receipt,by_id)
    excluded={r['capture'] for r in [*points.values(),*restricted.values()] if r.get('excluded')}
    if point_run_receipt:
        run=run_receipt(point_run_receipt,pr,mode)
        excluded.update(run.get('excluded_captures',[]))
    if not excluded<={r['capture'] for r in refs}:raise ValueError('unknown excluded capture')
    rows=[];object_rows=[];noise=[];unmapped=[]
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
        control=gap_score(restricted.get(key,{}).get('calls',[]),q,truth)
        sparse,null=sparse_calls(ref['calls'])
        visibility={name:sparse_visibility(ref,name,gt) for name in sparse}
        lt3_visibility={name:sparse_visibility(ref,name,gt) for name in sorted(set(sparse+null))}
        band,sizes=size_band(points.get(key,{}))
        frames=dict(baseline=object_frames(ref['calls'],q),points=object_frames(pc,q))
        frames['restricted_selector']=object_frames(restricted.get(key,{}).get('calls',[]),q)
        row=dict(item_id=key,room=task['room'],capture=ref['capture'],truth=dict(scored=truth),
                 baseline=base['score'],points=point['score'],point_minus_baseline=point['score']-base['score'],
                 baseline_lt3=any(n<3 for n in frames['baseline'].values()),size_band=band,object_sizes=sizes,
                 frames_grounded=frames,point_record_present=key in points,gap_available=dict(baseline=base['available'],points=point['available']))
        row.update(restricted_selector=control['score'],restricted_minus_baseline=control['score']-base['score'],
                   restricted_record_present=key in restricted,sparse93=bool(sparse),sparse_names=sparse,
                   null_ground_names=null,sparse_visibility=visibility,
                   sparse_visibility_groups=sorted({v['group'] for v in visibility.values()}))
        row.update(sparse_lt3=bool(sparse or null),sparse_lt3_visibility=lt3_visibility,
                   sparse_lt3_visibility_groups=sorted({v['group'] for v in lt3_visibility.values()}))
        if mode=='dense64':
            row.update(primary_dense64=ref['mapping']['dense_count']==64,
                       unchanged32=ref['mapping']['dense_count']==32,
                       ground_frame_count=ref['mapping']['dense_count'],
                       anchor_geometry_deltas=points.get(key,{}).get('anchor_geometry_deltas'),
                       anchor_geometry_unchanged=points.get(key,{}).get('anchor_geometry_unchanged'))
        row['gap_available']['restricted_selector']=control['available']
        if t1_capture:
            tc=t1.get(key,{}).get('calls',[]);ts=gap_score(tc,q,truth)
            row.update(T1=ts['score'],T1_minus_baseline=ts['score']-base['score'],point_minus_T1=point['score']-ts['score'],t1_record_present=key in t1)
            frames['T1']=object_frames(tc,q);row['gap_available']['T1']=ts['available']
        rows.append(row)
        for name in names(q):
            candidates=[v for v in points.get(key,{}).get('object_mask_sizes',[]) if name_key(v['name'])==name_key(name)]
            fraction=candidates[0]['fraction'] if len(candidates)==1 else None
            occurrence={k:row[k] for k in ('item_id','room','baseline','points','point_minus_baseline','restricted_selector','restricted_minus_baseline')}
            if t1_capture:occurrence.update({k:row[k] for k in ('T1','T1_minus_baseline','point_minus_T1')})
            occurrence.update(name=name,mask_fraction=fraction,size_band=fraction_band(fraction),
                              baseline_lt3=frames['baseline'][name]<3,
                              frames_grounded={arm:counts[name] for arm,counts in frames.items()})
            if mode=='dense64':occurrence['primary_dense64']=row['primary_dense64']
            object_rows.append(occurrence)
        unmapped.extend(dict(item_id=key,**call) for call in (points.get(key,{}).get('binding') or {}).get('unmapped_calls',[]))
        if key in repeats:
            rc=repeats[key]['calls'];rs=gap_score(rc,q,truth)
            from gpkg.runtime.p import compare
            same,gaps=compare(pc if mode=='dense64' else ref['calls'],rc)
            noise.append(dict(item_id=key,text_score=rs['score'],baseline_score=base['score'],
                              main_score=point['score'],reference='main arm' if mode=='dense64' else 'baseline',
                              difference=rs['score']-(point['score'] if mode=='dense64' else base['score']),discrete_match=same,
                              gap_differences=[{k:float(v) if hasattr(v,'as_tuple') else v for k,v in g.items()} for g in gaps]))
    if mode=='dense64':
        def rename(value):
            if isinstance(value,dict):
                keys={'points':'dense64','point_minus_baseline':'dense64_minus_baseline',
                      'point_minus_T1':'dense64_minus_T1','point_record_present':'dense64_record_present'}
                return {keys.get(k,k):rename(v) for k,v in value.items()
                        if k not in ('restricted_selector','restricted_minus_baseline','restricted_record_present')}
            if isinstance(value,list):return [rename(v) for v in value]
            return value
        rows=rename(rows);object_rows=rename(object_rows)
    result=dict(schema='dense-ground-score-v1' if mode=='dense64' else 'point-ceiling-score-v1',score='supplemental printed-gap MRA percent',
                truth_authority='supplied truth.scored' if supplied else 'pinned primary released_answer == ground_truth',
                total_manifest_items=150,denominator=len(rows),excluded_captures=sorted(excluded),
                arm_records=dict(points=len(points),restricted_selector=len(restricted),text_noise=len(repeats),T1=len(t1) if t1_capture else None),
                complete_paired_population=(len(points)==150 and (mode=='dense64' or len(restricted)==150) and not excluded
                                           and not (run or {}).get('failure')),
                run_failure=(run or {}).get('failure'),
                run_receipt=run,
                sparse_lt3_manifest_items=sum(bool(any(sparse_calls(r['calls']))) for r in refs),
                sparse_lt3_denominator=sum(r['sparse_lt3'] for r in rows),
                sparse_lt3_definition='served ground call printed fewer than three frames, including zero-frame failures',
                sparse_manifest_items=sparse_total,sparse_denominator=sum(r['sparse93'] for r in rows),
                sparse_definition='at least one served ground call printed an explicit 1-2-frame list; null statuses reported separately',
                visibility_definition='GT v2 pixels > 0 on valid anchors of each sparse called object; each item appears once per applicable bin; bins may overlap',
                gt_file=str(gt_path),gt_sha256=__import__('hashlib').sha256(gt_path.read_bytes()).hexdigest(),
                excluded_items=150-len(rows),capture_read=dict(points=pr,T1=tr),
                statistics=bootstrap(rows,rooms),rows=rows,text_noise=noise,
                object_statistics=bootstrap(object_rows,rooms),object_rows=object_rows,unmapped_calls=unmapped,
                object_group_definition='one occurrence per question operand; paired item score attached to each occurrence; size from point-arm masks',
                size_definition='smaller of two object mean nonempty selected-mask fractions; unknown unless both available',
                missing_gap_score=0,missing_capture_records_score=0)
    if mode=='dense64':
        geometry_changed=[r['item_id'] for r in rows if r['primary_dense64'] and r['anchor_geometry_unchanged'] is False]
        geometry_unknown=[r['item_id'] for r in rows if r['primary_dense64'] and r['anchor_geometry_unchanged'] is None]
        result.update(arm_records=dict(dense64=len(points),dense64_noise=len(repeats),T1=len(t1) if t1_capture else None),
                      capture_read=dict(dense64=pr,T1=tr),arm_noise=result.pop('text_noise'),
                      primary_population='104 items on 31 captures with 64 bound native frames',
                      control_population='46 items on 29 captures with 32 bound anchors',
                      primary_complete=all(r['dense64_record_present'] for r in rows if r['primary_dense64']) and not excluded and not (run or {}).get('failure'),
                      response_strings_differ_by_design=True,parity_gate_applies=False,
                      geometry_changed_items=geometry_changed,geometry_unmeasured_items=geometry_unknown,
                      geometry_intervention_observed=bool(geometry_changed),
                      object_group_definition='one occurrence per question operand; paired item score attached to each occurrence; size from dense-arm masks')
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument('--manifest',default=ROOT/'kit2/kit/rerun2/items544.json')
    p.add_argument('--out',required=True)
    for k in ('point-capture','point-receipt','dense-capture','dense-receipt','dense-run-receipt'):p.add_argument('--'+k)
    for k in ('t1-capture','t1-receipt','truth','point-run-receipt','gt'):p.add_argument('--'+k)
    a=p.parse_args()
    if bool(a.dense_capture)==bool(a.point_capture):p.error('supply exactly one point or dense capture')
    if a.dense_capture:
        if not a.dense_receipt or a.point_receipt or a.point_run_receipt:p.error('dense capture requires dense receipts')
        result=score(a.manifest,a.dense_capture,a.dense_receipt,a.t1_capture,a.t1_receipt,a.truth,a.dense_run_receipt,a.gt,mode='dense64')
    else:
        if not a.point_receipt or a.dense_receipt or a.dense_run_receipt:p.error('point capture requires point receipts')
        result=score(a.manifest,a.point_capture,a.point_receipt,a.t1_capture,a.t1_receipt,a.truth,a.point_run_receipt,a.gt)
    Path(a.out).write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ('denominator','excluded_items','capture_read')}))


if __name__=='__main__':main()
