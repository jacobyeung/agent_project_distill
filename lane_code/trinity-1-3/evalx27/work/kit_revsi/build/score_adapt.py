from pathlib import Path
K=Path(__file__).resolve().parents[1];p=K/'reader/official_score.py';s=p.read_text();a=s.index('from evalpath.official import VSI_PRIMARY_GROUPS');b=s.index('\n\ndef read_rows',a)
s=s[:a]+'''EXCLUDED={'object_abs_distance':283,'room_size_estimation':37}
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
'''+s[b:]
s=s.replace('six tasks','five categories').replace('seed=544,allow_partial=False):','seed=544,allow_partial=False,return_draws=False):')
s=s.replace('len(expected)!=4008','len(expected)!=679').replace('})!=288','})!=261').replace('Require all 4008 items and 288 scenes','Require all 679 items and 261 scenes')
s=s.replace("slots=[type_index[t] for t in ts]", "slots=[type_index[t] for t in ts if counts[:,type_index[t]].sum()>0]")
s=s.replace('val=float(np.mean(scores[slots]));draw=np.mean(sub[:,slots],axis=1);replicas.append(draw)', "val=float(np.mean(scores[slots])) if slots else float('nan');draw=np.mean(sub[:,slots],axis=1) if slots else np.full(repetitions,np.nan);replicas.append(draw)")
s=s.replace("unparsed=sum(r['unparsed'] for r in selected),**ci(draw))", "unparsed=sum(r['unparsed'] for r in selected),error_count=sum(r['error'] is not None for r in selected),**ci(draw))")
s=s.replace("/6\n    return dict", "/5\n    result=dict")
s=s.replace('six_task_mean','five_category_mean').replace("status='not read'","status='not read here: native reader required'")
a=s.index('\n\ndef score_run');s=s[:a]+'''
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
'''+s[a:]
s=s.replace('def score_run(dest,cohort,output,allow_partial=False):','def score_run(dest,cohort,output,allow_partial=False,parent_answers=None):')
s=s.replace("    return {a:dict(items=r['items']", "    if parent_answers:\n        comparison=paired(tasks,arms['B2048'],read_rows(parent_answers),allow_partial=allow_partial)\n        (out/'PAIRED_B2048.json').write_text(json.dumps(comparison,indent=2,allow_nan=False)+'\\n')\n    return {a:dict(items=r['items']")
# Retain inherited self-check as a separately named VSI compatibility helper.
a=s.index('def main():');s=s[:a]+'''def main():
    p=argparse.ArgumentParser();p.add_argument('--dest',required=True);p.add_argument('--cohort',default=str(Path(__file__).resolve().parents[1]/'cohort/COHORT_REVSI5.jsonl'));p.add_argument('--output',required=True);p.add_argument('--parent-answers')
    a=p.parse_args();print(json.dumps(score_run(a.dest,a.cohort,a.output,parent_answers=a.parent_answers)))
if __name__=='__main__':main()
''';p.write_text(s)
p=K/'proof/selection.py';s=p.read_text();a=s.index('TYPES=');b=s.index('\n\ndef verify_results',a);s=s[:a]+'''def select(rows):
    from official_score import GROUPS,facing
    chosen=[]
    for category,kinds in GROUPS.items():
        candidates=sorted((r for r in rows if r['question_type'] in kinds),key=lambda r:str(r['id']))
        if category=='object_rel_direction':
            chosen.extend(next(r for r in candidates if facing(r['question'])==label) for label in ('toward','away'))
        else:chosen.extend(candidates[:2])
    if len(chosen)!=10:raise ValueError('Require two items per category')
    return sorted(chosen,key=lambda r:str(r['id']))
'''+s[b:];p.write_text(s)
