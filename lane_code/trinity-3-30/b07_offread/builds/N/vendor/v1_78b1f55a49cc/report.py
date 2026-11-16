"""Official-score summaries, clustered intervals and refusal costs."""
from collections import Counter
from pathlib import Path
import numpy as np
from adapter import *
from scorer import TYPES,GROUPS,collapse

DISCLOSURE="only move, turn and pose are served, by frozen G3T run on this read's frames with step-544's own scale and gravity; every other call is refused"

def estimate(values,types):
    if not values:return None
    scores={t:np.mean([r['score'] for r in values if r['question_type']==t]) for t in types if any(r['question_type']==t for r in values)}
    if len(scores)!=len(types):return None
    if set(types)==set(TYPES):return collapse(scores)['primary']
    return float(np.mean(list(scores.values())))

def interval(values,types,cluster='scene',repeats=2000):
    if not values or estimate(values,types) is None:return None
    groups={}
    for row in values:groups.setdefault(row[cluster],[]).append(row)
    names=sorted(groups);sums=np.zeros((len(names),len(types)));counts=np.zeros_like(sums)
    for i,key in enumerate(names):
        for row in groups[key]:
            j=types.index(row['question_type']);sums[i,j]+=row['score'];counts[i,j]+=1
    rng=np.random.default_rng(544);weights=rng.multinomial(len(names),[1/len(names)]*len(names),size=repeats)
    den=weights@counts;num=weights@sums;valid=np.all(den>0,axis=1)
    means=num[valid]/den[valid]
    if not len(means):return None
    if set(types)==set(TYPES):
        boot=np.mean([np.mean(means[:,[types.index(t) for t in ts]],axis=1) for ts in GROUPS.values()],axis=0)
    else:boot=means.mean(axis=1)
    lo,hi=np.quantile(boot,[.025,.975])
    return dict(confidence=.95,low=float(lo),high=float(hi),clusters=len(names),replicates=repeats,valid_replicates=int(valid.sum()),seed=544)

def metrics(values,types):
    calls=[c for r in values for c in r['calls']]
    refused=[r for r in values if any(c['refused'] for c in r['calls'])]
    expected=50*len(types);complete=all(sum(r['question_type']==t for r in values)==50 for t in types)
    return dict(items=len(values),expected=expected,complete=complete,
        status='complete' if complete else f'incomplete ({len(values)}/{expected})',items_with_any_call=sum(bool(r['calls']) for r in values),
        camera_calls_served=sum(c['name'] in ('move','turn','pose') and c['kind']!='error' for c in calls),
        calls_refused=dict(Counter(c['name'] for c in calls if c['refused'])),
        camera_call_errors=sum(c['name'] in ('move','turn','pose') and c['kind']=='error' and not c['refused'] for c in calls),
        score=estimate(values,types) if complete else None,scene_interval=interval(values,types) if complete else None,room_interval=interval(values,types,'room') if complete else None,
        forced_closes=sum(r['forced_close'] for r in values),no_final_answers=sum(r['no_final_answer'] for r in values),
        gravity_refusals=sum(bool(r['geometry_refusal']) for r in values),geometry_auto_zero=sum(r.get('geometry_auto_zero',False) for r in values),seconds=sum(r['seconds'] for r in values),
        refusal_cost=dict(items=len(refused),answers=dict(Counter(r['answer'] or '<none>' for r in refused)),
                          score=float(np.mean([r['score'] for r in refused])) if refused and complete else None,
                          per_item=[dict(key=r['key'],answer=r['answer'],score=r['score']) for r in refused]))

def build(merged_path,output,comparators=(),proof_path=None,release_path=None):
    bundle=load(merged_path);bound=validate_bound(checked(bundle['bound']));truth=load(checked(bound['inputs']['SCORES.json']))
    proof_pin=pin(proof_path) if proof_path else bundle.get('proof')
    proof=load(checked(proof_pin)) if proof_pin else None
    if not bundle['synthetic'] and (not proof or proof.get('synthetic') is not False or proof.get('items')!=10):
        raise ValueError('non-synthetic report requires the in-job ten-item proof')
    if not bundle['synthetic'] and (bundle.get('proof')!=proof_pin or proof.get('read_binding')!=bundle['request_binding']):
        raise ValueError('proof does not bind this read')
    release=load(release_path) if release_path else dict(status='not run',compared_frames=0,identical_frames=0)
    index_check=load(checked(bound['inputs']['INDEX_CHECK.json'])) if 'INDEX_CHECK.json' in bound['inputs'] else dict(status='not run')
    index_note='Own selected-frame index comparison: '+index_check['status']
    if index_check['status']=='complete':index_note+=f"; {index_check['matching']}/{index_check['scenes']} scenes match; differences are recorded in REPORT.json."
    else:index_note+='; the separately staged reference list is required.'
    frame_note="Frames are the comparator reads' prepared 32-frame sets, decoded with av 15.1 from VSI-Bench copies of the ScanNet videos (SHA differs from the VSTI release); item pairing with f17 and P1 m200 holds. Release-video pixel check: "+release['status']+f"; {release['identical_frames']}/{release['compared_frames']} identical frames."
    proof_state='not run (synthetic)' if not proof else 'failed' if proof.get('failed') else 'passed' if proof.get('proven') else 'diverged'
    proof_note=('In-job dev-S1 proof failed: '+proof['error']) if proof and proof.get('failed') else (('In-job dev-S1 proof: '+str(proof['identical_count'])+'/10 identical; equal token-sequence share '+str(proof['equal_token_share'])+'; first divergences '+json.dumps([{r['key']:r['first_divergence']} for r in proof['records'] if r['first_divergence']],sort_keys=True)+'.') if proof else 'In-job dev-S1 proof: not run (synthetic rehearsal).')
    enriched=[dict(r,scene=truth[r['key']]['scene'],room=truth[r['key']]['room']) for r in bundle['items']]
    native=[r for r in enriched if r['arm']=='native'];script=[r for r in enriched if r['arm']=='scripted']
    per_type={t:metrics([r for r in native if r['question_type']==t],[t]) for t in TYPES}
    subtasks={g:metrics([r for r in native if r['question_type'] in ts],ts) for g,ts in GROUPS.items()}
    primary=metrics(native,list(TYPES))
    if not bundle['complete']:primary.update(score=None,scene_interval=None,room_interval=None)
    compared={}
    for path in comparators:
        label=path.get('label') if isinstance(path,dict) else None
        path=path['path'] if isinstance(path,dict) else path
        other=rows(path);lookup={str(r['example_id']):r for r in other};groups={}
        for t in CAMERA:
            paired=[];baseline=[]
            for r in native:
                if r['question_type']!=t:continue
                ref=lookup[truth[r['key']]['id']]
                if ref['question_type']!=t or ref['scene_name']!=r['scene']:raise ValueError('comparison item identity differs')
                baseline.append(float(ref['score']));paired.append(dict(r,score=r['score']-float(ref['score'])))
            groups[t]=dict(items=len(paired),keys=[r['key'] for r in paired],
                status='complete' if len(paired)==50 else f'incomplete ({len(paired)}/50)',
                other_model_score=float(np.mean(baseline)) if len(paired)==50 else None,
                paired_difference=estimate(paired,[t]) if len(paired)==50 else None,scene_interval=interval(paired,[t]) if len(paired)==50 else None,room_interval=interval(paired,[t],'room') if len(paired)==50 else None)
        compared[label or Path(path).name.split('.')[0]]=dict(label='other models',source=pin(path),types=groups)
    result=dict(schema='read-report-v1',synthetic=bundle['synthetic'],complete=bundle['complete'],
        source=pin(merged_path),proof=proof,proof_source=proof_pin,proof_summary=proof_note,frames=frame_note,index_check=index_check,release_check=release,disclosure=DISCLOSURE,missing=bundle['missing'],per_type=per_type,
        subtasks=subtasks,primary=primary,other_models=compared,
        scripted={t:metrics([r for r in script if r['question_type']==t],[t]) for t in CAMERA},
        timing=dict(shards=[dict(shard=c['shard'],seconds=c['seconds'],geometry_seconds=c.get('geometry_seconds')) for c in bundle['completions']]),
        gravity=[c['gravity'] for c in bundle['completions']],
        not_checked=['GPU decoding and real tower validity' ] if bundle['synthetic'] else [])
    dest=Path(output);dump(dest/'REPORT.json',result)
    source=str(dest/'REPORT.json')
    heading='Synthetic rehearsal' if bundle['synthetic'] else 'Read result'
    score_text='unavailable' if primary['score'] is None else f"{100*primary['score']:.2f}%"
    refused_names=', '.join(f'{name} ({sum(m["calls_refused"].values())})' for name,m in subtasks.items() if m['calls_refused']) or 'none'
    zeros=', '.join(f'{name} ({m["geometry_auto_zero"]})' for name,m in subtasks.items() if m['geometry_auto_zero']) or 'none'
    text=[heading+'\n',proof_note+'\n',frame_note+'\n',index_note+'\n',f'Primary: {score_text}; proof {proof_state}; subtasks with refused calls: {refused_names}; geometry auto-zero: {zeros}; missing items are never imputed. Source: `{source}`.\n',DISCLOSURE+'.\n',
          "Refusals use the runtime's recoverable error format (trace 3.13).\n",
          'The scale rule remains unaudited; the depth-head lineage before step 544 was not established.\n',
          'This rehearsal uses synthetic checkpoint depth/gravity and token generation. The statement above specifies the production serving policy.\n' if bundle['synthetic'] else '',
          f"Completed items: {len(native)}; missing items: {len(bundle['missing'])}. Source: `{source}`.\n",
          '| Type or subtask | Items | Any call | Served | Refused | Score | 95% scene interval |',
          '|---|---:|---:|---:|---:|---:|---|']
    for name,m in list(per_type.items())+list(subtasks.items()):
        val=m['status'] if m['score'] is None else f"{100*m['score']:.2f}%"
        ci=m['scene_interval'];span='unavailable' if ci is None else f"[{100*ci['low']:.2f}, {100*ci['high']:.2f}]"
        text.append(f"| {name} | {m['items']} | {m['items_with_any_call']} | {m['camera_calls_served']} | {sum(m['calls_refused'].values())} | {val} | {span} |")
    text.extend(['',f'All table values, room sensitivity intervals, refusal answer distributions, scripted scores, paired differences against other models, gravity refusals and timing: `{source}`.',
                 '', '| Type | Forced closes | No final answer | Gravity refusals | Refusal items | Refusal-item score |',
                 '|---|---:|---:|---:|---:|---:|'])
    for name,m in per_type.items():
        cost=m['refusal_cost'];val='unavailable' if cost['score'] is None else f"{100*cost['score']:.2f}%"
        text.append(f"| {name} | {m['forced_closes']} | {m['no_final_answers']} | {m['gravity_refusals']} | {cost['items']} | {val} |")
    text.extend(['',f'Refusal-answer distributions and refused-call names follow. Source: `{source}`.',''])
    for name,m in per_type.items():
        if m['refusal_cost']['items']:
            text.append(f"- {name}: calls {json.dumps(m['calls_refused'],sort_keys=True)}; final answers {json.dumps(m['refusal_cost']['answers'],sort_keys=True)}.")
    text.extend(['', '| Camera type | Native | Scripted camera program |', '|---|---:|---:|'])
    def percent(value):return 'unavailable' if value is None else f'{100*value:.2f}%'
    for name,m in result['scripted'].items():
        text.append(f"| {name} | {percent(per_type[name]['score'])} | {percent(m['score'])} |")
    text.extend(['', '| Other model | Camera type | Same-item count | Other-model score | Native minus other model | 95% scene interval |',
                 '|---|---|---:|---:|---:|---|'])
    for model,value in compared.items():
        for name,m in value['types'].items():
            ci=m['scene_interval'];span='unavailable' if ci is None else f"[{100*ci['low']:.2f}, {100*ci['high']:.2f}] pp"
            difference='unavailable' if m['paired_difference'] is None else f"{100*m['paired_difference']:.2f} pp"
            text.append(f"| {model} (other models) | {name} | {m['items']} | {percent(m['other_model_score'])} | {difference} | {span} |")
    text.extend(['',f'Camera comparisons use exactly the recorded item keys; intervals and differences are in percentage points. All values: `{source}`.',
                 '',f"Timing by shard: {json.dumps(result['timing']['shards'],sort_keys=True)}. Source: `{source}`.",
                 '', 'The intervals resample whole scenes; room sensitivity resamples scene prefixes. Intervals describe the observed items, and missing types have no score.',
                 '', 'Unchecked: '+('; '.join(result['not_checked']) or 'No additional checks claimed beyond the run receipts.')])
    (dest/'REPORT.md').write_text('\n'.join(text)+'\n');return result
